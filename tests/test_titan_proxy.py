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

    def test_preexisting_npc_preflight_must_precede_spawn_lease(self):
        summon = self.device.split("    OnSummon(Agent:agent):void=", 1)[1].split(
            "    AwaitSpawn(ExpectedEpoch:int", 1
        )[0]
        self.assertLess(
            summon.index("TitanSpawner.GetAgents().Length <> 0"),
            summon.index("TitanSpawner.DespawnAll(false)"),
        )
        self.assertLess(
            summon.index("TitanSpawner.DespawnAll(false)"),
            summon.index("Attempt := Runtime.Begin("),
        )

    def test_preflight_after_begin_mutation_is_rejected(self):
        preflight = (
            "            if (TitanSpawner.GetAgents().Length <> 0):\n"
            "                TitanSpawner.Disable()\n"
            "                TitanSpawner.DespawnAll(false)\n"
            "                Feedback.Show(Player, TitanProxyDenied, 3.0)\n"
            "                return\n"
        )
        self.assertIn(preflight, self.device)
        late_preflight = (
            "                if (TitanSpawner.GetAgents().Length <> 0):\n"
            "                    TitanSpawner.Disable()\n"
            "                    TitanSpawner.DespawnAll(false)\n"
            "                    Feedback.Show(Player, TitanProxyDenied, 3.0)\n"
            "                    return\n"
        )
        device = self.device.replace(preflight, "", 1).replace(
            "                set Epoch = StartedEpoch",
            late_preflight + "                set Epoch = StartedEpoch",
            1,
        )
        self.assertTrue(self.errors(device=device))

    def test_current_inflight_lease_is_required_for_single_unbound_npc(self):
        self.assertIn("SpawnPendingForCurrentEpoch()<transacts>:logic=", self.runtime)
        self.assertIn("if (Active?, SpawnInFlight?, SpawnEpoch = Epoch):", self.runtime)
        inventory = self.device.split("    UnexpectedSpawnCount(Runtime:", 1)[1].split(
            "    OnAdvance(Agent:agent):void=", 1
        )[0]
        self.assertLess(
            inventory.index("if (AllAgents.Length > 1):"),
            inventory.index("if (not Runtime.SpawnPendingForCurrentEpoch()?):")
        )

    def test_bypass_inflight_lease_mutation_rejected(self):
        runtime = self.runtime.replace(
            "if (Active?, SpawnInFlight?, SpawnEpoch = Epoch):",
            "if (Active?):",
        )
        self.assertTrue(self.errors(runtime=runtime))
        device = self.device.replace(
            "if (not Runtime.SpawnPendingForCurrentEpoch()?):",
            "if (false?):",
        )
        self.assertTrue(self.errors(device=device))

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

    def test_npc_elimination_must_match_owned_agent(self):
        device = self.device.replace("Runtime.IsOwnedNpc(Target)?", "true?")
        self.assertTrue(self.errors(device=device))

    def test_npc_elimination_subscription_required(self):
        device = self.device.replace(
            "TitanSpawner.EliminatedEvent.Subscribe(OnNpcEliminated),", ""
        )
        self.assertTrue(self.errors(device=device))

    def test_owner_commands_require_native_behavior_ack(self):
        runtime = self.runtime.replace(
            "NpcChar.IsActive[]\n            BehaviorReady?",
            "NpcChar.IsActive[]"
        )
        self.assertTrue(self.errors(runtime=runtime))
        runtime = self.runtime.replace(
            "Monster.IsActive[]\n            BehaviorReady?",
            "Monster.IsActive[]"
        )
        self.assertTrue(self.errors(runtime=runtime))

    def test_npc_behavior_must_emit_ack(self):
        behavior = self.behavior.replace(
            "Service.AcknowledgeBehavior(Agent)?",
            "Service.BoundNpc(Agent)?"
        )
        self.assertTrue(self.errors(behavior=behavior))

    def test_early_ready_feedback_rejected(self):
        device = self.device.replace(
            "Runtime.IsBehaviorReady(SpawnedAgent)?",
            "true?"
        )
        self.assertTrue(self.errors(device=device))

    def test_auto_spawn_detection_required(self):
        device = self.device.replace("UnexpectedSpawnCount(Runtime)?", "false?")
        self.assertTrue(self.errors(device=device))

    def test_spawn_count_match_required(self):
        device = self.device.replace("OnlyAgent = SpawnedAgent", "true?")
        self.assertTrue(self.errors(device=device))

    def test_no_preowner_cleanup_leak(self):
        device = self.device.replace(
            "if (Runtime := Service?, Runtime.Owns(Self)?):\n            Stopped := Runtime.End(Self)",
            "if (ProxyOwner?, Runtime := Service?, Runtime.Owns(Self)?):\n            Stopped := Runtime.End(Self)"
        )
        self.assertTrue(self.errors(device=device))

    def test_forged_behavior_ready_contract_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["movement"]["command_requires_behavior_ready"] = False
        self.assertTrue(self.errors(c=contract))

    def test_inflight_inventory_policy_cannot_claim_npc_is_trusted(self):
        contract = copy.deepcopy(self.contract)
        contract["lifecycle"]["inflight_inventory"] = "spawned_agent_is_trusted_while_loading"
        self.assertTrue(self.errors(c=contract))

    def test_forged_spawn_inventory_contract_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["lifecycle"]["unexpected_spawns"] = "ignore_auto_spawn"
        self.assertTrue(self.errors(c=contract))

    def test_unauthorized_summon_input_registration_rejected(self):
        device = self.device.replace(
            "State.IsAuthorizedActive(AvatarController, Owner, AvatarController.Token)",
            "true?"
        )
        self.assertTrue(self.errors(device=device))

    def test_nonregistered_summoner_rejected(self):
        device = self.device.replace("Registered = Player", "true?")
        self.assertTrue(self.errors(device=device))

    def test_unregistered_summon_input_rejected(self):
        device = self.device.replace("SummonInput.Register(Current)", "Print(\"missing summon registration\")")
        self.assertTrue(self.errors(device=device))

    def test_missing_unregister_on_owner_change_rejected(self):
        device = self.device.replace("SummonInput.Unregister(Previous)", "Print(\"not unregistered\")")
        self.assertTrue(self.errors(device=device))

    def test_commands_cannot_register_all_players(self):
        device = self.device + "\n# unsafe code: AdvanceInput.RegisterAll()\n"
        self.assertTrue(self.errors(device=device))

    def test_missing_command_registration_rejected(self):
        device = self.device.replace("AdvanceInput.Register(Owner)", "Print(\"no movement input\")")
        self.assertTrue(self.errors(device=device))

    def test_missing_command_unregister_rejected(self):
        device = self.device.replace("DismissInput.Unregister(Registered)", "Print(\"leaked dismiss\")")
        self.assertTrue(self.errors(device=device))

    def test_missing_terminal_command_cleanup_rejected(self):
        device = self.device.replace(
            "    FinishProxy():void=\n        # Remove input eligibility even when native actor cleanup fails.\n        ClearCommandInputs()",
            "    FinishProxy():void=\n        # cleanup omitted"
        )
        self.assertTrue(self.errors(device=device))

    def test_editor_registered_requirement_must_be_explicit(self):
        c = copy.deepcopy(self.contract)
        c["native_binding"]["input_registered_behavior"] = "Ignore Registered"
        self.assertTrue(self.errors(c=c))

    def test_global_registration_contract_rejected(self):
        c = copy.deepcopy(self.contract)
        c["safety"]["no_global_input_registration"] = False
        self.assertTrue(self.errors(c=c))

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

    def test_camera_only_opt_in_with_exact_npc_acknowledgement(self):
        self.assertIn("ExperimentalCameraEnabled:logic = false", self.device)
        camera = self.device.split(
            "    StartProxyCamera(ExpectedEpoch:int, Npc:agent):void=", 1
        )[1].split("    # Observes every native spawner agent", 1)[0]
        for fragment in (
            "ExperimentalCameraEnabled?",
            "Runtime.IsCurrentEpoch(ExpectedEpoch)?",
            "Runtime.IsBehaviorReady(Npc)?",
            "Owner := ProxyOwner?",
            "ProxyCamera.AddTo(Owner)",
            "CurrentCameraOwner = Owner",
            "Runtime.IsBehaviorReady(Npc)?",
            "if (not ProxyCamera.TeleportTo[Position, Rotation]):",
            "ProxyCamera.RemoveFrom(Owner)",
        ):
            self.assertIn(fragment, camera)

    def test_initial_camera_position_failure_cannot_push_stack(self):
        camera = self.device.split(
            "    StartProxyCamera(ExpectedEpoch:int, Npc:agent):void=", 1
        )[1].split("    TrackProxyCamera(ExpectedEpoch:int", 1)[0]
        self.assertLess(
            camera.index("if (ProxyCamera.TeleportTo[Position, Rotation]):"),
            camera.index("ProxyCamera.AddTo(Owner)")
        )
        device = self.device.replace(
            "if (ProxyCamera.TeleportTo[Position, Rotation]):",
            "if (true?):", 1
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_enabled_by_default_rejected(self):
        device = self.device.replace(
            "ExperimentalCameraEnabled:logic = false",
            "ExperimentalCameraEnabled:logic = true",
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_global_stack_mutation_rejected(self):
        device = self.device.replace("ProxyCamera.AddTo(Owner)", "ProxyCamera.AddToAll()")
        self.assertTrue(self.errors(device=device))
        device = self.device.replace(
            "ProxyCamera.RemoveFrom(Owner)", "ProxyCamera.RemoveFromAll()"
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_late_ack_bypass_rejected(self):
        device = self.device.replace(
            "Runtime.IsBehaviorReady(Npc)?", "true?"
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_epoch_and_owner_bypass_rejected(self):
        device = self.device.replace(
            "Runtime.IsCurrentEpoch(ExpectedEpoch)?", "true?"
        )
        self.assertTrue(self.errors(device=device))
        device = self.device.replace(
            "CurrentCameraOwner = Owner", "true?"
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_stack_must_pop_on_teardown(self):
        device = self.device.replace("ProxyCamera.RemoveFrom(Owner)", "Print(\"leak\")")
        self.assertTrue(self.errors(device=device))
        device = self.device.replace(
            "        ClearCommandInputs()\n        ReleaseProxyCamera()\n        # Invalidate all mailbox",
            "        ClearCommandInputs()\n        # Invalidate all mailbox",
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_physical_binding_is_conditional(self):
        device = self.device.replace(
            "        if (ExperimentalCameraEnabled?):\n"
            "            set Devices = AddPhysicalDevice[Devices, ProxyCamera]",
            "        set Devices = AddPhysicalDevice[Devices, ProxyCamera]",
        )
        self.assertTrue(self.errors(device=device))

    def test_camera_native_evidence_unverified(self):
        c = copy.deepcopy(self.contract)
        c["camera"]["native_test"] = "passed"
        self.assertTrue(self.errors(c=c))
        c = copy.deepcopy(self.contract)
        c["camera"]["npc_possession"] = True
        self.assertTrue(self.errors(c=c))


    def test_command_hud_is_hidden_until_exact_behavior_ack(self):
        summon = self.device.split("    OnSummon(Agent:agent):void=", 1)[1].split(
            "    AwaitSpawn(ExpectedEpoch:int", 1
        )[0]
        ready = self.device.split(
            "    AwaitBehaviorReady(ExpectedEpoch:int, SpawnedAgent:agent)", 1
        )[1].split("    # An optional fixed-point camera", 1)[0]
        self.assertNotIn("ActivateCommandInputs(", summon)
        self.assertLess(ready.index("Runtime.IsBehaviorReady(SpawnedAgent)?"),
                        ready.index("ActivateCommandInputs(Owner)"))
        self.assertLess(ready.index("Runtime.IsAuthorized()?"),
                        ready.index("ActivateCommandInputs(Owner)"))
        mutation = self.device.replace(
            "                        ActivateCommandInputs(Owner)",
            "                        Print(\"no command registration\")", 1
        )
        self.assertTrue(self.errors(device=mutation))

    def test_early_command_hud_registration_rejected(self):
        mutation = self.device.replace(
            "                RefreshSummonRegistration()\n                set WaypointIndex = 0",
            "                ActivateCommandInputs(Player)\n                set WaypointIndex = 0",
            1
        )
        self.assertTrue(self.errors(device=mutation))

    def test_acknowledgement_cannot_bypass_owner_recheck(self):
        mutation = self.device.replace(
            "Owner := ProxyOwner?, Owner.IsActive[], Runtime.IsAuthorized()?",
            "Owner := ProxyOwner?", 1
        )
        self.assertTrue(self.errors(device=mutation))

    def test_summon_action_hidden_while_proxy_pending(self):
        eligible = self.device.split(
            "    EligibleSummoner()<transacts>:?player=", 1
        )[1].split("    RefreshSummonRegistration():void=", 1)[0]
        self.assertIn("not ProxyOwner?", eligible)
        mutation = self.device.replace(
            "    EligibleSummoner()<transacts>:?player=\n        if:\n            not ProxyOwner?",
            "    EligibleSummoner()<transacts>:?player=\n        if:", 1
        )
        self.assertTrue(self.errors(device=mutation))

    def test_command_ui_contract_cannot_claim_early_access(self):
        c = copy.deepcopy(self.contract)
        c["safety"]["command_input_requires_behavior_ack"] = False
        self.assertTrue(self.errors(c=c))
        c = copy.deepcopy(self.contract)
        c["lifecycle"]["input_registration"] = "register_during_spawn"
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



class TitanSpawnHandshakeModel:
    """Independent scheduler-adversarial model of the bounded spawn handshake."""

    def __init__(self):
        self.epoch = 0
        self.active = False
        self.in_flight = False
        self.spawn_epoch = 0
        self.bound_npc = None
        self.behavior_ready = False
        self.npcs = []

    def begin(self):
        if self.active or self.in_flight or self.npcs:
            return None
        self.epoch += 1
        self.spawn_epoch = self.epoch
        self.in_flight = True
        self.active = True
        self.bound_npc = None
        self.behavior_ready = False
        return self.epoch

    def return_spawn(self, epoch, agent):
        if not self.in_flight or self.spawn_epoch != epoch:
            return False
        self.in_flight = False
        self.spawn_epoch = 0
        if not self.active or self.epoch != epoch or agent is None:
            return False
        if len(self.npcs) != 1 or self.npcs[0] != agent:
            return False
        self.bound_npc = agent
        return True

    def acknowledge(self, agent):
        if self.active and self.bound_npc == agent and agent in self.npcs:
            self.behavior_ready = True
            return True
        return False

    def can_command(self, agent):
        return (
            self.active and self.behavior_ready and self.bound_npc == agent
            and len(self.npcs) == 1 and self.npcs[0] == agent
        )

    def unexpected_agents(self):
        if len(self.npcs) > 1:
            return True
        if self.bound_npc is None:
            # One visible agent while SpawnAt suspends is not yet bound,
            # but cannot move or cue; it must be reconciled on return.
            return bool(self.npcs) and not self.in_flight
        return self.npcs != [self.bound_npc]

    def stop(self):
        self.active = False
        self.behavior_ready = False
        self.bound_npc = None
        self.npcs = []
        self.epoch += 1
        # Do NOT reset self.in_flight. The earlier SpawnAt must return.


class TitanSpawnHandshakeTests(unittest.TestCase):
    def setUp(self):
        self.p = TitanSpawnHandshakeModel()

    def test_spawnat_return_does_not_equal_navigation_ready(self):
        epoch = self.p.begin()
        self.p.npcs = ["titan"]
        self.assertTrue(self.p.return_spawn(epoch, "titan"))
        self.assertFalse(self.p.can_command("titan"))
        self.assertTrue(self.p.acknowledge("titan"))
        self.assertTrue(self.p.can_command("titan"))

    def test_visible_candidate_waits_for_suspending_spawnat_return(self):
        epoch = self.p.begin()
        self.p.npcs = ["titan"]
        self.assertFalse(self.p.unexpected_agents())
        self.assertFalse(self.p.can_command("titan"))
        self.assertTrue(self.p.return_spawn(epoch, "titan"))
        self.assertFalse(self.p.can_command("titan"))
        self.assertTrue(self.p.acknowledge("titan"))
        self.assertTrue(self.p.can_command("titan"))

    def test_wrong_single_candidate_rejected_on_return(self):
        epoch = self.p.begin()
        self.p.npcs = ["auto"]
        self.assertFalse(self.p.unexpected_agents())
        self.assertFalse(self.p.return_spawn(epoch, "titan"))
        self.assertTrue(self.p.unexpected_agents())
        self.assertFalse(self.p.acknowledge("auto"))
        self.assertFalse(self.p.can_command("auto"))

    def test_single_pending_candidate_timeout_cleans_before_late_return(self):
        epoch = self.p.begin()
        self.p.npcs = ["auto"]
        self.assertFalse(self.p.unexpected_agents())
        self.p.stop()
        self.assertTrue(self.p.in_flight)
        self.assertEqual(self.p.npcs, [])
        self.assertIsNone(self.p.begin())
        self.assertFalse(self.p.return_spawn(epoch, "auto"))
        self.assertIsNotNone(self.p.begin())

    def test_unsolicited_autospawn_fails_closed(self):
        epoch = self.p.begin()
        self.p.npcs = ["auto", "titan"]
        self.assertTrue(self.p.unexpected_agents())
        self.assertFalse(self.p.return_spawn(epoch, "titan"))
        self.assertFalse(self.p.can_command("titan"))

    def test_wrong_agent_return_fails_closed(self):
        epoch = self.p.begin()
        self.p.npcs = ["auto"]
        self.assertFalse(self.p.return_spawn(epoch, "titan"))
        self.assertFalse(self.p.acknowledge("auto"))

    def test_late_return_never_authorizes_new_generation(self):
        old = self.p.begin()
        self.p.stop()
        self.assertTrue(self.p.in_flight)
        self.assertIsNone(self.p.begin())
        self.assertFalse(self.p.return_spawn(old, "stale"))
        latest = self.p.begin()
        self.assertNotEqual(old, latest)
        self.p.npcs = ["current"]
        self.assertTrue(self.p.return_spawn(latest, "current"))
        self.assertFalse(self.p.acknowledge("stale"))
        self.assertTrue(self.p.acknowledge("current"))

    def test_behavior_timeout_invalidates_all_commands(self):
        epoch = self.p.begin()
        self.p.npcs = ["titan"]
        self.assertTrue(self.p.return_spawn(epoch, "titan"))
        self.p.stop()
        self.assertFalse(self.p.acknowledge("titan"))
        self.assertFalse(self.p.can_command("titan"))

    def test_dead_npc_is_not_a_command_target(self):
        epoch = self.p.begin()
        self.p.npcs = ["titan"]
        self.assertTrue(self.p.return_spawn(epoch, "titan"))
        self.assertTrue(self.p.acknowledge("titan"))
        self.p.npcs = []
        self.assertTrue(self.p.unexpected_agents())
        self.assertFalse(self.p.can_command("titan"))

    def test_extra_npc_after_ready_invalidates_inventory(self):
        epoch = self.p.begin()
        self.p.npcs = ["titan"]
        self.assertTrue(self.p.return_spawn(epoch, "titan"))
        self.assertTrue(self.p.acknowledge("titan"))
        self.p.npcs.append("ambient")
        self.assertTrue(self.p.unexpected_agents())
        self.assertFalse(self.p.can_command("titan"))

    def test_preexisting_agent_rejected_without_stranding_spawn_lease(self):
        # Preflight happens before Begin; no SpawnAt exists to complete a
        # lease if the dedicated spawner was already populated.
        self.p.npcs = ["ambient"]
        self.assertIsNone(self.p.begin())
        self.assertFalse(self.p.in_flight)
        self.p.npcs = []  # dedicated spawner cleanup
        epoch = self.p.begin()
        self.assertIsNotNone(epoch)
        self.p.npcs = ["titan"]
        self.assertTrue(self.p.return_spawn(epoch, "titan"))

    def test_preowner_failure_still_cleans_dedicated_spawner(self):
        epoch = self.p.begin()
        self.p.npcs = ["ambient", "duplicate"]
        self.assertTrue(self.p.unexpected_agents())
        self.p.stop()
        self.assertEqual(self.p.npcs, [])
        self.assertFalse(self.p.can_command("ambient"))


class OwnerInputRegistrationModel:
    """Adversarial source-policy model, NOT native Input Trigger execution.

    A pending NPC cannot grant the owner command HUD. Only exact behavior
    acknowledgement for the current authorized owner activates those inputs.
    """

    def __init__(self):
        self.authorized_owner = None
        self.summoner = None
        self.pending_owner = None
        self.commands = None
        self.proxy_active = False

    def reconcile(self, candidate, authorized):
        self.authorized_owner = candidate if authorized else None
        if self.proxy_active and self.pending_owner != self.authorized_owner:
            self.dismiss()
        self.summoner = self.authorized_owner if not self.proxy_active else None

    def summon(self, actor):
        if (self.proxy_active or actor is None or actor != self.summoner
                or actor != self.authorized_owner):
            return False
        self.proxy_active = True
        self.pending_owner = actor
        self.summoner = None
        self.commands = None
        return True

    def acknowledge(self, actor, *, exact_npc=True, generation_valid=True):
        if (not self.proxy_active or actor != self.pending_owner
                or actor != self.authorized_owner or not exact_npc
                or not generation_valid):
            return False
        self.commands = actor
        return True

    def command(self, actor):
        return (
            self.proxy_active and actor == self.commands
            and actor == self.pending_owner and actor == self.authorized_owner
        )

    def dismiss(self):
        self.commands = None
        self.pending_owner = None
        self.proxy_active = False
        self.summoner = self.authorized_owner

    def disconnect(self, actor):
        if actor == self.authorized_owner:
            self.authorized_owner = None
        if actor == self.pending_owner:
            self.dismiss()
        self.summoner = self.authorized_owner if not self.proxy_active else None


class OwnerInputRegistrationModelTests(unittest.TestCase):
    def setUp(self):
        self.m = OwnerInputRegistrationModel()

    def test_nonowner_never_receives_summon_or_command(self):
        self.m.reconcile("creator", True)
        self.assertFalse(self.m.summon("intruder"))
        self.assertTrue(self.m.summon("creator"))
        self.assertFalse(self.m.command("creator"))
        self.assertFalse(self.m.acknowledge("intruder"))
        self.assertTrue(self.m.acknowledge("creator"))
        self.assertFalse(self.m.command("intruder"))
        self.assertTrue(self.m.command("creator"))

    def test_pending_spawn_never_exposes_command_or_repeat_summon(self):
        self.m.reconcile("creator", True)
        self.assertTrue(self.m.summon("creator"))
        self.assertIsNone(self.m.summoner)
        self.assertIsNone(self.m.commands)
        self.assertFalse(self.m.command("creator"))
        self.assertFalse(self.m.summon("creator"))
        self.assertFalse(self.m.acknowledge("creator", exact_npc=False))
        self.assertFalse(self.m.acknowledge("creator", generation_valid=False))
        self.assertFalse(self.m.command("creator"))

    def test_revoked_authority_retracts_actions(self):
        self.m.reconcile("creator", True)
        self.assertTrue(self.m.summon("creator"))
        self.assertTrue(self.m.acknowledge("creator"))
        self.m.reconcile("creator", False)
        self.assertFalse(self.m.command("creator"))
        self.assertFalse(self.m.summon("creator"))
        self.assertIsNone(self.m.commands)

    def test_disconnect_unregistered_and_cleans_commands(self):
        self.m.reconcile("creator", True)
        self.assertTrue(self.m.summon("creator"))
        self.assertTrue(self.m.acknowledge("creator"))
        self.m.disconnect("creator")
        self.assertIsNone(self.m.summoner)
        self.assertIsNone(self.m.commands)
        self.assertFalse(self.m.command("creator"))

    def test_new_authorized_player_cannot_inherit_old_proxy(self):
        self.m.reconcile("owner-A", True)
        self.assertTrue(self.m.summon("owner-A"))
        self.assertTrue(self.m.acknowledge("owner-A"))
        self.m.reconcile("owner-B", True)
        self.assertFalse(self.m.command("owner-B"))
        self.assertFalse(self.m.command("owner-A"))
        self.assertTrue(self.m.summon("owner-B"))
        self.assertFalse(self.m.command("owner-B"))
        self.assertTrue(self.m.acknowledge("owner-B"))
        self.assertTrue(self.m.command("owner-B"))

    def test_dismiss_restores_only_current_summon_eligibility(self):
        self.m.reconcile("creator", True)
        self.assertTrue(self.m.summon("creator"))
        self.assertTrue(self.m.acknowledge("creator"))
        self.m.dismiss()
        self.assertFalse(self.m.command("creator"))
        self.assertEqual(self.m.summoner, "creator")
        self.assertTrue(self.m.summon("creator"))
        self.assertFalse(self.m.command("creator"))


class TitanCameraStackReferenceModel:
    """Stack ownership policy only; never models actual UEFN camera behavior."""

    def __init__(self, *, enabled=False):
        self.enabled = enabled
        self.camera_owner = None
        self.active_epoch = 0

    def start(self, *, owner, epoch, active, ready):
        if (not self.enabled or not active or not ready or owner is None
                or self.camera_owner is not None or epoch != self.active_epoch):
            return False
        self.camera_owner = owner
        return True

    def frame(self, *, owner, epoch, active, ready, teleport_ok=True):
        if (owner != self.camera_owner or not active or not ready
                or epoch != self.active_epoch):
            return False
        if not teleport_ok:
            self.release()
            return False
        return True

    def release(self):
        self.camera_owner = None

    def restart(self):
        self.release()
        self.active_epoch += 1


class TitanCameraStackPolicyTests(unittest.TestCase):
    def setUp(self):
        self.cam = TitanCameraStackReferenceModel()

    def test_disabled_by_default_and_no_implicit_stack(self):
        self.assertFalse(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.assertIsNone(self.cam.camera_owner)

    def test_camera_only_after_native_ack_and_owner(self):
        self.cam.enabled = True
        self.assertFalse(self.cam.start(owner="creator", epoch=0, active=True, ready=False))
        self.assertFalse(self.cam.start(owner=None, epoch=0, active=True, ready=True))
        self.assertTrue(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.assertFalse(self.cam.frame(owner="other", epoch=0, active=True, ready=True))
        self.assertTrue(self.cam.frame(owner="creator", epoch=0, active=True, ready=True))

    def test_failed_teleport_releases_stack_without_grant(self):
        self.cam.enabled = True
        self.assertTrue(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.assertFalse(self.cam.frame(
            owner="creator", epoch=0, active=True, ready=True, teleport_ok=False
        ))
        self.assertIsNone(self.cam.camera_owner)

    def test_stale_epoch_after_revocation_cannot_track(self):
        self.cam.enabled = True
        self.assertTrue(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.cam.restart()
        self.assertFalse(self.cam.frame(owner="creator", epoch=0, active=True, ready=True))
        self.assertFalse(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.assertTrue(self.cam.start(owner="creator", epoch=1, active=True, ready=True))

    def test_two_players_cannot_share_a_viewpoint_lease(self):
        self.cam.enabled = True
        self.assertTrue(self.cam.start(owner="creator", epoch=0, active=True, ready=True))
        self.assertFalse(self.cam.start(owner="intruder", epoch=0, active=True, ready=True))
        self.cam.release()
        self.assertTrue(self.cam.start(owner="intruder", epoch=0, active=True, ready=True))


if __name__ == "__main__":
    unittest.main()
