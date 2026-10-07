#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"content"/"catalog"
SLICE=ROOT/"content"/"vertical_slice"/"slice_001_ossuary_march.json"
COMBAT=ROOT/"content"/"vertical_slice"/"slice_001_combat_runtime.json"
CLASSES=ROOT/"content"/"vertical_slice"/"slice_001_classes.json"

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
    doc=json.loads(CLASSES.read_text(encoding="utf-8"))
    ability_ids={a["id"] for a in combat.get("abilities",[])}
    status_ids={s["id"] for s in combat.get("statuses",[])}
    allowed_classes=set(slice_doc.get("classes",[]))
    seen=set()

    for c in doc.get("classes",[]):
        cid=c.get("class_id")
        if not cid or cid in seen: errors.append(f"duplicate/empty class id {cid}")
        seen.add(cid)
        if cid not in catalog or catalog[cid].get("family")!="class": errors.append(f"{cid}: missing canonical class")
        if cid not in allowed_classes: errors.append(f"{cid}: not selected for SLICE-001")
        if not c.get("ability_ids"): errors.append(f"{cid}: must define at least one ability")
        for aid in c.get("ability_ids",[]):
            if aid not in ability_ids: errors.append(f"{cid}: unknown first-slice ability {aid}")
        for sid in c.get("passive_status_ids",[]):
            if sid not in status_ids: errors.append(f"{cid}: unknown passive status {sid}")
        if not isinstance(c.get("max_resource"),int) or c["max_resource"]<0: errors.append(f"{cid}: invalid max_resource")
        if not isinstance(c.get("base_max_companions"),int) or c["base_max_companions"]<0: errors.append(f"{cid}: invalid base_max_companions")
        if not str(c.get("resource_id","")).strip(): errors.append(f"{cid}: resource_id empty")
        if not c.get("resource_rules"): errors.append(f"{cid}: resource rules empty")
        for unlock in c.get("required_unlock_ids",[]):
            if unlock not in catalog: errors.append(f"{cid}: missing unlock prerequisite {unlock}")

    if set(seen)!=allowed_classes:
        errors.append(f"class manifest mismatch; expected={sorted(allowed_classes)} actual={sorted(seen)}")

    if errors:
        print("AEONFALL first-slice class validation FAILED")
        for e in errors: print(f"- {e}")
        return 1

    print("AEONFALL first-slice class validation PASSED")
    print(f"- classes: {len(seen)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
