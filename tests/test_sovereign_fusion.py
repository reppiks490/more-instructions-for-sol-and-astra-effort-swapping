"""Mutation regression tests; inspect source policy, not executed Verse/UEFN."""
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

    def test_canonical_sources_pass(self):
        self.assertEqual(guard.check_sources(self.runtime, self.device, self.policy), [])

    def test_disabled_until_provisioned(self):
        self.mutate("device", "Enabled:logic = false", "Enabled:logic = true")

    def test_authoritative_entitlement(self):
        self.mutate("runtime", "Authorized := Authority.CanWield(Player)", "Authorized := true")

    def test_one_controller_lease(self):
        self.mutate("runtime", "if (Controller?):", "if (false?):")

    def test_owner_immutable(self):
        self.mutate("runtime", "Bound = Player", "Player.IsActive[]")

    def test_cooldown_gate(self):
        self.mutate("runtime", "Now >= CooldownUntil", "Now >= 0.0")

    def test_generation_increment(self):
        self.mutate("runtime", "set Generation += 1", "set Generation += 0")

    def test_no_stale_energy_spend(self):
        self.mutate("runtime", "IsCurrent(Player, Token)?", "Player.IsActive[]")

    def test_spend_resource_check(self):
        self.mutate("runtime", "Energy >= Cost", "Energy >= 0")

    def test_spend_bounded(self):
        self.mutate("runtime", "Cost <= 25", "Cost <= 999")

    def test_spend_positive(self):
        self.mutate("runtime", "Cost > 0", "Cost >= 0")

    def test_revocation_heartbeat(self):
        self.mutate("device", "Granted := Authority.CanWield(Player)", "Granted := true")

    def test_character_swap_fail_closed(self):
        self.mutate("device", "Character = OriginalCharacter", "Player.IsActive[]")

    def test_no_broadcast_camera(self):
        self.device += "\n    Bad():void=\n        ArmorCamera.AddToAll()\n"
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_native_after_admission(self):
        self.mutate("device", "ArmorGlow.Pickup(Player)", "ArmorGlow.Pickup(Player)\n                ArmorGlow.Pickup(Player)")

    def test_cleanup_camera(self):
        self.mutate("device", "ArmorCamera.RemoveFrom(Owner)", "ArmorCamera.AddTo(Owner)")

    def test_cleanup_aura(self):
        self.mutate("device", "ArmorGlow.Clear(Owner)", "ArmorGlow.Pickup(Owner)")

    def test_owner_must_initiate_separation(self):
        self.mutate("device", "Owner = Player", "Player.IsActive[]")

    def test_unauthorized_titan_is_rejected(self):
        self.policy["titan_possession_implemented"] = True
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_no_unverified_native_claim(self):
        self.policy["engine_verification"]["compile"] = "passed"
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))

    def test_no_public_unlock(self):
        self.policy["ordinary_unlockable"] = True
        self.assertTrue(guard.check_sources(self.runtime, self.device, self.policy))


if __name__ == "__main__":
    unittest.main()
