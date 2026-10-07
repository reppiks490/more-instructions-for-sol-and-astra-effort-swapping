#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"content"/"catalog"
SLICE=ROOT/"content"/"vertical_slice"/"slice_001_ossuary_march.json"
COMBAT=ROOT/"content"/"vertical_slice"/"slice_001_combat_runtime.json"
DATA=ROOT/"content"/"vertical_slice"/"slice_001_taming.json"

STEPS={"Approach","Feed","Evade","Calm","Track","Protect","DenyCorpse"}

def load_catalog():
    result={}
    for p in CATALOG.rglob("*.json"):
        payload=json.loads(p.read_text(encoding="utf-8"))
        values=payload.get("entities",[]) if isinstance(payload,dict) else payload
        for e in values:
            if isinstance(e,dict) and e.get("id"):
                result[e["id"]]=e
    return result

def main()->int:
    errors=[]
    catalog=load_catalog()
    slice_doc=json.loads(SLICE.read_text(encoding="utf-8"))
    combat=json.loads(COMBAT.read_text(encoding="utf-8"))
    doc=json.loads(DATA.read_text(encoding="utf-8"))

    expected=set(slice_doc["tameable_wildlife"])
    ability_ids={a["id"] for a in combat.get("abilities",[])}
    if doc.get("ability_id") not in ability_ids:
        errors.append(f"missing taming ability {doc.get('ability_id')}")
    if doc.get("required_class_id") not in set(slice_doc["classes"]):
        errors.append(f"required class {doc.get('required_class_id')} is not in SLICE-001")

    seen=set()
    sequences=set()
    for species in doc.get("species",[]):
        sid=species.get("species_id")
        if not sid or sid in seen: errors.append(f"duplicate/empty species id {sid}")
        seen.add(sid)
        if sid not in catalog or catalog[sid].get("family")!="wildlife":
            errors.append(f"{sid}: missing canonical wildlife definition")
        if sid not in expected:
            errors.append(f"{sid}: not selected as SLICE-001 tameable")
        steps=species.get("steps",[])
        if len(steps)<3:
            errors.append(f"{sid}: taming sequence requires at least three steps")
        invalid=[s for s in steps if s not in STEPS]
        if invalid:
            errors.append(f"{sid}: invalid steps {invalid}")
        seq=tuple(steps)
        if seq in sequences:
            errors.append(f"{sid}: duplicates another species' full taming sequence")
        sequences.add(seq)
        timeout=species.get("max_challenge_seconds")
        if not isinstance(timeout,(int,float)) or timeout<=0:
            errors.append(f"{sid}: invalid challenge timeout {timeout}")
        if not str(species.get("failure_event_id","")).strip():
            errors.append(f"{sid}: missing failure event")
        if not str(species.get("success_event_id","")).strip():
            errors.append(f"{sid}: missing success event")

    if seen!=expected:
        errors.append(f"taming manifest mismatch; expected={sorted(expected)} actual={sorted(seen)}")

    if errors:
        print("AEONFALL first-slice taming validation FAILED")
        for e in errors: print(f"- {e}")
        return 1

    print("AEONFALL first-slice taming validation PASSED")
    print(f"- species: {len(seen)}")
    print(f"- unique challenge sequences: {len(sequences)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
