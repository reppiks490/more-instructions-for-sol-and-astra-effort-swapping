#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"content"/"transcendent"/"ascension_trials.json"
OUTPUT=ROOT/"verse"/"generated"/"ascension_trial_bootstrap.verse"

def q(v:str)->str:
    return '"' + v.replace("\\","\\\\").replace('"','\\"') + '"'

def arr(values:list[str])->str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main()->int:
    doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    lines=[
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/transcendent/ascension_trials.json",
        "",
        "AEONFALLAscensionTrialDefinitions:[]aeonfall_ascension_trial_definition = array{",
    ]
    for t in doc["trials"]:
        lines += [
            "    aeonfall_ascension_trial_definition{",
            f"        TrialId := {q(t['id'])},",
            f"        Index := {t['index']},",
            f"        DisplayName := {q(t['name'])},",
            f"        RequiredPreviousTrialId := {q(t.get('previous',''))},",
            f"        ObjectiveIds := {arr(t.get('objectives',[]))},",
            f"        TimeLimitSeconds := {float(t['time_limit_seconds']):.1f},",
            f"        RequiresAxiomHeart := {'true' if t.get('requires_axiom_heart') else 'false'},",
            f"        UnlocksAxiomForge := {'true' if t.get('unlocks_axiom_forge') else 'false'},",
            f"        AllowsCompanions := {'true' if t.get('allows_companions',True) else 'false'},",
            f"        AllowsGodAbilities := {'true' if t.get('allows_god_abilities',True) else 'false'},",
            f"        AllowsAbsoluteAbilities := {'true' if t.get('allows_absolute_abilities',True) else 'false'}",
            "    },",
        ]
    lines += [
        "}",
        "",
        "aeonfall_ascension_trial_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : AEONFALLAscensionTrialDefinitions):",
        "            Registered := GetAEONFALLAscensionTrialRegistry().Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.ascension_trial_registration_failed",',
        "                        SourceId := Definition.TrialId",
        "                    }",
        "                )",
        "",
    ]
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text("\n".join(lines),encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc['trials'])} trials")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
