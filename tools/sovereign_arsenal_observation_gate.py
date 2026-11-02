"""Source-only per-pulse safety gate for FUS-001 Sovereign attacks.

This reference model is NOT an authoritative UEFN adapter. All observations,
actor keys and paid plans must originate in trusted server services. Never
construct them from client RPCs or expose the underlying journal as a grant.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
import re

from tools.sovereign_arsenal_admission import RegisteredTarget
from tools.sovereign_arsenal_hit_journal import (
    ATTACK_SPECS, HitDecision, HitPlan, MAX_ACTIVE_PLANS, MAX_SEQUENCE,
    SourceHitJournal,
)
from tools.validate_sovereign_arsenal_universe import load_contract

REGIONS = frozenset(f"REG-{n:03d}" for n in range(1, 14))
MAX_OBSERVATION_WINDOW_MS = 6000
_TARGET_FLAGS = (
    "registered_monster", "alive", "vulnerable", "friendly", "player",
    "boss", "companion", "sovereign_army", "invulnerable",
    "status_immune", "line_of_sight", "within_cone",
)


@dataclass(frozen=True)
class BoundActor:
    """Server registry binding; actor_key identifies an instance, not a name."""
    target_id: str
    actor_key: str
    region_id: str


@dataclass(frozen=True)
class HitObservation:
    """A fresh server-only collision/registry/LOS snapshot for ONE pulse."""
    generation: int
    event_sequence: int
    pulse_index: int
    server_time_ms: int
    actor_key: str
    region_id: str
    owner_authorized: bool
    controller_lease_valid: bool
    native_hit_confirmed: bool
    target: RegisteredTarget


@dataclass
class _BoundPlan:
    plan: HitPlan
    actors: dict[str, BoundActor]
    opened_ms: int
    deadline_ms: int
    last_observed_ms: int


class SourceHitObservationGate:
    """Bounded, fail-closed *offline* adapter around the hit journal.

    Only a native server can authenticate paid receipts, actor instances,
    collision, cover, region unload, owner revocation or actual effect writes.
    This gate models what that server must enforce at every hit pulse.
    """

    def __init__(self, contract: dict | None = None) -> None:
        contract = load_contract() if contract is None else contract
        gate = contract["universe_first_gate"]
        if any(gate[k] is not False for k in (
                "world_content_complete", "prototype_allowed",
                "native_enablement_allowed")):
            raise ValueError("universe-first native activation must stay disabled")
        self._abilities: dict[str, dict] = {}
        for ability in contract["abilities"]:
            ident = ability["id"]
            if ident not in ATTACK_SPECS:
                continue
            if ident in self._abilities:
                raise ValueError(f"duplicate offensive contract: {ident}")
            if (ability["native_enabled"] is not False
                    or (ability["damage_each"], ability["max_pulses"],
                        ability["max_targets"]) != ATTACK_SPECS[ident]
                    or type(ability["range_cm"]) is not int
                    or not 0 < ability["range_cm"] <= 650):
                raise ValueError(f"unsafe offensive ability contract: {ident}")
            self._abilities[ident] = ability
        if set(self._abilities) != set(ATTACK_SPECS):
            raise ValueError("missing offensive Sovereign contracts")
        self._journal = SourceHitJournal()
        self._bound: dict[tuple[int, int], _BoundPlan] = {}
        self._revoked = False

    @property
    def active_count(self) -> int:
        return len(self._bound)

    @property
    def generation(self) -> int:
        return self._journal.generation

    @staticmethod
    def _valid_actor(actor: object) -> bool:
        return (type(actor) is BoundActor
                and type(actor.target_id) is str
                and re.fullmatch(r"MON-[0-9]{3,4}", actor.target_id) is not None
                and type(actor.actor_key) is str
                and 1 <= len(actor.actor_key) <= 96
                and type(actor.region_id) is str and actor.region_id in REGIONS)

    @staticmethod
    def _valid_observation(obs: object) -> bool:
        if type(obs) is not HitObservation:
            return False
        if (any(type(getattr(obs, name)) is not int for name in (
                "generation", "event_sequence", "pulse_index", "server_time_ms"))
                or not 1 <= obs.event_sequence <= MAX_SEQUENCE
                or obs.generation <= 0 or obs.pulse_index < 0
                or not 0 <= obs.server_time_ms <= MAX_SEQUENCE
                or type(obs.actor_key) is not str
                or type(obs.region_id) is not str
                or any(type(getattr(obs, name)) is not bool for name in (
                    "owner_authorized", "controller_lease_valid", "native_hit_confirmed"))
                or type(obs.target) is not RegisteredTarget
                or type(obs.target.target_id) is not str):
            return False
        if any(type(getattr(obs.target, name)) is not bool for name in _TARGET_FLAGS):
            return False
        for name in ("distance_cm", "health_fraction"):
            value = getattr(obs.target, name)
            if type(value) not in (int, float) or not math.isfinite(value):
                return False
        return True

    def stage(self, plan: HitPlan, bindings: tuple[BoundActor, ...], *,
              opened_ms: int, deadline_ms: int) -> bool:
        """Stage only after a separate server has atomically paid the receipt."""
        if (self._revoked or not SourceHitJournal._valid(plan)
                or plan.generation != self.generation
                or type(bindings) is not tuple
                or len(bindings) != len(plan.target_ids)
                or any(not self._valid_actor(actor) for actor in bindings)
                or tuple(actor.target_id for actor in bindings) != plan.target_ids
                or len({actor.actor_key for actor in bindings}) != len(bindings)
                or len({actor.region_id for actor in bindings}) != 1
                or type(opened_ms) is not int or type(deadline_ms) is not int
                or not 0 <= opened_ms < deadline_ms <= MAX_SEQUENCE
                or deadline_ms - opened_ms > MAX_OBSERVATION_WINDOW_MS
                or len(self._bound) >= MAX_ACTIVE_PLANS):
            return False
        if not self._journal.stage(plan):
            return False
        self._bound[(plan.generation, plan.event_sequence)] = _BoundPlan(
            plan, {actor.target_id: actor for actor in bindings},
            opened_ms, deadline_ms, opened_ms,
        )
        return True

    def resolve(self, observation: HitObservation) -> HitDecision:
        """A protected/covered hit becomes a terminal zero-damage miss.

        Malformed proof does not consume a slot; a well-formed live target that
        became protected does consume it. Stale actors, region transfers,
        expiry and owner/lease revocation invalidate outstanding work.
        """
        def deny(reason: str) -> HitDecision:
            return HitDecision(False, reason)

        if not self._valid_observation(observation):
            return deny("malformed server observation")
        if self._revoked or observation.generation != self.generation:
            return deny("revoked generation")
        key = (observation.generation, observation.event_sequence)
        bound = self._bound.get(key)
        if bound is None:
            return deny("unknown or closed paid event")
        target_id = observation.target.target_id
        actor = bound.actors.get(target_id)
        if actor is None or observation.pulse_index >= bound.plan.pulses:
            return deny("target/pulse not in paid plan")
        if (observation.actor_key != actor.actor_key
                or observation.region_id != actor.region_id):
            self.close(*key)
            return deny("actor instance or region changed; event revoked")
        if observation.server_time_ms < bound.last_observed_ms:
            return deny("server clock regression")
        if not observation.owner_authorized or not observation.controller_lease_valid:
            self.revoke()
            return deny("owner or controller lease revoked")
        if observation.server_time_ms > bound.deadline_ms:
            self.close(*key)
            return deny("paid event expired")
        bound.last_observed_ms = observation.server_time_ms
        target = observation.target
        ability = self._abilities[bound.plan.ability_id]
        allowed = (
            target.registered_monster and target.alive and target.vulnerable
            and not (target.friendly or target.player or target.boss
                     or target.companion or target.sovereign_army
                     or target.invulnerable)
            and target.line_of_sight and target.within_cone
            and 0 <= target.distance_cm <= ability["range_cm"]
            and 0 <= target.health_fraction <= 1
            and (bound.plan.ability_id != "SFA-007" or not target.status_immune)
            and (bound.plan.ability_id != "SFA-011"
                 or target.health_fraction <= 0.25)
        )
        hit = allowed and observation.native_hit_confirmed
        decision = self._journal.resolve(
            observation.generation, observation.event_sequence,
            target_id, observation.pulse_index, native_hit_confirmed=hit,
        )
        if decision.accepted and not allowed:
            decision = replace(decision, reason="protected/covered target: terminal miss")
        if decision.accepted and decision.slots_consumed == (
                len(bound.actors) * bound.plan.pulses):
            self.close(*key)
        return decision

    def close(self, generation: int, event_sequence: int) -> bool:
        if type(generation) is not int or type(event_sequence) is not int:
            return False
        key = (generation, event_sequence)
        self._bound.pop(key, None)
        return self._journal.close(generation, event_sequence)

    def revoke(self) -> None:
        """Terminal owner/session/stream teardown; no restaging this generation."""
        self._revoked = True
        for generation, sequence in tuple(self._bound):
            self.close(generation, sequence)

    def change_generation(self, new_generation: int) -> None:
        self._journal.change_generation(new_generation)
        self._bound.clear()
        self._revoked = False
