#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"content"/"catalog"
SLICE=ROOT/"content"/"vertical_slice"/"slice_001_ossuary_march.json"
DATA=ROOT/"content"/"vertical_slice"/"slice_001_hireables.json"

ORDERS={"Follow","Guard","FocusTarget","HoldPosition","Flank","Retreat"}

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
    doc=json.loads(DATA.read_text(encoding="utf-8"))

    expected=set(slice_doc["hireables"])
    slice_bosses=set(slice_doc["minibosses"])|{slice_doc["major_boss"]}
    slice_events={slice_doc["world_event"]}
    seen=set()

    for item in doc.get("hireables",[]):
        nid=item.get("npc_id")
        if not nid or nid in seen: errors.append(f"duplicate/empty hireable id {nid}")
        seen.add(nid)
        entity=catalog.get(nid)
        if not entity or entity.get("family")!="npc":
            errors.append(f"{nid}: missing canonical NPC")
        elif entity.get("acquisition",{}).get("paid") is True:
            errors.append(f"{nid}: first-slice hireable must remain earnable, not paid-designated")
        if nid not in expected: errors.append(f"{nid}: not selected for SLICE-001")

        fid=item.get("faction_id","")
        if fid:
            if fid not in catalog or catalog[fid].get("family")!="faction":
                errors.append(f"{nid}: invalid faction {fid}")

        rep=item.get("required_reputation")
        if not isinstance(rep,int) or rep<0: errors.append(f"{nid}: invalid required reputation {rep}")

        orders=item.get("allowed_orders",[])
        if not orders: errors.append(f"{nid}: no allowed orders")
        invalid=[o for o in orders if o not in ORDERS]
        if invalid: errors.append(f"{nid}: invalid orders {invalid}")
        if len(orders)!=len(set(orders)): errors.append(f"{nid}: duplicate allowed orders")

        if item.get("max_simultaneous_per_player")!=1:
            errors.append(f"{nid}: first-slice individual hireable cap must be 1")

        for boss in item.get("required_boss_ids",[]):
            if boss not in slice_bosses:
                errors.append(f"{nid}: boss gate {boss} is not available inside SLICE-001")
        for event in item.get("required_world_event_ids",[]):
            if event not in slice_events:
                errors.append(f"{nid}: event gate {event} is not available inside SLICE-001")
        for unlock in item.get("required_unlock_ids",[]):
            if unlock not in catalog:
                errors.append(f"{nid}: missing unlock prerequisite {unlock}")

    if seen!=expected:
        errors.append(f"hireable manifest mismatch; expected={sorted(expected)} actual={sorted(seen)}")

    if errors:
        print("AEONFALL first-slice hireable validation FAILED")
        for e in errors: print(f"- {e}")
        return 1

    print("AEONFALL first-slice hireable validation PASSED")
    print(f"- hireables: {len(seen)}")
    print("- paid-designated selected: 0")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
