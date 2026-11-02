"""Source mutation tests plus an independent deterministic Titan proxy policy model.

The Python model is not Verse execution, UEFN compilation, NPC simulation,
network replication or proof that navigation succeeds in a Fortnite session.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_titan_proxy", ROOT / "tools/validate_titan_proxy.py"
)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class ProxyModel:
    """A deliberately small adversarial reference model of the source policy."""
    def __init__(self):
        self.lease = None
        self.owner = None
        self.generation = 0
        self.epoch = 0
        self.active = False
        self.npc = None
        self.sequence = 0
        self.next_move = 0.0
        self.next_cue = 0.0
        self.energy = 100

    def acquire(self, device):
        if self.lease is not None:
            return False
        self.lease = device
        return True

    def begin(self, device, player, token, *, authorized=True, character_unchanged=True):
        if (self.lease != device or self.active or not authorized
                or not character_unchanged or token <= 0):
            return False
        self.owner = player
        self.generation = token
        self.epoch += 1
        self.active = True
        self.npc = None
        self.sequence = 0
        self.next_move = 0
        self.next_cue = 0
        return True

    def bind(self, npc, *, valid=True):
        if not self.active or self.npc is not None or not valid:
            return False
        self.npc = npc
        return True

    def move(self, player, now, distance_cm):
        if (not self.active or self.owner != player or self.npc is None
                or distance_cm > 1600 or now < self.next_move):
            return False
        self.sequence += 1
        self.next_move = now + 0.5
        return True

    def cue(self, player, now):
        if (not self.active or self.owner != player or self.npc is None
                or now < self.next_cue or self.energy < 5):
            return False
        self.energy -= 5
        self.next_cue = now + 2
        return True

    def stop(self, device):
        if self.lease != device:
            return False
        self.active = False
        self.npc = None
        self.owner = None
        self.generation = 0
        self.epoch += 1
        return True


class TitanProxySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(audit.CONTRACT.read_text(encoding="utf-8"))
        cls.runtime = audit.RUNTIME.read_text(encoding="utf-8")
        cls.behavior = audit.BEHAVIOR.read_text(encoding="utf-8")
        cls.device = audit.DEVICE.read_text(encoding="utf-8")
        cls.fusion = audit.FUSION.read_text(encoding="utf-8")

    def errors(self, **changes):
        values = {
            "c": self.contract, "runtime": self.runtime,
            "behavior": self.behavior, "device": self.device,
            "fusion": self.fusion
        }
        values.update(changes)
        return audit.validate(**values)

    def test_authored_contract(self):
        self.assertEqual(self.errors(), [])

    def test_native_evidence_forgery_rejected(self):
        c = copy.deepcopy(self.contract)
        c["native_evidence"]["uefn_compile"] = "passed"
        self.assertTrue(self.errors(c=c))

    def test_fake_npc_possession_rejected(self):
        c = copy.deepcopy(self.contract)
        c["camera"]["npc_possession"] = True
        self.assertTrue(self.errors(c=c))

    def test_missing_owner_binding_rejected(self):
        runtime = self.runtime.replace("CurrentOwner = Player", "true?")
        self.assertTrue(self.errors(runtime=runtime))

    def test_canonical_state_bypass_rejected(self):
        runtime = self.runtime.replace(
            "State.IsAuthorizedActive(Controller, CurrentOwner, Generation)", "true?"
        )
        self.assertTrue(self.errors(runtime=runtime))

    def test_generation_bypass_rejected(self):
        runtime = self.runtime.replace("Controller.Token = Token", "true?")
        self.assertTrue(self.errors(runtime=runtime))

    def test_late_spawn_filter_rejected(self):
        runtime = self.runtime.replace("not OwnedNpc?", "true?")
        self.assertTrue(self.errors(runtime=runtime))

    def test_player_npc_rejected(self):
        runtime = self.runtime.replace("not player[Agent]", "true?")
        self.assertTrue(self.errors(runtime=runtime))

    def test_unbounded_move_rejected(self):
        runtime = self.runtime.replace("Range <= 1600.0", "Range >= 0.0")
        self.assertTrue(self.errors(runtime=runtime))

    def test_no_energy_charge_rejected(self):
        runtime = self.runtime.replace(
            "Budget.Spend[Controller, Player, Generation, State, 5]", "true?"
        )
        self.assertTrue(self.errors(runtime=runtime))

    def test_untagged_spawner_association_rejected(self):
        device = self.device.replace(
            "Spawned := TitanSpawner.SpawnAt(Position, false)",
            "SpawnedEvent.Subscribe(OnSpawned)"
        )
        self.assertTrue(self.errors(device=device))

    def test_serial_spawn_guard_rejected(self):
        runtime = self.runtime.replace("not SpawnInFlight?", "true?")
        self.assertTrue(self.errors(runtime=runtime))

    def test_global_output_rejected(self):
        device = self.device.replace("AttackCueOutput.Trigger(Player)", "AttackCueOutput.Trigger()")
        self.assertTrue(self.errors(device=device))

    def test_missing_teardown_rejected(self):
        device = self.device.replace("TitanSpawner.DespawnAll(false)", "Print(\"not cleaned\")")
        self.assertTrue(self.errors(device=device))

    def test_cannot_add_second_player_profile(self):
        runtime = self.runtime + "\nvar Faux:weak_map(player, int) = map{}\n"
        self.assertTrue(self.errors(runtime=runtime))

    def test_cannot_add_damage_in_npc_behavior(self):
        behavior = self.behavior + "\n# bad: .Damage(50)\n"
        self.assertTrue(self.errors(behavior=behavior))

    def test_extra_navigation_owner_rejected(self):
        behavior = self.behavior.replace(
            "Navigation.StopNavigation()", "Navigation.NavigateTo(FakeTarget)\nNavigation.StopNavigation()"
        )
        self.assertTrue(self.errors(behavior=behavior))

    def test_unauthorized_f002_activation_rejected(self):
        fusion = self.fusion.replace('RequestedFormId <> "FUS-001"', "false?")
        self.assertTrue(self.errors(fusion=fusion))

    def test_enable_by_default_rejected(self):
        device = self.device.replace("Enabled:logic = false", "Enabled:logic = true")
        self.assertTrue(self.errors(device=device))

    def test_serialized_spawn_contract_rejected(self):
        c = copy.deepcopy(self.contract)
        c["lifecycle"]["spawn_association"] = "untagged_spawn_event"
        self.assertTrue(self.errors(c=c))

    def test_shared_spawner_assertion_rejected(self):
        c = copy.deepcopy(self.contract)
        c["safety"]["no_shared_npc_spawner"] = False
        self.assertTrue(self.errors(c=c))

    def test_unsupported_dynamic_camera_rejected(self):
        c = copy.deepcopy(self.contract)
        c["camera"]["proxy_follow_camera"] = "native_verified"
        self.assertTrue(self.errors(c=c))


class TitanProxyPolicyModelTests(unittest.TestCase):
    def setUp(self):
        self.p = ProxyModel()
        self.assertTrue(self.p.acquire("proxy-A"))

    def test_single_session_lease(self):
        self.assertFalse(self.p.acquire("proxy-B"))

    def test_only_verified_owner_begins(self):
        self.assertFalse(self.p.begin("proxy-B", "owner", 5))
        self.assertFalse(self.p.begin("proxy-A", "owner", 5, authorized=False))
        self.assertFalse(self.p.begin("proxy-A", "owner", 5, character_unchanged=False))
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))

    def test_duplicate_npc_rejected(self):
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))
        self.assertTrue(self.p.bind("npc-1"))
        self.assertFalse(self.p.bind("npc-2"))

    def test_move_stays_bounded_and_owner_scoped(self):
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))
        self.assertTrue(self.p.bind("npc"))
        self.assertFalse(self.p.move("intruder", 1.0, 100))
        self.assertFalse(self.p.move("owner", 1.0, 1601))
        self.assertTrue(self.p.move("owner", 1.0, 500))
        self.assertFalse(self.p.move("owner", 1.2, 500))
        self.assertTrue(self.p.move("owner", 1.5, 500))
        self.assertEqual(self.p.sequence, 2)

    def test_attack_cue_spends_and_cools_down(self):
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))
        self.assertTrue(self.p.bind("npc"))
        self.assertFalse(self.p.cue("intruder", 1.0))
        self.assertTrue(self.p.cue("owner", 1.0))
        self.assertEqual(self.p.energy, 95)
        self.assertFalse(self.p.cue("owner", 2.0))
        self.assertTrue(self.p.cue("owner", 3.0))
        self.assertEqual(self.p.energy, 90)

    def test_epoch_invalidated_before_new_session(self):
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))
        prior_epoch = self.p.epoch
        self.assertTrue(self.p.bind("npc"))
        self.assertTrue(self.p.stop("proxy-A"))
        self.assertFalse(self.p.active)
        self.assertFalse(self.p.move("owner", 20.0, 100))
        self.assertNotEqual(prior_epoch, self.p.epoch)
        self.assertTrue(self.p.begin("proxy-A", "owner", 7))
        self.assertNotEqual(prior_epoch, self.p.epoch)

    def test_wrong_controller_cannot_stop(self):
        self.assertTrue(self.p.begin("proxy-A", "owner", 5))
        self.assertFalse(self.p.stop("proxy-B"))
        self.assertTrue(self.p.active)


if __name__ == "__main__":
    unittest.main()
