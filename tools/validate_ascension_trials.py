#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"content"/"transcendent"/"ascension_trials.json"

def main()->int:
    doc=json.loads(PATH.read_text(encoding="utf-8"))
    trials=doc.get("trials",[])
    errors=[]

    if len(trials)!=10:
        errors.append(f"expected exactly 10 Ascension Trials, found {len(trials)}")

    ids=set()
    for expected_index,trial in enumerate(trials,start=1):
        tid=trial.get("id")
        if tid in ids or not tid:
            errors.append(f"duplicate/empty trial id {tid}")
        ids.add(tid)

        if trial.get("index")!=expected_index:
            errors.append(f"{tid}: index {trial.get('index')} != {expected_index}")

        expected_id=f"ASC-TRIAL-{expected_index:03d}"
        if tid!=expected_id:
            errors.append(f"trial {expected_index}: id {tid} != {expected_id}")

        previous=trial.get("previous","")
        expected_previous="" if expected_index==1 else f"ASC-TRIAL-{expected_index-1:03d}"
        if previous!=expected_previous:
            errors.append(f"{tid}: previous {previous!r} != {expected_previous!r}")

        if len(trial.get("objectives",[]))<3:
            errors.append(f"{tid}: requires at least three objectives")

        limit=trial.get("time_limit_seconds")
        if not isinstance(limit,(int,float)) or limit<=0:
            errors.append(f"{tid}: invalid time limit")

        if expected_index<10 and trial.get("requires_axiom_heart") is True:
            errors.append(f"{tid}: only Trial X may require Axiom Heart")

    if len(trials)==10:
        t9=trials[8]
        t10=trials[9]
        if t9.get("unlocks_axiom_forge") is not True:
            errors.append("Trial IX must unlock the Axiom Forge")
        if t10.get("requires_axiom_heart") is not True:
            errors.append("Trial X must require the Axiom Heart")
        if t10.get("unlocks_axiom_forge") is True:
            errors.append("Trial X cannot unlock the forge after Heart requirement")

    if errors:
        print("AEONFALL Ascension Trial validation FAILED")
        for e in errors:
            print(f"- {e}")
        return 1

    print("AEONFALL Ascension Trial validation PASSED")
    print("- trials: 10")
    print("- Trial IX unlocks Axiom Forge: yes")
    print("- Trial X requires Axiom Heart: yes")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
