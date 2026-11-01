#!/usr/bin/env python3
"""Build fail-closed Verse definitions for canonical intermediate Axiom refinements."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "content/crafting/axiom_heart_recipe.json"
BINDINGS = ROOT / "content/crafting/refinement_gate_bindings.json"
OUTPUT = ROOT / "verse/generated/axiom_refinement_recipes.verse"


def render(graph: dict, bindings: dict) -> str:
    recipes = graph["recipes"]
    if graph["root_material_id"] != "MAT-030":
        raise ValueError("Axiom Heart canonical root changed")
    by_id = {r["id"]: r for r in recipes}
    if len(by_id) != len(recipes) or "RCP-013" not in by_id:
        raise ValueError("duplicate recipe ID or missing RCP-013")
    entries = bindings["recipes"]
    bound = {e["recipe_id"]: e for e in entries}
    expected = set(by_id) - {"RCP-013"}
    if len(bound) != len(entries) or set(bound) != expected:
        raise ValueError("every non-final canonical recipe needs exactly one gate binding")
    lines = [
        "# GENERATED FILE — do not hand edit.",
        "# Sources: content/crafting/axiom_heart_recipe.json + refinement_gate_bindings.json",
        "AxiomRefinementRecipes:[]aeonfall_refinement_recipe_definition = array{",
    ]
    for recipe in recipes:
        rid = recipe["id"]
        if rid == "RCP-013":
            continue
        gate = bound[rid]
        state = gate["state"]
        if state not in {"bound", "unbound"}:
            raise ValueError(f"{rid}: invalid gate state")
        if not isinstance(gate["reason"], str) or not gate["reason"].strip():
            raise ValueError(f"{rid}: missing gate evidence explanation")
        rank = gate["minimum_ascension_rank"]
        if type(rank) is not int or not 0 <= rank <= 2:
            raise ValueError(f"{rid}: invalid ascension rank")
        trials = gate["required_trial_ids"]
        if (not isinstance(trials, list) or len(set(trials)) != len(trials)
                or any(t not in {f"ASC-TRIAL-{i:03d}" for i in range(1, 11)} for t in trials)):
            raise ValueError(f"{rid}: invalid trial binding")
        # RCP-012's entire narrative prerequisite set is provable today.
        if rid == "RCP-012" and (state != "bound" or rank != 2 or trials != ["ASC-TRIAL-008"]):
            raise ValueError("RCP-012 must require Absolute rank and Trial VIII")
        if state == "bound" and rid != "RCP-012":
            raise ValueError(f"{rid}: unverified narrative prerequisites cannot be marked bound")
        output = recipe["output"]
        out_id, qty = output["material_id"], output["quantity"]
        if out_id == "MAT-030" or type(qty) is not int or qty <= 0:
            raise ValueError(f"{rid}: invalid intermediate output")
        costs = recipe["inputs"]
        ids = [c["material_id"] for c in costs]
        if (not costs or len(ids) != len(set(ids)) or out_id in ids
                or any(type(c["quantity"]) is not int or c["quantity"] <= 0 for c in costs)):
            raise ValueError(f"{rid}: invalid or duplicate inputs")
        if not recipe["station"].strip():
            raise ValueError(f"{rid}: missing station")
        costs_verse = ", ".join(
            f'aeonfall_material_cost{{MaterialId := {json.dumps(c["material_id"])}, Amount := {c["quantity"]}}}'
            for c in costs
        )
        trials_verse = ", ".join(json.dumps(t) for t in trials)
        lines.extend([
            f"    # {rid}: {gate['reason']}",
            "    aeonfall_refinement_recipe_definition{",
            f'        RecipeId := {json.dumps(rid)},',
            f'        StationId := {json.dumps(recipe["station"])},',
            f'        OutputMaterialId := {json.dumps(out_id)},',
            f'        OutputQuantity := {qty},',
            f'        Costs := array{{{costs_verse}}},',
            f'        MinimumAscensionRank := {rank},',
            f'        RequiredTrialIds := array{{{trials_verse}}},',
            f'        GateBound := {"true" if state == "bound" else "false"}',
            "    },",
        ])
    lines.extend(["}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(json.loads(GRAPH.read_text(encoding="utf-8")),
                      json.loads(BINDINGS.read_text(encoding="utf-8")))
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("stale intermediate refinement registry")
        print("Axiom refinement registry matches canonical graph and gate bindings")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8")
        print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
