"""Fail-closed, deterministic *source-only* Arsenal admission reference model.

This is NOT Verse, does not execute native effects, and cannot authorize gameplay.
Inputs marked as trusted MUST be supplied by the authoritative Architect/UEFN
server adapter, never by the client, a display name, a cosmetic, or an input device.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from tools.validate_sovereign_arsenal_universe import load_contract


@dataclass(frozen=True)
class RegisteredTarget:
    """Snapshot obtained from an authoritative registry and collision preflight."""
    target_id: str
    registered_monster: bool = True
    alive: bool = True
    vulnerable: bool = True
    friendly: bool = False
    player: bool = False
    boss: bool = False
    companion: bool = False
    sovereign_army: bool = False
    invulnerable: bool = False
    status_immune: bool = False
    line_of_sight: bool = True
    within_cone: bool = True
    distance_cm: float = 100.0
    health_fraction: float = 0.20


@dataclass(frozen=True)
class AuthoritativeSnapshot:
    """Trusted server observations; a client MUST NOT construct this in production."""
    owner_authorized: bool
    controller_lease_valid: bool
    generation: int
    server_time_ms: int
    server_event_sequence: int
    equipped_class_id: str = ""
    targets: tuple[RegisteredTarget, ...] = ()
    shield: int = 0
    max_shield: int = 100
    destination_authored: bool = False
    destination_clear: bool = False
    destination_line_of_sight: bool = False


@dataclass(frozen=True)
class AdmissionReceipt:
    admitted: bool
    reason: str
    energy_after: int
    damage_upper_bound: int = 0
    shield_restored: int = 0
    event_sequence: int = 0


class ArsenalAdmissionOracle:
    """Reference state machine; no native damage, teleport, slow, or shield calls."""

    MAX_SEQUENCE = 2**63 - 1

    def __init__(self, contract: dict | None = None):
        contract = load_contract() if contract is None else contract
        gate = contract["universe_first_gate"]
        if any(gate[k] is not False for k in
               ("world_content_complete", "prototype_allowed", "native_enablement_allowed")):
            raise ValueError("native/prototype gate must remain closed")
        self.abilities = {ability["id"]: ability for ability in contract["abilities"]}
        self.energy = contract["resource_invariants"]["initial_energy"]
        self.max_damage = contract["resource_invariants"]["max_damage_per_request"]
        self.max_spend = contract["resource_invariants"]["max_spend_per_transaction"]
        self.shield_pool = contract["resource_invariants"]["max_shield_per_generation_shared"]
        self.generation = 1
        self.ready_at_ms: dict[str, int] = {}
        self.last_server_time_ms = 0
        self.last_event_sequence = 0
        self.shield_granted = 0
        self.mark: tuple[str, int, int] | None = None

    def change_generation(self, new_generation: int) -> None:
        if type(new_generation) is not int or new_generation <= self.generation:
            raise ValueError("generation must increase")
        self.generation = new_generation
        self.energy = 100
        self.shield_granted = 0
        self.mark = None
        self.last_event_sequence = 0
        # Real server cooldowns are retained across controller replacement.
        # Server clock is monotonic across generations, never reset.

    def admit(self, ability_id: str, proof: AuthoritativeSnapshot) -> AdmissionReceipt:
        def deny(reason: str) -> AdmissionReceipt:
            return AdmissionReceipt(False, reason, self.energy)

        # All preflight fields are server-generated. Reject malformed clocks and
        # out-of-order time before any resource/effect mutation.
        now = proof.server_time_ms
        sequence = proof.server_event_sequence
        if type(now) is not int or not 0 <= now <= self.MAX_SEQUENCE:
            return deny("untrusted server clock")
        if now < self.last_server_time_ms:
            return deny("clock regression")
        if (not proof.owner_authorized or not proof.controller_lease_valid
                or type(proof.generation) is not int or proof.generation != self.generation):
            return deny("owner/controller/generation")
        if type(sequence) is not int or not self.last_event_sequence < sequence <= self.MAX_SEQUENCE:
            return deny("duplicate/stale server event")
        # Consume an authenticated server event even if downstream preflight fails.
        # This blocks retries of the same paid-attack receipt after a miss.
        self.last_event_sequence = sequence
        self.last_server_time_ms = now

        ability = self.abilities.get(ability_id)
        if ability is None or ability.get("native_enabled") is not False:
            return deny("unknown or enabled ability")
        if now < self.ready_at_ms.get(ability_id, 0):
            return deny("cooldown")
        cost = ability["energy_cost"] + ability["upstream_energy_cost"]
        if cost <= 0 or cost > self.max_spend:
            return deny("transaction cost outside cap")
        if self.energy < cost:
            return deny("energy")

        targets = proof.targets
        if not isinstance(targets, tuple):
            return deny("target evidence must be immutable snapshot")
        is_attack = ability["damage_each"] > 0
        if is_attack:
            if not 1 <= len(targets) <= ability["max_targets"]:
                return deny("invalid target count")
            ids = [t.target_id for t in targets]
            if len(set(ids)) != len(ids):
                return deny("duplicated target")
            for target in targets:
                if (not target.target_id.startswith("MON-") or len(target.target_id) <= 4
                        or not target.registered_monster or not target.alive
                        or not target.vulnerable or target.friendly or target.player
                        or target.boss or target.companion or target.sovereign_army
                        or target.invulnerable or not target.line_of_sight
                        or not target.within_cone):
                    return deny("unregistered/protected/covered target")
                if (type(target.distance_cm) not in (int, float)
                        or not math.isfinite(target.distance_cm)
                        or not 0 <= target.distance_cm <= ability["range_cm"]):
                    return deny("invalid target range")
                if (type(target.health_fraction) not in (int, float)
                        or not math.isfinite(target.health_fraction)
                        or not 0 <= target.health_fraction <= 1):
                    return deny("invalid target health")
                if ability_id == "SFA-011" and target.health_fraction > 0.25:
                    return deny("finisher target above threshold")
                if ability_id == "SFA-007" and target.status_immune:
                    return deny("native status immunity")
        elif targets:
            return deny("self-only ability cannot select targets")

        if ability_id == "SFA-010" and not (proof.destination_authored
                                           and proof.destination_clear
                                           and proof.destination_line_of_sight):
            return deny("unsafe destination")

        restored = 0
        if ability["shield_restore_cap"]:
            if (type(proof.shield) is not int or type(proof.max_shield) is not int
                    or not 0 <= proof.shield <= proof.max_shield <= 500):
                return deny("invalid shield snapshot")
            restored = min(ability["shield_restore_cap"], proof.max_shield - proof.shield,
                           self.shield_pool - self.shield_granted)
            if restored <= 0:
                return deny("shared shield allowance exhausted")

        damage = len(targets) * ability["damage_each"] * ability["max_pulses"]
        if (ability_id == "SFA-002" and proof.equipped_class_id == "CLS-006"
                and self.mark is not None and self.mark[0] in (t.target_id for t in targets)
                and self.mark[1] > now and self.mark[2] == self.generation):
            damage += 4  # total bonus, not per target/pulse
        if damage > self.max_damage:
            return deny("damage ceiling")

        # Commit only after every guard has passed. In UEFN this must become a
        # single server-side reservation/effect acknowledgement transaction.
        self.energy -= cost
        self.ready_at_ms[ability_id] = now + int(ability["cooldown_seconds"] * 1000)
        self.shield_granted += restored
        if ability_id == "SFA-001":
            self.mark = (targets[0].target_id, now + 4000, self.generation)
        return AdmissionReceipt(True, "reference-only; native effects disabled",
                                self.energy, damage, restored, sequence)
