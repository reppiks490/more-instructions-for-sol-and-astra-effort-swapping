"""Source-mutation guards for live NPC targeting and status execution.

These checks are not a Verse compiler or a native Fortnite play session.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "verse/core/actor_registry.verse"
TARGETING = "verse/combat/targeting_runtime.verse"
INPUT = "verse/combat/targeted_ability_input_device.verse"
STATUS = "verse/combat/status_ability_adapter_device.verse"
PATHS = (REGISTRY, TARGETING, INPUT, STATUS)


def section(source: str, start: str, end: str | None = None) -> str:
    if start not in source:
        return ""
    block = source.split(start, 1)[1]
    return block.split(end, 1)[0] if end and end in block else block


def source_errors(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    registry = sources.get(REGISTRY, "")
    targeting = sources.get(TARGETING, "")
    target_input = sources.get(INPUT, "")
    status = sources.get(STATUS, "")

    live = section(registry, "    IsLiveCharacter(", "    Unregister(")
    for fragment in (
        "IsLiveCharacter(RuntimeKey:string)<decides><transacts>:void=",
        "IsRegistered[RuntimeKey]",
        "TargetAgent := GetAgent[RuntimeKey]",
        "Character := TargetAgent.GetFortCharacter[]",
        "Character.IsActive[]",
    ):
        if fragment not in "    IsLiveCharacter(" + live:
            errors.append("actor liveness must use native active-character check: " + fragment)
    if "using { /Fortnite.com/Characters }" not in registry:
        errors.append("actor registry missing native fort_character API import")

    checks = (
        ("set_actor", "    SetActorTarget(", "    SetRuntimeTarget(",
         "GetAEONFALLActorRegistry().IsLiveCharacter[TargetKey]"),
        ("set_runtime", "    SetRuntimeTarget(", "    GetSelection(",
         "GetAEONFALLActorRegistry().IsLiveCharacter[TargetKey]"),
        ("get_selection", "    GetSelection(", "    Clear(",
         "GetAEONFALLActorRegistry().IsLiveCharacter[Selection.TargetKey]"),
        ("tick", "    TickAll(", "# Mutable service allocation",
         "GetAEONFALLActorRegistry().IsLiveCharacter[Selection.TargetKey]"),
    )
    for label, start, end, fragment in checks:
        if fragment not in section(targeting, start, end):
            errors.append("targeting " + label + " must revalidate live character")
    if "GetAEONFALLActorRegistry().IsRegistered[OwnerKey]" not in section(
        targeting, "    SetRuntimeTarget(", "    GetSelection("
    ):
        errors.append("target selector still must verify authoritative owner")

    pressed = section(target_input, "    OnPressed(", "#")
    # The first comment in OnPressed is not a boundary; use the whole callback.
    pressed = section(target_input, "    OnPressed(")
    for fragment in (
        "player[Agent]",
        "OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]",
        "OwnerCharacter := Agent.GetFortCharacter[]",
        "OwnerCharacter.IsActive[]",
        "Selection := GetAEONFALLTargetingRuntime().GetSelection[OwnerKey]",
        "GetAEONFALLAbilityActivationService().TryActivate(",
    ):
        if fragment not in pressed:
            errors.append("targeted input missing active-owner guard: " + fragment)
    if not (0 <= pressed.find("OwnerCharacter.IsActive[]") <
            pressed.find("GetSelection[OwnerKey]") <
            pressed.find("TryActivate(")):
        errors.append("targeted input must verify owner before paid request")
    if "using { /Fortnite.com/Characters }" not in target_input:
        errors.append("targeted input missing native fort_character API import")

    handler = section(status, "    OnAbilityEffectRequested(")
    for fragment in (
        "ClaimEffectRequest(Request)",
        "if (not GetAEONFALLActorRegistry().IsRegistered[Request.TargetKey]):",
        'set ResultCode = "target_not_registered"',
        "else if (not GetAEONFALLActorRegistry().IsLiveCharacter[Request.TargetKey]):",
        'set ResultCode = "target_not_active"',
        "if (Succeeded?):",
        "GetAEONFALLStatusRuntime().ApplyBatch[",
        "AEONFALLAdapterResultDelivery.Report(",
    ):
        if fragment not in handler:
            errors.append("status adapter must fail closed on dead target: " + fragment)
    if not (0 <= handler.find("ClaimEffectRequest(Request)") <
            handler.find("IsRegistered[Request.TargetKey]") <
            handler.find("IsLiveCharacter[Request.TargetKey]") <
            handler.find('set ResultCode = "target_not_active"') <
            handler.find("GetAEONFALLStatusRuntime().ApplyBatch[")):
        errors.append("status preflight must reject dead target before side effects")
    return errors


def reference_target_eligible(registered: bool, fort_character_active: bool) -> bool:
    return registered and fort_character_active


class LiveTargetAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {path: (ROOT / path).read_text(encoding="utf-8") for path in PATHS}

    def mutate(self, path: str, before: str, after: str) -> None:
        self.assertIn(before, self.sources[path])
        other = dict(self.sources)
        other[path] = other[path].replace(before, after, 1)
        self.assertTrue(source_errors(other), before)

    def mutate_last(self, path: str, before: str, after: str) -> None:
        # The target runtime calls liveness on create and read/tick.
        # Mutate the later call specifically instead of detecting a different
        # guard failure in the earlier method.
        at = self.sources[path].rfind(before)
        self.assertGreaterEqual(at, 0)
        other = dict(self.sources)
        other[path] = other[path][:at] + after + other[path][at+len(before):]
        self.assertTrue(source_errors(other), before)

    def test_authored_source(self):
        self.assertEqual(source_errors(self.sources), [])

    def test_registry_cannot_trust_key_alone(self):
        self.mutate(REGISTRY, "        Character.IsActive[]", '        Character = Character')

    def test_registry_requires_live_native_character(self):
        self.mutate(REGISTRY, "        Character := TargetAgent.GetFortCharacter[]",
                    "        Character := TargetAgent")

    def test_actor_target_preflight(self):
        self.mutate(TARGETING, "            GetAEONFALLActorRegistry().IsLiveCharacter[TargetKey]",
                    "            GetAEONFALLActorRegistry().IsRegistered[TargetKey]")

    def test_runtime_target_preflight(self):
        self.mutate_last(TARGETING, "            GetAEONFALLActorRegistry().IsLiveCharacter[TargetKey]",
                    "            GetAEONFALLActorRegistry().IsRegistered[TargetKey]")

    def test_read_must_revalidate_liveness(self):
        self.mutate(TARGETING, "        GetAEONFALLActorRegistry().IsLiveCharacter[Selection.TargetKey]",
                    "        GetAEONFALLActorRegistry().IsRegistered[Selection.TargetKey]")

    def test_tick_expires_eliminated_npc(self):
        self.mutate_last(TARGETING, "                GetAEONFALLActorRegistry().IsLiveCharacter[Selection.TargetKey]",
                    "                GetAEONFALLActorRegistry().IsRegistered[Selection.TargetKey]")

    def test_target_input_rejects_eliminated_owner(self):
        self.mutate(INPUT, "            OwnerCharacter.IsActive[]",
                    "            OwnerCharacter = OwnerCharacter")

    def test_target_input_requires_actual_player(self):
        self.mutate(INPUT, "            player[Agent]",
                    "            Agent = Agent")

    def test_status_adapter_rejects_dead_registered_target(self):
        self.mutate(STATUS, "else if (not GetAEONFALLActorRegistry().IsLiveCharacter[Request.TargetKey]):",
                    "else if (not GetAEONFALLActorRegistry().IsRegistered[Request.TargetKey]):")

    def test_status_adapter_rejects_without_success_result(self):
        self.mutate(STATUS, 'set ResultCode = "target_not_active"',
                    'set ResultCode = "ok"')

    def test_status_adapter_distinguishes_missing_registration(self):
        self.mutate(STATUS, 'set ResultCode = "target_not_registered"',
                    'set ResultCode = "ok"')

    def test_reference_registered_but_eliminated_is_not_targetable(self):
        self.assertFalse(reference_target_eligible(True, False))
        self.assertFalse(reference_target_eligible(False, True))
        self.assertTrue(reference_target_eligible(True, True))


if __name__ == "__main__":
    unittest.main()
