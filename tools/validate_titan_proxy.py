#!/usr/bin/env python3
"""Static, source-pinned Titan proxy research audit. NOT native Verse execution."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "content/sovereign/titan_proxy_experiment.json"
RUNTIME = ROOT / "verse/sovereign/titan_proxy_command_runtime.verse"
BEHAVIOR = ROOT / "verse/sovereign/titan_proxy_behavior.verse"
DEVICE = ROOT / "verse/sovereign/titan_proxy_device.verse"
FUSION = ROOT / "verse/sovereign/fusion_state_runtime.verse"

RUNTIME_GUARDS = (
    "weak_map(session, aeonfall_titan_proxy_command_runtime)",
    "not Active?",
    "Token > 0",
    "Controller.Token = Token",
    "Controller.VisualOwner?",
    "CurrentOwner = Player",
    "Controller.VisualCharacter?",
    "State.IsAuthorizedActive(Controller, Player, Token)",
    "State.IsAuthorizedActive(Controller, CurrentOwner, Generation)",
    "IsAuthorized()?",
    "not OwnedNpc?",
    "BehaviorReady:logic = false",
    "set BehaviorReady = false",
    "AcknowledgeBehavior(Agent:agent)",
    "IsBehaviorReady(Agent:agent)",
    "NpcChar.IsActive[]\n            BehaviorReady?",
    "Monster.IsActive[]\n            BehaviorReady?",
    "not SpawnInFlight?",
    "set SpawnEpoch = Epoch",
    "SpawnEpoch <> ExpectedEpoch",
    "set SpawnInFlight = false",
    "IsOwnedNpc(Agent:agent)",
    "Current = Agent",
    "CompleteSpawn(ExpectedEpoch:int, Spawned:?agent)",
    "not player[Agent]",
    "Agent.GetFortCharacter[]",
    "Controller.Running?",
    "CurrentOwner.GetFortCharacter[]",
    "Current = Character",
    "Spawned = Agent",
    "Range <= 1600.0",
    "Now >= NextMoveAt",
    "set NextMoveAt = Now + 0.5",
    "Command.Sequence > SeenSequence",
    "Budget.Spend[Controller, Player, Generation, State, 5]",
    "set NextCueAt = Now + 2.0",
    "set Active = false",
    "set Pending = false",
    "set Epoch += 1",
    "set Lease = false",
)
BEHAVIOR_GUARDS = (
    "class(npc_behavior)",
    "GetAgent[]",
    "Character.GetNavigatable[]",
    "Service.AcknowledgeBehavior(Agent)?",
    "Service.GetNewMove[Agent, SeenSequence]",
    "MakeNavigationTarget(Command.Destination)",
    "Navigation.NavigateTo(",
    "?AllowPartialPath := false",
    "Sleep(2.0)",
    "Navigation.StopNavigation()",
    "StartupChecks >= 40",
    "OnEnd<override>()",
)
DEVICE_GUARDS = (
    "Enabled:logic = false",
    "TitanSpawner:npc_spawner_device",
    "Waypoints:[]creative_prop",
    "GetAEONFALLTitanProxyCommands()",
    "Runtime.Acquire(Self)",
    "SummonInput.PressedEvent.Subscribe(OnSummon)",
    "AdvanceInput.PressedEvent.Subscribe(OnAdvance)",
    "AttackCueInput.PressedEvent.Subscribe(OnAttackCue)",
    "DismissInput.PressedEvent.Subscribe(OnDismiss)",
    "TitanSpawner.EliminatedEvent.Subscribe(OnNpcEliminated)",
    "Result.Target?",
    "Runtime.IsOwnedNpc(Target)?",
    "SpawnProxy(StartedEpoch)",
    "TitanSpawner.SpawnAt(Position, false)",
    "Runtime.CompleteSpawn(ExpectedEpoch, Spawned)?",
    "TitanSpawner.GetAgents()",
    "OnlyAgent = SpawnedAgent",
    "AwaitBehaviorReady(ExpectedEpoch, SpawnedAgent)",
    "Runtime.IsBehaviorReady(SpawnedAgent)?",
    "Attempts >= 20",
    "UnexpectedSpawnCount(Runtime)?",
    "TitanProxyRequested",
    "SummonInput.Register(Current)",
    "SummonInput.Unregister(Previous)",
    "SummonInput.Disable()",
    "SummonInput.Enable()",
    "Registered := SummonRegistered?",
    "Registered = Player",
    "EligibleSummoner()<transacts>:?player=",
    "State.IsAuthorizedActive(AvatarController, Owner, AvatarController.Token)",
    "RefreshSummonRegistration()",
    "AdvanceInput.Register(Owner)",
    "AttackCueInput.Register(Owner)",
    "DismissInput.Register(Owner)",
    "AdvanceInput.Unregister(Registered)",
    "AttackCueInput.Unregister(Registered)",
    "DismissInput.Unregister(Registered)",
    "ClearCommandInputs()",
    "PlayerRemovedEvent().Subscribe(OnPlayerLeft)",
    "AvatarController.VisualOwner?",
    "AvatarController.VisualCharacter?",
    "Runtime.Begin(",
    "AwaitSpawn(StartedEpoch)",
    "ValidOwner[Agent]",
    "Runtime.RequestMove(Player, Destination)?",
    "Runtime.RequestAttackCue(Player)?",
    "AttackCueOutput.Trigger(Player)",
    "Runtime.IsAuthorized()?",
    "Stopped := Runtime.End(Self)",
    "TitanSpawner.Disable()",
    "TitanSpawner.DespawnAll(false)",
    "Subscription.Cancel()",
    "OnEnd<override>()",
)


def validate(c: dict, runtime: str, behavior: str, device: str, fusion: str) -> list[str]:
    errors: list[str] = []
    expected = {
        "schema_version": 1,
        "feature": "sovereign_titan_npc_proxy_experiment",
        "canonical_form": "FUS-002",
        "f002_activation": "disabled",
        "experiment_authority": "active_FUS-001_same_owner_generation",
        "activation_default": False,
        "owner_limit": 1,
        "nonpersistent": True,
        "session_runtime": "verse/sovereign/titan_proxy_command_runtime.verse",
        "npc_behavior": "verse/sovereign/titan_proxy_behavior.verse",
        "controller_device": "verse/sovereign/titan_proxy_device.verse",
        "canonical_state": "verse/sovereign/fusion_state_runtime.verse",
        "authoritative_owner": "aeonfall_fusion_state_runtime.IsAuthorizedActive",
    }
    for field, value in expected.items():
        if c.get(field) != value:
            errors.append(f"unsafe {field}: expected {value!r}")
    binding = c.get("native_binding", {})
    fields = {
        "controller_class": "aeonfall_titan_proxy_device",
        "npc_spawner_type": "npc_spawner_device",
        "character_behavior": "aeonfall_titan_proxy_behavior",
        "spawn_api": "npc_spawner_device.SpawnAt",
        "spawner_reconciliation_api": "npc_spawner_device.GetAgents",
        "input_registered_behavior": "Require Registered",
        "input_registration_api": "input_trigger_device.Register/Unregister",
        "waypoints_type": "creative_prop",
        "waypoints_min": 1,
        "waypoints_max": 8,
        "character_definition": None,
        "spawner_editor_path": None,
        "input_editor_paths": [],
        "waypoint_editor_paths": [],
    }
    for name, expected_value in fields.items():
        if binding.get(name) != expected_value:
            errors.append(f"native binding drift: {name}")
    if binding.get("input_types") != {
        "summon": "input_trigger_device",
        "advance": "input_trigger_device",
        "attack_cue": "input_trigger_device",
        "dismiss": "input_trigger_device",
    }:
        errors.append("input binding drift")
    if binding.get("outputs") != {
        "attack_cue": "trigger_device", "feedback": "hud_message_device"
    }:
        errors.append("output binding drift")
    movement = c.get("movement", {})
    for name, value in {
        "native": "navigatable.NavigateTo",
        "navigation_owner": "npc_behavior_only",
        "reach_radius_cm": 150,
        "max_navigation_seconds": 2,
        "poll_seconds": 0.15,
        "max_waypoint_distance_from_owner_cm": 1600,
        "min_command_spacing_seconds": 0.5,
        "allow_partial_path": False,
        "behavior_bootstrap_checks": 40,
        "behavior_ready_timeout_seconds": 5,
        "command_requires_behavior_ready": True,
    }.items():
        if movement.get(name) != value:
            errors.append(f"movement bound drift: {name}")
    if c.get("attack") != {
        "effect": "owner_instigated_cue_only_no_damage",
        "energy_cost": 5, "cooldown_seconds": 2,
        "direct_damage": False, "independent_hit_validation": False
    }:
        errors.append("attack capability falsely expanded")
    if c.get("camera") != {
        "player_movement": "native_fortnite_character",
        "owner_camera": "existing_FUS-001_orbit_camera",
        "proxy_follow_camera": "not_implemented",
        "npc_possession": False
    }:
        errors.append("camera/possession capability mismatch")
    for key in ("no_shared_npc_spawner", "no_second_owner_or_profile_root",
                "attack_cue_must_not_wire_damage", "f002_not_activated",
                "requires_native_compile", "requires_two_client_launch_session",
                "no_untagged_spawned_event_association",
                "no_global_input_registration"):
        if c.get("safety", {}).get(key) is not True:
            errors.append(f"safety gate disabled: {key}")
    lifecycle = c.get("lifecycle", {})
    for field, value in {
        "lease": "one_session_controller",
        "late_spawn": "reject_and_despawn",
        "npc_elimination": "exact_agent_identity_then_teardown",
        "input_registration": "verified_owner_only_dynamic_register_unregister",
        "behavior_ack": "npc_behavior_ack_required_before_commands",
        "unexpected_spawns": "fail_closed_despawn_dedicated_spawner",
        "spawn_association": "serialized_SpawnAt_return_and_epoch",
        "owner_exit": "invalidate_before_despawn",
        "generation_change": "invalidate",
        "character_replacement": "invalidate",
        "device_shutdown": "cancel_subscriptions_and_despawn",
        "player_join": "no_implicit_entitlement",
        "replication": "native_npc_simulation_unverified",
    }.items():
        if lifecycle.get(field) != value:
            errors.append(f"lifecycle mismatch: {field}")
    if c.get("native_evidence") != {
        "uefn_compile": "not_run", "npc_character_definition": "not_run",
        "npc_spawn": "not_run", "navigation": "not_run",
        "attack_cue": "not_run", "multiplayer": "not_run",
        "cleanup": "not_run", "player_possession": "unproven"
    }:
        errors.append("native evidence must remain explicitly unverified")

    for label, source, fragments in (
        ("runtime", runtime, RUNTIME_GUARDS),
        ("npc behavior", behavior, BEHAVIOR_GUARDS),
        ("device", device, DEVICE_GUARDS),
    ):
        for fragment in fragments:
            if fragment not in source:
                errors.append(f"{label} missing guard: {fragment}")
    # Never append a player persistable root or open a second form grant.
    combined = runtime + behavior + device
    if "SpawnedEvent.Subscribe" in device:
        errors.append("unversioned native SpawnedEvent association is prohibited")
    if "RegisterAll(" in device or "UnregisterAll(" in device:
        errors.append("Titan inputs may register or clear only their owner")
    # Registrations must occur after authorized session admission, and they
    # must be torn down before invalidating the NPC command authority.
    command_start = device.find("    ActivateCommandInputs(Owner:player):void=")
    command_end = device.find("    ClearCommandInputs():void=")
    if command_start < 0 or command_end <= command_start:
        errors.append("owner command input lifecycle missing")
    else:
        command_segment = device[command_start:command_end]
        for fragment in (
            "AdvanceInput.Register(Owner)", "AttackCueInput.Register(Owner)",
            "DismissInput.Register(Owner)"
        ):
            if fragment not in command_segment:
                errors.append("owner command input registration missing: " + fragment)
    teardown = device[command_end:device.find("    # Only a current and active Armor Fusion owner", command_end)]
    for fragment in (
        "AdvanceInput.Disable()", "AttackCueInput.Disable()",
        "DismissInput.Disable()", "AdvanceInput.Unregister(Registered)",
        "AttackCueInput.Unregister(Registered)",
        "DismissInput.Unregister(Registered)"
    ):
        if fragment not in teardown:
            errors.append("owner command input cleanup missing: " + fragment)
    finish_at = device.find("    FinishProxy():void=")
    terminal = device[finish_at:device.find("    OnEnd<override>():void=", finish_at)]
    if finish_at < 0 or "ClearCommandInputs()" not in terminal:
        errors.append("terminal cleanup must remove command input eligibility")
    if device.find("ActivateCommandInputs(Player)", device.find("    OnSummon(")) < device.find("Attempt := Runtime.Begin("):
        errors.append("Titan command inputs registered before authoritative begin")

    if "weak_map(player," in combined:
        errors.append("second persistent profile map prohibited")
    if 'BeginActivation(' in combined or 'ConfirmActivated(' in combined:
        errors.append("proxy must not activate FUS-002 or claim state ownership")
    if ".Damage(" in combined or ".SetHealth(" in combined:
        errors.append("proxy attack cue must never apply damage")
    if "GetPlayspace().GetPlayers()[0]" in combined:
        errors.append("first-player-as-owner is prohibited")
    if "RequestedFormId <> \"FUS-001\"" not in fusion:
        errors.append("architect FUS-002 activation guard absent")
    # The only despawn path must first invalidate the mailbox epoch.
    if device.find("Stopped := Runtime.End(Self)") > device.find("TitanSpawner.DespawnAll(false)", device.find("    FinishProxy():void=")):
        errors.append("runtime must invalidate before active NPC cleanup")
    if runtime.find("Budget.Spend[Controller, Player, Generation, State, 5]") > runtime.find("set NextCueAt = Now + 2.0"):
        errors.append("attack cue cooldown cannot precede resource charge")
    if behavior.count("Navigation.NavigateTo(") != 1:
        errors.append("single NPC navigation authority required")
    if device.find("Feedback.Show(Owner, TitanProxyReady, 3.0)") < device.find("Runtime.IsBehaviorReady(SpawnedAgent)?"):
        errors.append("Titan ready feedback must follow behavior acknowledgement")
    for required in (
        "NpcChar.IsActive[]\n            BehaviorReady?",
        "Monster.IsActive[]\n            BehaviorReady?",
    ):
        if required not in runtime:
            errors.append("Titan commands require actual acknowledged behavior")
    # Conditional cleanup based only on ProxyOwner leaks auto-spawned NPCs
    # rejected before the owner-facing session was initialized.
    finish = device[device.find("    FinishProxy():void="):device.find("    OnEnd<override>():void=")]
    if "if (ProxyOwner?" in finish:
        errors.append("Titan cleanup must also run before owner association")
    return errors


def main() -> int:
    problems = validate(
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        RUNTIME.read_text(encoding="utf-8"),
        BEHAVIOR.read_text(encoding="utf-8"),
        DEVICE.read_text(encoding="utf-8"),
        FUSION.read_text(encoding="utf-8"),
    )
    for problem in problems:
        print("ERROR:", problem)
    if not problems:
        print("Titan NPC proxy source contract OK; UEFN compile/navigation/replication NOT RUN.")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
