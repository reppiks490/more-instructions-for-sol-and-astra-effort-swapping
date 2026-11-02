"""Deterministic FUS-001 policy model, not a Verse runtime or native test."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ArsenalModel:
    owner: str = "creator"
    generation: int = 1
    energy: int = 100
    deadline: float = 90.0
    active: bool = True
    last_used: dict[str, float] = field(default_factory=dict)
    marked: str = ""
    marked_at: float = -1000.0
    shield_granted: float = 0.0

    def request(
        self, ability: str, now: float, caller: str, generation: int,
        *, target: str = "", distance: float = 0.0, view_cosine: float = 1.0,
        hostile: bool = True, vulnerable: bool = True, class_id: str = "",
        target_count: int = 1, shield: float = 0.0, max_shield: float = 100.0
    ) -> tuple[bool, float]:
        if not self.active or caller != self.owner or generation != self.generation:
            return False, 0.0
        if now < 0 or now >= self.deadline:
            return False, 0.0
        rules = {
            "rend": (15, 2.0),  # Avatar 10 + Arsenal 5
            "collapse": (20, 8.0),
            "bulwark": (15, 18.0),
        }
        if ability not in rules:
            return False, 0.0
        cost, cooldown = rules[ability]
        if self.energy < cost or now < self.last_used.get(ability, -1000.0) + cooldown:
            return False, 0.0
        if ability != "bulwark":
            if not target.startswith("MON-") or not hostile or not vulnerable:
                return False, 0.0
            limit, minimum_cosine = ((350, 0.70) if ability == "rend" else (650, 0.85))
            if not 0 < distance <= limit or view_cosine < minimum_cosine:
                return False, 0.0
        if ability == "rend":
            effect = 18.0
            self.marked, self.marked_at = target, now
        elif ability == "collapse":
            if not 1 <= target_count <= 3:
                return False, 0.0
            effect = 10.0 * target_count
            if class_id == "CLS-006" and self.marked == target and now < self.marked_at + 4.0:
                effect += 4.0
        else:
            if max_shield > 500.0 or max_shield <= shield:
                return False, 0.0
            effect = min(20.0, max_shield - shield, 40.0 - self.shield_granted)
            if effect < 1.0:
                return False, 0.0
            self.shield_granted += effect
        self.energy -= cost
        self.last_used[ability] = now
        return True, effect
