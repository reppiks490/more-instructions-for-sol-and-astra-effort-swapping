"""Bounded source-only hit/pulse settlement for FUS-001 Arsenal attacks.

This is an executable reference of the *post-admission* server contract, not
native damage, collision, authority, or a UEFN adapter. A real adapter must
atomically obtain its plans from the Architect's paid, generation-bound receipt
and a native actor-registry/LOS preflight. Never accept plans from clients.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MAX_DAMAGE_PER_REQUEST = 54
MAX_TARGETS = 3
MAX_PULSES = 2
MAX_ACTIVE_PLANS = 64
MAX_SEQUENCE = 2**63 - 1
# Canonical offensive SFA identities: (damage/pulse, pulses, maximum targets).
# Self-only armor/tempo/reposition actions intentionally have no hit slots.
ATTACK_SPECS = {
    "SFA-001": (18, 1, 1), "SFA-002": (10, 1, 3),
    "SFA-004": (8, 1, 1), "SFA-005": (6, 2, 3),
    "SFA-007": (4, 1, 1), "SFA-009": (12, 1, 2),
    "SFA-011": (20, 1, 1), "SFA-012": (12, 1, 3),
}


@dataclass(frozen=True)
class HitPlan:
    """Offline representation of one already-admitted, paid attack."""
    generation: int
    event_sequence: int
    ability_id: str
    target_ids: tuple[str, ...]
    damage_each: int
    pulses: int
    damage_upper_bound: int
    bonus_target_id: str = ""
    bonus_damage_total: int = 0


@dataclass(frozen=True)
class HitDecision:
    accepted: bool
    reason: str
    damage: int = 0
    event_sequence: int = 0
    slots_consumed: int = 0
    damage_committed: int = 0


@dataclass
class _ActivePlan:
    plan: HitPlan
    slots: set[tuple[str, int]] = field(default_factory=set)
    damage_committed: int = 0
    bonus_used: bool = False


class SourceHitJournal:
    """Deterministic per-generation, per-event, per-target/pulse hit ledger.

    Stage does not grant access: the caller MUST validate the plan against
    an authoritative paid admission receipt before invoking this model. Its
    returned damage is an upper-bound proposal, not a native effect call.
    """

    def __init__(self) -> None:
        self._active: dict[tuple[int, int], _ActivePlan] = {}
        self._seen: set[tuple[int, int]] = set()
        self._generation = 1

    @property
    def generation(self) -> int:
        return self._generation

    @staticmethod
    def _valid(plan: object) -> bool:
        if type(plan) is not HitPlan:
            return False
        if (type(plan.generation) is not int or plan.generation <= 0
                or type(plan.event_sequence) is not int
                or not 1 <= plan.event_sequence <= MAX_SEQUENCE
                or type(plan.ability_id) is not str
                or plan.ability_id not in ATTACK_SPECS
                or type(plan.target_ids) is not tuple
                or not 1 <= len(plan.target_ids) <= MAX_TARGETS):
            return False
        if any(type(t) is not str or len(t) <= 4 or not t.startswith("MON-")
               for t in plan.target_ids):
            return False
        if len(set(plan.target_ids)) != len(plan.target_ids):
            return False
        if (type(plan.damage_each) is not int or plan.damage_each <= 0
                or type(plan.pulses) is not int or not 1 <= plan.pulses <= MAX_PULSES
                or type(plan.damage_upper_bound) is not int
                or not 1 <= plan.damage_upper_bound <= MAX_DAMAGE_PER_REQUEST
                or type(plan.bonus_target_id) is not str
                or type(plan.bonus_damage_total) is not int):
            return False
        canonical_damage, canonical_pulses, canonical_targets = ATTACK_SPECS[plan.ability_id]
        if (plan.damage_each != canonical_damage or plan.pulses != canonical_pulses
                or len(plan.target_ids) > canonical_targets):
            return False
        if plan.bonus_damage_total:
            if (plan.ability_id != "SFA-002" or plan.pulses != 1
                    or plan.bonus_damage_total != 4
                    or plan.bonus_target_id not in plan.target_ids):
                return False
        elif plan.bonus_target_id:
            return False
        return (plan.damage_upper_bound ==
                len(plan.target_ids) * plan.damage_each * plan.pulses
                + plan.bonus_damage_total)

    def stage(self, plan: HitPlan) -> bool:
        """Stage a validated source-only attack; duplicates are never reset."""
        if not self._valid(plan) or plan.generation != self._generation:
            return False
        key = (plan.generation, plan.event_sequence)
        if key in self._seen or len(self._active) >= MAX_ACTIVE_PLANS:
            return False
        self._active[key] = _ActivePlan(plan)
        self._seen.add(key)
        return True

    def resolve(self, generation: int, event_sequence: int, target_id: str,
                pulse_index: int, *, native_hit_confirmed: bool) -> HitDecision:
        """Record one server-observed hit/miss; never perform damage itself.

        A well-formed miss consumes its unique slot, preventing a late retry
        from converting a miss into a hit. Malformed evidence consumes nothing.
        """
        def deny(reason: str) -> HitDecision:
            return HitDecision(False, reason)

        if (type(generation) is not int or type(event_sequence) is not int
                or type(target_id) is not str or type(pulse_index) is not int
                or type(native_hit_confirmed) is not bool):
            return deny("malformed native hit evidence")
        if generation != self._generation:
            return deny("stale generation")
        active = self._active.get((generation, event_sequence))
        if active is None:
            return deny("unknown or closed event")
        plan = active.plan
        if target_id not in plan.target_ids or not 0 <= pulse_index < plan.pulses:
            return deny("target or pulse outside paid plan")
        slot = (target_id, pulse_index)
        if slot in active.slots:
            return deny("duplicate target/pulse")
        bonus = 0
        if (native_hit_confirmed and not active.bonus_used
                and target_id == plan.bonus_target_id and pulse_index == 0):
            bonus = plan.bonus_damage_total
        proposed = plan.damage_each + bonus if native_hit_confirmed else 0
        if active.damage_committed + proposed > plan.damage_upper_bound:
            return deny("request damage cap")
        active.slots.add(slot)
        active.damage_committed += proposed
        if bonus:
            active.bonus_used = True
        return HitDecision(True, "source-only hit recorded" if native_hit_confirmed
                           else "source-only miss recorded", proposed,
                           event_sequence, len(active.slots), active.damage_committed)

    def close(self, generation: int, event_sequence: int) -> bool:
        """Close after native effect acknowledgement/timeout; never re-open."""
        if type(generation) is not int or type(event_sequence) is not int:
            return False
        return self._active.pop((generation, event_sequence), None) is not None

    def change_generation(self, new_generation: int) -> None:
        """Revoke all old plans, including outstanding hit acknowledgements."""
        if type(new_generation) is not int or new_generation <= self._generation:
            raise ValueError("generation must increase")
        self._active.clear()
        self._seen.clear()
        self._generation = new_generation


def plan_from_admission(*, ability: dict, generation: int, event_sequence: int,
                        target_ids: tuple[str, ...], admitted: bool,
                        damage_upper_bound: int, marked_target_id: str = "") -> HitPlan | None:
    """Translate already-verified admission data; never authenticate a receipt.

    The caller must compare the event to the real Architect receipt, energy
    debit, controller lease, target registry and native LOS. This function is
    deliberately incapable of checking those UEFN facts.
    """
    if admitted is not True or type(ability) is not dict:
        return None
    if type(damage_upper_bound) is not int or type(marked_target_id) is not str:
        return None
    if type(target_ids) is not tuple:
        return None
    damage_each = ability.get("damage_each")
    pulses = ability.get("max_pulses")
    if (type(damage_each) is not int or damage_each <= 0
            or type(pulses) is not int or not 1 <= pulses <= MAX_PULSES
            or type(ability.get("id")) is not str):
        return None
    bonus = damage_upper_bound - len(target_ids) * damage_each * pulses
    if type(bonus) is not int or bonus not in (0, 4):
        return None
    if bonus and (ability.get("id") != "SFA-002" or marked_target_id not in target_ids):
        return None
    plan = HitPlan(generation, event_sequence, ability.get("id"), target_ids,
                   damage_each, pulses,
                   damage_upper_bound, marked_target_id if bonus else "", bonus)
    return plan if SourceHitJournal._valid(plan) else None
