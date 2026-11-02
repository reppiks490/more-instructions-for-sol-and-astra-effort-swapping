#!/usr/bin/env python3
"""Universe-first FUS-001 arsenal design contract, NOT a Verse/UEFN compiler.

The dry-run reference model below never grants access or applies native effects.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "content/sovereign/sovereign_arsenal_universe_contract.json"
EXISTING = ROOT / "content/sovereign/sovereign_arsenal.json"
REQUIRED_IMMUNITIES = {
    "no_native_invulnerability", "no_boss_mechanic_bypass", "no_status_immunity",
    "no_team_or_permission_changes", "no_player_damage", "no_ally_or_companion_damage",
    "no_teleport_through_geometry",
}
REQUIRED_ASSETS = {"mesh", "animation", "vfx", "audio", "accessibility"}


def load_contract(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract: dict, existing: dict) -> list[str]:
    errors: list[str] = []

    def require(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    require(contract.get("form_id") == "FUS-001" and contract.get("parent_ability_id") == "UNI-001", "canonical fusion identity changed")
    gate = contract.get("universe_first_gate", {})
    require(all(gate.get(k) is False for k in ("world_content_complete", "prototype_allowed", "native_enablement_allowed")), "universe-first stop gate must remain closed")
    require(gate.get("editor_validation") == "not_run", "editor evidence cannot be inferred from source")
    identity = contract.get("identity", {})
    require(identity.get("authority") == "aeonfall_fusion_state_runtime.IsAuthorizedActive", "canonical authority replaced")
    require(identity.get("owner_limit") == 1 and identity.get("display_name_authorization") is False, "owner-only identity weakened")
    require(identity.get("session_generation_required") is True and identity.get("controller_lease_required") is True and identity.get("rebind_within_session") is False, "controller/generation policy weakened")
    progression = contract.get("progression_invariants", {})
    require(all(progression.get(k) is value for k, value in {
        "transcendent_zero_unchanged": True, "axiom_heart_unchanged": True,
        "ordinary_unlockable": False, "titan_fusion_enabled": False,
        "permission_escalation": False,
    }.items()), "canonical progression or permissions changed")
    resource = contract.get("resource_invariants", {})
    require(all(resource.get(k) == v for k, v in {
        "pool": "canonical_fusion_budget", "initial_energy": 100, "max_energy": 120,
        "max_spend_per_transaction": 25, "max_shield_per_generation_shared": 40,
        "max_damage_per_request": 54, "max_targets_per_request": 3,
    }.items()), "resource bounds changed")
    require(all(resource.get(k) is True for k in ("no_passive_recharge", "cooldowns_persist_on_adapter_replacement", "no_cooldown_bypass")), "resource lifetime policy weakened")
    require(REQUIRED_IMMUNITIES <= set(contract.get("immunity_exceptions", [])), "immunity exceptions missing")
    require(all(v == "not_run" for v in contract.get("acceptance", {}).values()) and len(contract.get("acceptance", {})) == 7, "unverified native evidence promoted")
    synergy = contract.get("synergy", {})
    require(all(synergy.get(k) == v for k, v in {
        "class_id": "CLS-006", "source_ability": "SFA-001", "consumer_ability": "SFA-002",
        "mark_duration_seconds": 4, "max_bonus_damage_total": 4,
        "requires_equipped_class": True, "no_class_grant": True, "no_profile_write": True,
    }.items()), "class synergy escaped bounded existing contract")

    abilities = contract.get("abilities", [])
    require(isinstance(abilities, list) and len(abilities) == 12, "expected twelve distinct arsenal definitions")
    if not isinstance(abilities, list):
        return errors
    ids = [a.get("id") for a in abilities if isinstance(a, dict)]
    require(ids == [f"SFA-{i:03d}" for i in range(1, 13)], "ability IDs missing, reordered or duplicated")
    require(len({a.get("mechanic_id") for a in abilities if isinstance(a, dict)}) == 12, "mechanical identities must be unique")
    for i, ability in enumerate(abilities):
        if not isinstance(ability, dict):
            errors.append(f"ability {i} is not a record")
            continue
        aid = ability.get("id", f"index-{i}")
        status = "source_only_disabled" if i < 3 else "design_only"
        require(ability.get("implementation_status") == status, f"{aid}: invalid staged status")
        require(ability.get("adapter") == ("verse/sovereign/sovereign_arsenal_device.verse" if i < 3 else None), f"{aid}: unauthorized native adapter claim")
        for k, value in (("owner_only", True), ("native_enabled", False), ("permission_changes", False), ("persistent_grant", False),
                         ("target_players", False), ("target_bosses", False), ("target_companions", False), ("target_sovereign_army", False)):
            require(ability.get(k) is value, f"{aid}: {k} violates isolation")
        for k, low, high in (("energy_cost", 1, 25), ("upstream_energy_cost", 0, 10),
                             ("cooldown_seconds", 2, 120), ("range_cm", 0, 650),
                             ("max_targets", 1, 3), ("damage_each", 0, 20),
                             ("max_pulses", 1, 2), ("bonus_damage_total", 0, 4),
                             ("shield_restore_cap", 0, 20), ("effect_duration_seconds", 0, 8)):
            n = ability.get(k)
            require(type(n) in (int, float) and low <= n <= high, f"{aid}: invalid {k}")
        # Counts and debits are discrete native transactions, not fractional
        # Python floats. Include Avatar's upstream Reaver charge in the cap.
        for discrete in ("energy_cost", "upstream_energy_cost", "max_targets",
                         "damage_each", "max_pulses", "bonus_damage_total",
                         "shield_restore_cap"):
            require(type(ability.get(discrete)) is int, f"{aid}: {discrete} must be integer")
        spent = ability.get("energy_cost", 0) + ability.get("upstream_energy_cost", 0)
        require(spent <= resource.get("max_spend_per_transaction", 25),
                f"{aid}: combined upstream plus arsenal debit exceeds cap")
        if not all(type(ability.get(k)) is int for k in
                   ("damage_each", "max_targets", "max_pulses", "bonus_damage_total")):
            continue
        damage = ability["damage_each"] * ability["max_targets"] * ability["max_pulses"] + ability["bonus_damage_total"]
        require(damage <= 54, f"{aid}: per-request damage exceeds cap")
        offensive = ability["damage_each"] > 0
        require(ability.get("target_family") == ("MON-" if offensive else "self"), f"{aid}: invalid target family")
        require(ability.get("requires_live_vulnerable_character") is offensive, f"{aid}: vulnerability guard mismatch")
        require(ability.get("requires_line_of_sight") is (offensive or aid == "SFA-010"), f"{aid}: cover/LOS contract mismatch")
        require(ability.get("shield_generation_pool") == ("shared_40" if ability.get("shield_restore_cap", 0) else None), f"{aid}: shield pool bypass")
        require(bool(ability.get("counterplay")) and bool(ability.get("telegraph")), f"{aid}: telegraph/counterplay absent")
        notes = ability.get("notes", {})
        if aid == "SFA-004":
            require(notes.get("no_forced_displacement") is True,
                    "SFA-004: cannot grant forced displacement")
        if aid == "SFA-006":
            require(notes.get("max_tempo_multiplier") == 1.15,
                    "SFA-006: native tempo ceiling drift")
        if aid == "SFA-010":
            require(notes.get("requires_authored_destination") is True
                    and notes.get("no_wall_phasing") is True,
                    "SFA-010: bounded authored anchor and no wall phasing required")
        if aid == "SFA-011":
            require(notes.get("threshold_health_fraction_max") == 0.25,
                    "SFA-011: finisher threshold drift")
        assets = ability.get("asset_plan", {})
        require(isinstance(assets, dict) and REQUIRED_ASSETS <= set(assets) and all(isinstance(assets.get(k), str) and assets[k].startswith(aid + "-") for k in REQUIRED_ASSETS), f"{aid}: missing distinct asset plans")
    if len(abilities) >= 3:
        old = existing.get("weapons", [])
        for i in range(3):
            a, b = abilities[i], old[i]
            require(a.get("id") == b.get("ability") and a.get("energy_cost") == b.get("energy_cost") and a.get("cooldown_seconds") == b.get("cooldown_seconds") and a.get("range_cm") == b.get("range_cm", 0), f"{a.get('id')}: existing source kit drift")
        require(abilities[0].get("damage_each") == old[0].get("damage") and abilities[0].get("upstream_energy_cost") == old[0].get("upstream_avatar_energy_cost"), "Reaver damage/upstream payment drift")
        require(abilities[1].get("damage_each") == old[1].get("base_damage_each") and abilities[1].get("max_targets") == old[1].get("max_targets") and abilities[1].get("bonus_damage_total") == old[1].get("sepulchral_mark_bonus_each"), "Cataclysm damage/mark drift")
        require(abilities[2].get("shield_restore_cap") == old[2].get("shield_restore"), "Aegis shield drift")
    return errors


@dataclass(frozen=True)
class DryRunReceipt:
    allowed: bool
    reason: str
    energy_after: int
    damage_upper_bound: int = 0
    shield_restored: int = 0


class DryRunArsenal:
    """Deterministic paper-only contract oracle; not an authoritative adapter."""
    def __init__(self, contract: dict):
        self.abilities = {a["id"]: a for a in contract["abilities"]}
        self.energy = 100
        self.generation = 1
        self.cooldowns: dict[str, float] = {}
        self.shield_granted = 0
        self.mark: tuple[str, float, int] | None = None

    def change_generation(self, token: int) -> None:
        if token <= self.generation:
            raise ValueError("generation must increase")
        self.generation = token
        self.energy = 100
        self.shield_granted = 0
        self.mark = None
        # Cooldowns intentionally survive adapter/generation changes.

    def cast(self, aid: str, now: float, *, owner: bool = True, token: int = 1,
             target_id: str = "MON-001", target_count: int = 1,
             los: bool = True, vulnerable: bool = True, class_id: str = "",
             shield: int = 0, max_shield: int = 100,
             health_fraction: float = 0.2, destination_authored: bool = True) -> DryRunReceipt:
        a = self.abilities[aid]
        def deny(reason: str) -> DryRunReceipt:
            return DryRunReceipt(False, reason, self.energy)
        if not owner or token != self.generation:
            return deny("owner/generation")
        if now < self.cooldowns.get(aid, -1.0):
            return deny("cooldown")
        cost = a["energy_cost"] + a["upstream_energy_cost"]
        if self.energy < cost:
            return deny("energy")
        if not 1 <= target_count <= a["max_targets"]:
            return deny("target count")
        if a["damage_each"]:
            if not target_id.startswith("MON-") or not vulnerable or (a["requires_line_of_sight"] and not los):
                return deny("protected/covered target")
        if aid == "SFA-011" and not 0 <= health_fraction <= 0.25:
            return deny("finisher threshold")
        if aid == "SFA-010" and (not destination_authored or not los):
            return deny("invalid authored destination")
        restored = 0
        if a["shield_restore_cap"]:
            if not 0 <= shield <= max_shield <= 500:
                return deny("shield bounds")
            restored = min(a["shield_restore_cap"], max_shield - shield, 40 - self.shield_granted)
            if restored < 1:
                return deny("shield exhausted")
        damage = target_count * a["damage_each"] * a["max_pulses"]
        if aid == "SFA-002" and class_id == "CLS-006" and self.mark and self.mark == (target_id, self.mark[1], token) and now < self.mark[1]:
            damage += 4
        self.energy -= cost
        self.cooldowns[aid] = now + a["cooldown_seconds"]
        self.shield_granted += restored
        if aid == "SFA-001":
            self.mark = (target_id, now + 4.0, token)
        return DryRunReceipt(True, "dry-run only", self.energy, damage, restored)


def main() -> int:
    errors = validate(load_contract(), json.loads(EXISTING.read_text(encoding="utf-8")))
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print("PASS: 12 bounded FUS-001 arsenal definitions; universe-first native gate remains CLOSED (source only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
