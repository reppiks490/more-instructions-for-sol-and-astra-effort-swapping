"""Mutation regressions for FUS-001 adapter; NOT native UEFN execution."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fusion_guard", ROOT / "tools/validate_sovereign_fusion.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class FusionSourceGuards(unittest.TestCase):
    def setUp(self):
        self.runtime = (ROOT / guard.RUNTIME).read_text(encoding="utf-8")
        self.device = (ROOT / guard.DEVICE).read_text(encoding="utf-8")
        self.policy = json.loads((ROOT / guard.POLICY).read_text(encoding="utf-8"))

    def mutate(self, target, old, replacement):
        source = getattr(self, target)
        self.assertIn(old, source)
        setattr(self, target, source.replace(old, replacement, 1))
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_authored_sources_pass(self):
        self.assertEqual(guard.check_sources(self.runtime, self.device, self.policy), [])

    def test_disabled_by_default(self):
        self.mutate("device", "Enabled:logic = false", "Enabled:logic = true")

    def test_architect_state_is_required(self):
        self.mutate("device", "GetAEONFALLFusionState[]", "GetAEONFALLSovereignFusionRuntime[]")

    def test_native_authority_is_reused(self):
        self.mutate("device", "State.AcquireController(Self, Authority)", "State.AcquireController(Self, FakeAuthority)")

    def test_native_identity_is_rechecked_for_spending(self):
        self.mutate("runtime", "Authorized := State.IsAuthorizedActive(Device, Player, NewToken)", "Authorized := true")

    def test_single_budget_controller(self):
        self.mutate("runtime", "if (Controller?):", "if (false?):")

    def test_cooldown_before_reentry(self):
        self.mutate("runtime", "GetSimulationElapsedTime() >= CooldownUntil", "GetSimulationElapsedTime() >= 0.0")

    def test_cooldown_survives_replacement(self):
        self.mutate("runtime", "set Controller = false", "set CooldownUntil = 0.0\n            set Controller = false")

    def test_active_token_cannot_be_substituted(self):
        self.mutate("runtime", "Token = NewToken", "NewToken > 0")

    def test_spending_requires_energy(self):
        self.mutate("runtime", "Remaining >= Cost", "Remaining >= 0")

    def test_negative_energy_spend_rejected(self):
        self.mutate("runtime", "Cost > 0", "Cost >= 0")

    def test_unbounded_energy_spend_rejected(self):
        self.mutate("runtime", "Cost <= 25", "Cost <= 999")

    def test_bad_resource_cap_rejected(self):
        self.mutate("runtime", "Capacity <= 120", "Capacity <= 1200")

    def test_unsupported_titan_form_rejected(self):
        self.mutate("device", '"FUS-001"', '"FUS-002"')

    def test_activation_requires_native_visual_ack(self):
        self.mutate("device", "ArmorGlow.HasEffect[Player]", "Player.IsActive[]")

    def test_cleanup_precedes_fusion_completion(self):
        self.mutate("device", "ClearPhysical()", "set Token = Token",)

    def test_character_swap_exits(self):
        self.mutate("device", "Character = OriginalCharacter", "Player.IsActive[]")

    def test_only_owner_can_separate(self):
        self.mutate("device", "Owner = Player", "Player.IsActive[]")

    def test_camera_cleanup(self):
        self.mutate("device", "ArmorCamera.RemoveFrom(Owner)", "ArmorCamera.AddTo(Owner)")

    def test_visual_cleanup(self):
        self.mutate("device", "ArmorGlow.Clear(Owner)", "ArmorGlow.Pickup(Owner)")

    def test_no_global_grants(self):
        self.device += "\n    Bad():void=\n        ArmorCamera.AddToAll()\n"
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_no_parallel_owner(self):
        self.runtime += "\n    var Owner:?player = false\n"
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_unverified_npc_possession_not_claimed(self):
        self.policy["titan_possession_implemented"] = True
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_no_fabricated_native_compile(self):
        self.policy["engine_verification"]["compile"] = "passed"
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))


if __name__ == "__main__":
    unittest.main()
