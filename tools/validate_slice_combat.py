#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
DATA = ROOT / "content" / "vertical_slice" / "slice_001_combat_runtime.json"

RESOURCE_POLICIES = {"Cooldown","Charges","Meter","EncounterOnly","TransformationOnly"}
TARGET_POLICIES = {"Self","Ally","Enemy","Position","Direction","Area","AuthoredObjective"}
STACK_RULES = {"RefreshDuration","AddStack","ReplaceIfStronger","RejectDuplicate"}
STATUS_CATEGORIES = {"Buff","Debuff","CrowdControl","DamageOverTime","HealingOverTime","Reveal","Mark","Environmental"}

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

    allowed_owners=set(slice_doc["skills"])|set(slice_doc["classes"])|set(slice_doc["weapons"])|set(slice_doc["armor_sets"])
    statuses=doc.get("statuses",[])
    abilities=doc.get("abilities",[])
    status_ids=set()
    ability_ids=set()

    for s in statuses:
        sid=s.get("id")
        if not sid or sid in status_ids: errors.append(f"duplicate/empty status id {sid}")
        status_ids.add(sid)
        if s.get("stack_rule") not in STACK_RULES: errors.append(f"{sid}: invalid stack rule {s.get('stack_rule')}")
        if s.get("category") not in STATUS_CATEGORIES: errors.append(f"{sid}: invalid category {s.get('category')}")
        if not isinstance(s.get("max_stacks"),int) or s["max_stacks"]<=0: errors.append(f"{sid}: max_stacks must be positive")
        if not isinstance(s.get("duration_seconds"),(int,float)) or s["duration_seconds"]<0: errors.append(f"{sid}: duration must be >= 0")

    for a in abilities:
        aid=a.get("id")
        owner=a.get("owner_entity_id")
        policy=a.get("resource_policy")
        if not aid or aid in ability_ids: errors.append(f"duplicate/empty ability id {aid}")
        ability_ids.add(aid)
        if owner not in catalog: errors.append(f"{aid}: missing owner {owner}")
        if owner not in allowed_owners: errors.append(f"{aid}: owner {owner} is outside first-slice ability scope")
        if policy not in RESOURCE_POLICIES: errors.append(f"{aid}: invalid resource policy {policy}")
        if a.get("target_policy") not in TARGET_POLICIES: errors.append(f"{aid}: invalid target policy {a.get('target_policy')}")
        if not str(a.get("adapter_id","")).strip(): errors.append(f"{aid}: missing publish-path adapter")

        for sid in a.get("status_ids",[]):
            if sid not in status_ids: errors.append(f"{aid}: missing referenced status {sid}")

        if policy=="Cooldown" and a.get("cooldown_seconds",0)<=0: errors.append(f"{aid}: cooldown ability requires cooldown_seconds > 0")
        if policy=="Charges":
            if a.get("max_charges",0)<=0: errors.append(f"{aid}: charge ability requires max_charges > 0")
            if a.get("recharge_seconds",0)<=0: errors.append(f"{aid}: charge ability requires recharge_seconds > 0")
        if policy=="Meter":
            if a.get("max_meter",0)<=0: errors.append(f"{aid}: meter ability requires max_meter > 0")
            cost=a.get("activation_cost",0)
            if cost<=0 or cost>a.get("max_meter",0): errors.append(f"{aid}: invalid meter activation cost {cost}")

        if a.get("requires_transformation_context") and policy!="TransformationOnly":
            errors.append(f"{aid}: transformation context requirement must use TransformationOnly policy")
        if a.get("requires_encounter_context") and policy not in {"EncounterOnly","TransformationOnly"}:
            errors.append(f"{aid}: encounter context requirement should use encounter-scoped policy")

    if len(statuses)<10: errors.append("first slice requires at least 10 canonical status definitions")
    if len(abilities)<8: errors.append("first slice requires at least 8 canonical ability definitions")

    if errors:
        print("AEONFALL first-slice combat runtime validation FAILED")
        for e in errors: print(f"- {e}")
        return 1

    print("AEONFALL first-slice combat runtime validation PASSED")
    print(f"- statuses: {len(statuses)}")
    print(f"- abilities: {len(abilities)}")
    print("- production dependency on Experimental Ability API: none")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
