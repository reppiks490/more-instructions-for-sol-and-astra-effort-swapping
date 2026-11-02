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
    "BehaviorTerminated:logic = false",
    "LastBehaviorPulseAt:float = -1.0",
    "set LastBehaviorPulseAt = GetSimulationElapsedTime()",
    "set BehaviorTerminated = false",
    "set BehaviorTerminated = true",
    "if (not BehaviorTerminated?, BoundNpc(Agent)?):",
    "if (not BehaviorTerminated?, BehaviorReady?, BoundNpc(Agent)?, BehaviorPulseFresh()?):",
    "set BehaviorReady = false",
    "AcknowledgeBehavior(Agent:agent)",
    "IsBehaviorReady(Agent:agent)",
    "BoundEpochFor(Agent:agent)<decides><transacts>:int=",
    "WithdrawBehavior(Agent:agent, ExpectedEpoch:int)",
    "Epoch = ExpectedEpoch",
    "HasTerminatedBehavior()<transacts>:logic=",
    "if (Active?, BehaviorTerminated?):",
    "IsReadyForCurrentNpc()<transacts>:logic=",
    "BehaviorPulseFresh()<transacts>:logic=",
    "Now - LastBehaviorPulseAt <= 4.0",
    "HasStaleBehaviorHeartbeat()<transacts>:logic=",
    "not BehaviorPulseFresh()?",
    "IsBehaviorReady(Npc)?",
    "IsBehaviorReady(Agent)?",
    "IsBehaviorReady(Owned)?",
    "NpcChar.IsActive[]\n            BehaviorReady?",
    "Monster.IsActive[]\n            BehaviorReady?",
    "not SpawnInFlight?",
    "SpawnPendingForCurrentEpoch()<transacts>:logic=",
    "if (Active?, SpawnInFlight?, SpawnEpoch = Epoch):",
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
    "Service.AcknowledgeBehavior(Agent)?, BoundEpoch := Service.BoundEpochFor[Agent]",
    "set AckEpoch = BoundEpoch",
    "Service.WithdrawBehavior(Agent, AckEpoch)",
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
    "ExperimentalCameraEnabled:logic = false",
    "ProxyCamera:gameplay_camera_fixed_point_device",
    "ProxyCameraOffset:vector3",
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
    "StartProxyCamera(ExpectedEpoch, SpawnedAgent)",
    "TrackProxyCamera(ExpectedEpoch:int, Npc:agent, Owner:player)",
    "ProxyCamera.AddTo(Owner)",
    "ProxyCamera.TeleportTo[Position, Rotation]",
    "ProxyCamera.RemoveFrom(Owner)",
    "ReleaseProxyCamera()",
    "Attempts >= 20",
    "UnexpectedSpawnCount(Runtime)?",
    "if (not Runtime.SpawnPendingForCurrentEpoch()?):",
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
    "ActivateCommandInputs(Owner)",
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
    "Runtime.IsReadyForCurrentNpc()?",
    "Runtime.HasStaleBehaviorHeartbeat()?",
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
        "camera_type": "gameplay_camera_fixed_point_device",
        "camera_editor_path": None,
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
        "behavior_heartbeat_timeout_seconds": 4,
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
        "proxy_follow_camera": "experimental_opt_in_fixed_point_world_offset_unverified",
        "npc_possession": False,
        "experimental_enabled_by_default": False,
        "camera_device": "gameplay_camera_fixed_point_device",
        "camera_stack": "owner_only_AddTo_RemoveFrom",
        "update_seconds": 0.15,
        "camera_offset": "editable_world_space_not_NPC_facing",
        "native_test": "not_run",
    }:
        errors.append("camera/possession capability mismatch")
    for key in ("no_shared_npc_spawner", "no_second_owner_or_profile_root",
                "attack_cue_must_not_wire_damage", "f002_not_activated",
                "requires_native_compile", "requires_two_client_launch_session",
                "no_untagged_spawned_event_association",
                "no_global_input_registration",
                "camera_requires_npc_behavior_ack",
                "command_input_requires_behavior_ack",
                "behavior_onend_revokes_readiness",
                "behavior_onend_terminal_for_epoch",
                "behavior_end_cleanup_before_command_registration",
                "orphan_spawner_monitor_cleanup",
                "behavior_heartbeat_fail_closed"):
        if c.get("safety", {}).get(key) is not True:
            errors.append(f"safety gate disabled: {key}")
    lifecycle = c.get("lifecycle", {})
    for field, value in {
        "lease": "one_session_controller",
        "late_spawn": "reject_and_despawn",
        "npc_elimination": "exact_agent_identity_then_teardown",
        "input_registration": "summon_owner_only_commands_after_exact_behavior_ack",
        "behavior_ack": "npc_behavior_ack_required_before_commands",
        "behavior_end": "epoch_scoped_withdraw_and_terminal_command_cleanup",
        "orphan_spawns": "purge_dedicated_spawner_without_owner",
        "behavior_heartbeat": "ack_pulse_expiry_reaps_even_before_command_hud",
        "unexpected_spawns": "fail_closed_despawn_dedicated_spawner",
        "spawn_association": "serialized_SpawnAt_return_and_epoch",
        "inflight_inventory": "allow_single_untrusted_candidate_until_exact_SpawnAt_return_or_timeout",
        "owner_exit": "invalidate_before_despawn",
        "generation_change": "invalidate",
        "character_replacement": "invalidate",
        "device_shutdown": "cancel_subscriptions_and_despawn",
        "player_join": "no_implicit_entitlement",
        "replication": "native_npc_simulation_unverified",
        "camera_teardown": "remove_owner_camera_before_npc_despawn",
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
    # Begin marks SpawnInFlight before any SpawnAt is actually called.
    # Rejecting an already-populated dedicated spawner after Begin and
    # calling End would leave SpawnInFlight permanently set (no async
    # completion exists to clear it). Preflight must precede reservation.
    summon = device[device.find("    OnSummon(Agent:agent):void="):
                    device.find("    AwaitSpawn(ExpectedEpoch:int")]
    # No movement/cue/dismiss input may appear while SpawnAt suspends or
    # while the NPC behavior is still bootstrapping. Source checks are
    # structural; native UI timing remains a separate Launch Session gate.
    if "ActivateCommandInputs(" in summon:
        errors.append("Titan command HUD must remain off during spawn admission")
    owner_bound = summon.find("set ProxyOwner = option{Player}")
    summon_hidden = summon.find("RefreshSummonRegistration()")
    if not (0 <= owner_bound < summon_hidden < summon.find("TitanSpawner.Reset()")):
        errors.append("summon action must be retracted once a proxy is pending")
    eligible = device[device.find("    EligibleSummoner()<transacts>:?player="):
                      device.find("    RefreshSummonRegistration():void=")]
    if "not ProxyOwner?" not in eligible:
        errors.append("summon action must be hidden during active or pending proxy")
    ready_start = device.find("    AwaitBehaviorReady(ExpectedEpoch:int, SpawnedAgent:agent)")
    ready_end = device.find("    # An optional fixed-point camera", ready_start)
    ready = device[ready_start:ready_end]
    ack = ready.find("Runtime.IsBehaviorReady(SpawnedAgent)?")
    owner = ready.find("Owner := ProxyOwner?, Owner.IsActive[], Runtime.IsAuthorized()?")
    registration = ready.find("ActivateCommandInputs(Owner)")
    if ready_start < 0 or ready_end < 0 or not (0 <= ack < owner < registration):
        errors.append("Titan command input registration requires exact NPC ack and live owner")
    preflight = summon.find("TitanSpawner.GetAgents().Length <> 0")
    reserve = summon.find("Attempt := Runtime.Begin(")
    cleanup = summon.find("TitanSpawner.DespawnAll(false)")
    if min(preflight, reserve, cleanup) < 0 or not (preflight < cleanup < reserve):
        errors.append("Titan preexisting-spawn cleanup must precede async lease reservation")

    # A native SpawnAt call suspends while the NPC is loading. Polling
    # GetAgents before return cannot classify one candidate as hostile;
    # until CompleteSpawn checks its returned identity the candidate
    # remains untrusted and cannot execute commands or receive cues.
    inventory_at = device.find("    UnexpectedSpawnCount(Runtime:")
    inventory_end = device.find("    OnAdvance(Agent:agent):void=", inventory_at)
    inventory = device[inventory_at:inventory_end]
    if inventory_at < 0 or inventory_end < 0 or not (
        inventory.find("if (AllAgents.Length > 1):") >= 0
        and inventory.find("if (not Runtime.SpawnPendingForCurrentEpoch()?):") >= 0
        and inventory.find("if (AllAgents.Length > 1):")
        < inventory.find("if (not Runtime.SpawnPendingForCurrentEpoch()?):")
    ):
        errors.append("single pending SpawnAt candidate must remain untrusted until identity reconciliation")

    # Guard the actual command paths, not just a stray string elsewhere.
    for start, end, required in (
        ("    RequestMove(", "    GetNewMove(", "IsBehaviorReady(Npc)?"),
        ("    GetNewMove(", "    # Attack is a bounded", "IsBehaviorReady(Agent)?"),
        ("    RequestAttackCue(", "    # Invalidate mailbox", "IsBehaviorReady(Owned)?"),
    ):
        begin = runtime.find(start)
        finish = runtime.find(end, begin)
        if begin < 0 or finish <= begin or required not in runtime[begin:finish]:
            errors.append("heartbeat authorization missing in " + start.strip())
    ready_start = runtime.find("    IsReadyForCurrentNpc()")
    ready_end = runtime.find("    IsBehaviorReady(Agent:agent)", ready_start)
    if ready_start < 0 or ready_end <= ready_start or (
        "IsBehaviorReady(Npc)?" not in runtime[ready_start:ready_end]
    ):
        errors.append("current NPC readiness must require a fresh behavior pulse")
    get_new_start = runtime.find("    GetNewMove(")
    get_new_end = runtime.find("    # Attack is a bounded", get_new_start)
    if get_new_start < 0 or get_new_end <= get_new_start or (
        "        BehaviorReady?" not in runtime[get_new_start:get_new_end]
    ):
        errors.append("navigation dequeue must still require behavior readiness")
    if runtime.count("set LastBehaviorPulseAt = -1.0") < 4:
        errors.append("behavior heartbeat must reset on begin, bind, withdrawal and end")
    monitor_start = device.find("    Monitor()<suspends>:void=")
    monitor_end = device.find("    FinishProxy():void=", monitor_start)
    monitor = device[monitor_start:monitor_end]
    if monitor_start < 0 or monitor_end < 0 or not (
        0 <= monitor.find("Runtime.HasStaleBehaviorHeartbeat()?")
        < monitor.find("else if (CommandRegistered?):")
    ):
        errors.append("stale behavior heartbeat must be reaped before HUD registration")

    # The optional camera is presentation for a single authorized owner,
    # never NPC possession or a replacement for canonical FUS-001 control.
    if "ProxyCamera.AddToAll(" in device or "ProxyCamera.RemoveFromAll(" in device:
        errors.append("Titan experimental camera must not alter all players' camera stacks")
    camera_start = device.find("    StartProxyCamera(ExpectedEpoch:int, Npc:agent):void=")
    camera_end = device.find("    # Observes every native spawner agent", camera_start)
    camera = device[camera_start:camera_end]
    if camera_start < 0 or camera_end < 0 or not all(fragment in camera for fragment in (
        "ExperimentalCameraEnabled?",
        "Runtime.IsCurrentEpoch(ExpectedEpoch)?",
        "Runtime.IsBehaviorReady(Npc)?",
        "Owner := ProxyOwner?",
        "ProxyCamera.IsValid[]",
        "NpcCharacter := Npc.GetFortCharacter[]",
        "if (ProxyCamera.TeleportTo[Position, Rotation]):",
        "ProxyCamera.AddTo(Owner)",
        "set CameraOwner = option{Owner}",
        "Sleep(0.15)",
        "Runtime.IsBehaviorReady(Npc)?",
        "CurrentCameraOwner = Owner",
        "if (not ProxyCamera.TeleportTo[Position, Rotation]):",
        "ReleaseProxyCamera()",
        "ProxyCamera.RemoveFrom(Owner)",
        "set CameraOwner = false",
    )):
        errors.append("experimental camera lost owner/epoch/behavior gating or owned teardown")
    start_camera = camera.split("    TrackProxyCamera(ExpectedEpoch:int", 1)[0]
    if not (0 <= start_camera.find("if (ProxyCamera.TeleportTo[Position, Rotation]):")
            < start_camera.find("ProxyCamera.AddTo(Owner)")):
        errors.append("Titan camera must be positioned successfully before stack addition")
    # The camera is added only after behavior becomes ready, and must be
    # removed before despawning so FUS-001 orbit camera remains on the stack.
    ready_at = device.find("    AwaitBehaviorReady(ExpectedEpoch:int")
    if ready_at < 0 or not (
        device.find("Runtime.IsBehaviorReady(SpawnedAgent)?", ready_at)
        < device.find("StartProxyCamera(ExpectedEpoch, SpawnedAgent)", ready_at)
    ):
        errors.append("Titan camera must not start before NPC behavior acknowledgement")
    finish_at = device.find("    FinishProxy():void=")
    finish = device[finish_at:device.find("    OnEnd<override>():void=", finish_at)]
    if finish_at < 0 or not (
        0 <= finish.find("ReleaseProxyCamera()")
        < finish.find("Stopped := Runtime.End(Self)")
        < finish.find("TitanSpawner.DespawnAll(false)")
    ):
        errors.append("camera stack must be removed before NPC teardown")
    bindings_start = device.find("    GetPhysicalDevices()<decides><transacts>:[]creative_object=")
    bindings_end = device.find("    AddPhysicalDevice(", bindings_start)
    if bindings_start < 0 or bindings_end < 0 or not all(fragment in device[bindings_start:bindings_end] for fragment in (
        "if (ExperimentalCameraEnabled?):",
        "AddPhysicalDevice[Devices, ProxyCamera]",
    )):
        errors.append("optional camera binding must be checked only when enabled")

    # An NPC behavior may end without NPC elimination. Prevent an acknowledged
    # but now-headless NPC from accepting paid cues or retaining owner HUD.
    behavior_end = behavior[behavior.find("    OnEnd<override>():void="):]
    withdraw_at = runtime.find("    WithdrawBehavior(Agent:agent, ExpectedEpoch:int)")
    withdraw_end = runtime.find("    IsReadyForCurrentNpc()", withdraw_at)
    withdraw = runtime[withdraw_at:withdraw_end]
    movement_start = runtime.find("    GetNewMove(Agent:agent, SeenSequence:int)")
    movement_end = runtime.find("    # Attack is a bounded", movement_start)
    movement = runtime[movement_start:movement_end]
    monitor_start = device.find("    Monitor()<suspends>:void=")
    monitor_end = device.find("    FinishProxy():void=", monitor_start)
    monitor = device[monitor_start:monitor_end]
    if not all(x in behavior_end for x in (
        "if (AckEpoch > 0):", "Service.WithdrawBehavior(Agent, AckEpoch)",
        "Navigation.StopNavigation()"
    )) or not all(x in withdraw for x in (
        "Active?", "Epoch = ExpectedEpoch", "Current := OwnedNpc?",
        "Current = Agent", "set BehaviorTerminated = true",
        "set BehaviorReady = false", "set Pending = false"
    )) or "BehaviorReady?" not in movement or not all(x in monitor for x in (
        "else if (Runtime.HasTerminatedBehavior()?):",
        "else if (CommandRegistered?):",
        "if (not Runtime.IsReadyForCurrentNpc()?):", "FinishProxy()"
    )):
        errors.append("NPC behavior OnEnd must revoke exact epoch readiness and command HUD")

    # A terminal behavior must be reaped even if it ended between the
    # handshake and command HUD registration. Orphaned agents from a
    # dedicated spawner must also be cleared without an associated owner.
    terminal_at = monitor.find("else if (Runtime.HasTerminatedBehavior()?):")
    command_at = monitor.find("else if (CommandRegistered?):")
    orphan_at = monitor.find("if (TitanSpawner.GetAgents().Length > 0):")
    orphan_disable = monitor.find("TitanSpawner.Disable()", orphan_at)
    orphan_despawn = monitor.find("TitanSpawner.DespawnAll(false)", orphan_at)
    if not (0 <= terminal_at < command_at and
            "FinishProxy()" in monitor[terminal_at:command_at]):
        errors.append("terminal behavior must clean up before command registration")
    if not (0 <= command_at < orphan_at < orphan_disable < orphan_despawn
            and "else:\n                    # The spawner is dedicated" in monitor):
        errors.append("unowned Titan spawner agents must be purged in ownerless monitor branch")

    # OnEnd must be a one-way transition within the same epoch. Otherwise
    # an OnBegin poll overlapping native shutdown could re-acknowledge the
    # same NPC and reopen paid cues/owner HUD before the monitor tears down.
    begin = runtime[runtime.find("    Begin("):runtime.find("    IsAuthorized()")]
    acknowledge = runtime[runtime.find("    AcknowledgeBehavior("):
                          runtime.find("    # A stopped npc_behavior")]
    ready_start = runtime.find("    IsBehaviorReady(")
    ready = runtime[ready_start:runtime.find("    BoundNpc(Agent:agent)", ready_start)]
    move = runtime[runtime.find("    RequestMove("):runtime.find("    GetNewMove(")]
    cue = runtime[runtime.find("    RequestAttackCue("):runtime.find("    # Invalidate mailbox")]
    if not all((
        "set BehaviorTerminated = false" in begin,
        "if (not BehaviorTerminated?, BoundNpc(Agent)?):" in acknowledge,
        "set BehaviorTerminated = true" in withdraw,
        "if (not BehaviorTerminated?, BehaviorReady?, BoundNpc(Agent)?, BehaviorPulseFresh()?):" in ready,
        "not BehaviorTerminated?" in movement,
        "not BehaviorTerminated?" in move,
        "not BehaviorTerminated?" in cue,
    )):
        errors.append("terminal NPC behavior must not re-acknowledge or accept commands in same epoch")

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
