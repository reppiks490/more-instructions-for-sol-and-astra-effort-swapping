#!/usr/bin/env python3
"""Regression guards for UNI-001 source and authored policy; no Verse execution."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "authority": "verse/sovereign/sovereign_authority_device.verse",
    "runtime": "verse/sovereign/sovereign_runtime.verse",
    "controller": "verse/sovereign/sovereign_controller_device.verse",
    "behavior": "verse/sovereign/sovereign_monster_behavior.verse",
    "normal_ai": "verse/sovereign/sovereign_normal_ai_device.verse",
}
POLICY_PATH = "content/sovereign/sovereign_unmaking.json"


def code(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def method(source: str, name: str) -> str:
    match = re.search(rf"^    {re.escape(name)}(?:<[^\n]*?>)?\(", source, re.M)
    if not match:
        return ""
    following = re.search(r"^    [A-Za-z_][A-Za-z0-9_]*(?:<[^\n]*?>)?\(", source[match.end():], re.M)
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def check_sources(sources: dict[str, str], policy: dict) -> list[str]:
    source = {name: code(text) for name, text in sources.items()}
    errors: list[str] = []
    def need(name: str, fragment: str):
        if fragment not in source[name]:
            errors.append(f"{name}: missing guard {fragment}")
    def scoped(name: str, method_name: str, *fragments: str):
        block = method(source[name], method_name)
        for fragment in fragments:
            if fragment not in block:
                errors.append(f"{name}.{method_name}: missing guard {fragment}")
    def ordered(name: str, method_name: str, *fragments: str):
        block = method(source[name], method_name)
        positions = [block.find(fragment) for fragment in fragments]
        if any(index < 0 for index in positions) or positions != sorted(positions):
            errors.append(f"{name}.{method_name}: missing or reordered atomic commit")

    for name in ("authority", "controller"):
        need(name, "Enabled:logic = false")
        need(name, "weak_map(session," if name == "authority" else "Authority:aeonfall_sovereign_authority_device")
    scoped("authority", "CanWield", "Running?", "not Revoked?", "Bound = Player",
           "Player.IsActive[]", "OwnerReference.IsReferenced[Player]")
    scoped("authority", "ObserveReference", "Reference := OwnerReference.GetAgent()", "Current = Bound",
           "set Revoked = true", "Candidate := player[Agent]")
    if "OwnerReference.Register(" in source["authority"] or "PlayerAddedEvent" in source["authority"]:
        errors.append("authority: public registration or first-join provisioning is forbidden")
    if "GetPlayerName" in source["authority"] or "GetTeam" in source["authority"]:
        errors.append("authority: names and teams cannot authenticate the unique owner")
    need("runtime", "weak_map(session, aeonfall_sovereign_runtime)")
    need("runtime", "GetAEONFALLSovereignRuntime()<decides><transacts>")
    need("runtime", "set AEONFALLSovereignRuntimes[GetSession()] = Created")
    scoped("runtime", "BindVerifiedOwner", "Existing = Player", "return false", "Player.IsActive[]")
    scoped("runtime", "Begin", "Current = Device", "Existing = Player", "not Active?",
           "set Generation += 1", "Duration <= 600.0", "ArmyCap <= 96")
    scoped("runtime", "Enroll", "Player <> OwnerPlayer", "Participants.Length >= 512", "Generation = Token")
    scoped("runtime", "PayTribute", "<decides><transacts>:void=", "Sovereign <> Payer",
           "Payer.IsActive[]", "Sovereign.IsActive[]", "Held >= Amount", "OwnerAmount <= 1000000000 - Amount")
    ordered("runtime", "PayTribute", "PayerSaved := ProfileService.TrySaveProfile(Payer, NewPayer)",
            "PayerSaved?", "OwnerSaved := ProfileService.TrySaveProfile(Sovereign, NewOwner)",
            "OwnerSaved?", "set Participants[Payer]")
    scoped("runtime", "ClaimArmy", "Generation = Token", "Army.Length < MaxArmy")
    scoped("runtime", "Resolve", "Generation = Token", "Now - State.JoinedAt < MinimumExposureSeconds",
           "set Active = false", "set Army = map{}")
    scoped("controller", "AuthorizedOwner", "Character.IsActive[]", "Authorized := Authority.CanWield(Player)", "Authorized?")
    scoped("controller", "ToggleVeil", "AuthorizedOwner[Agent]", "BindVerifiedOwner(Player)", "Character.Hide()", "Existing.Show()")
    if "Sleep(" in method(source["controller"], "ToggleVeil"):
        errors.append("controller.ToggleVeil: the owner veil cannot have a cooldown")
    scoped("controller", "MaintenanceLoop", "Authority.CanWield(Sovereign)", "RevealOwner()",
           "Finish(Token, true)", "GetSimulationElapsedTime() >= Service.Deadline", "ShowParticipantSnapshot(Player, Service)",
           "not Hidden.IsActive[]", "RestoreTeams()", "GetAgents().Length > RiftBurstPerRegion")
    scoped("controller", "Manifest", "Service.IsCurrent(Generation)?", "Region.Maelstrom.Enable()",
           "Region.Rift.Enable()", "1..RiftBurstPerRegion", "Region.Monstrosities.Spawn()")
    scoped("controller", "Draw", "Service.Begin[Self, Player", "RedVoidSky.Play()", "Countdown.Start()", "OriginalTeams.Length = 0")
    scoped("controller", "PlayerJoined", "Service.Enroll(Player, Token)", "ShowParticipantSnapshot(Player, Service)")
    scoped("controller", "ShowParticipantSnapshot", "aeonfall_sovereign_quest_state.Tributed", "Demand.Hide(Player)",
           "aeonfall_sovereign_quest_state.Defiant", "Demand.Show(Player, SovereignDemand, 0.0)")
    scoped("controller", "ValidSettings", "Regions.Length <= 8", "Regions.Length * RiftBurstPerRegion <= 32",
           "DrawInput <> VeilInput", "SeenSpawners.Find[Region.Monstrosities]", "SeenVFX.Find[Region.Maelstrom]",
           "not Countdown.IsStatePerAgent[]")
    scoped("controller", "RecruitRegisteredMonsters", "not player[Agent]", "Character.GetNavigatable[]",
           "Service.ClaimArmy[Agent, Token]", "Teams.AddToTeam[Agent, OwnerTeam]", "Service.RemoveArmyMember(Agent)")
    scoped("controller", "IsMonsterCanonical", "Id[0] = 'M'", "Id[1] = 'O'", "Id[2] = 'N'", "Id[3] = '-'")
    scoped("controller", "Finish", "Service.Resolve[Generation, Stopped, MinimumExposureSeconds]",
           "EnableUnmakingElimination?", "State.MayBeEliminated?", "Character.Damage(")
    need("controller", "EnableUnmakingElimination:logic = false")
    scoped("runtime", "Defy", "State.State = aeonfall_sovereign_quest_state.Demanded", "MayBeEliminated := true")
    if source["runtime"].count("MayBeEliminated := true") != 1:
        errors.append("runtime: only explicit Defy may consent to optional elimination")
    scoped("controller", "CleanupPhysical", "RedVoidSky.Stop()", "Region.Maelstrom.Disable()", "Region.Rift.Disable()",
           "Region.Monstrosities.DespawnAll(false)", "Countdown.Reset()", "RestoreTeams()")
    scoped("controller", "RestoreTeams", "Teams.AddToTeam[Agent, OldTeam]", "set Pending[Agent] = OldTeam", "set OriginalTeams = Pending")
    scoped("controller", "OnEnd", "Subscription.Cancel()", "Service.OwnsController(Self)?", "RevealOwner()", "Service.ReleaseController(Self)")
    scoped("behavior", "OnBegin", "Service.GetCommand[Agent]", "Navigation.NavigateTo(", "Sleep(0.5)", "Navigation.StopNavigation()")
    waits = re.findall(r"Sleep\(([0-9.]+)\)", method(source["behavior"], "OnBegin"))
    if not waits or any(float(wait) > 0.5 for wait in waits):
        errors.append("behavior.OnBegin: every navigation cancellation wait must be at most 0.5 seconds")
    if "option{Character.EliminatedEvent().Subscribe" in source["controller"]:
        errors.append("controller.Draw: capture the native subscription before option construction")
    scoped("behavior", "OnEnd", "NormalAI.Forget(Agent)", "Service.RemoveArmyMember(Agent)", "Navigation.StopNavigation()")
    for name, text in source.items():
        if "GetFortCharacter()" in text:
            errors.append(f"{name}: native failable GetFortCharacter requires []")
    expected = {
        "id": "UNI-001", "owner_limit": 1, "ordinary_unlockable": False,
        "veil.unlimited_at_will": True, "veil.cooldown_seconds": 0, "veil.resource_cost": 0,
        "quest.owner_exempt": True, "quest.tribute.material_id": "MAT-008", "quest.tribute.amount": 40,
        "quest.tribute.checked_atomic_two_profile_save": True,
        "army.maximum_commanded": 64, "army.rift_total_limit": 32, "army.spawn_timer_required": False,
        "army.spawn_at_game_start_required": False,
        "engine_verification.compile": "not_run", "engine_verification.session": "not_run",
    }
    for key, expected_value in expected.items():
        value = policy
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if type(value) is not type(expected_value) or value != expected_value:
            errors.append(f"policy drift: {key}")
    if len(policy.get("activation", {}).get("stages", [])) != 3:
        errors.append("policy: herald, maelstrom and rift stages required")
    return errors


def main() -> int:
    try:
        sources = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in SOURCES.items()}
        policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
        errors = check_sources(sources, policy)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Sovereign Unmaking source and authored policy guards passed; engine execution not run.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
