# Intermediate Axiom Heart Refinement — Executable Boundary

Canonical source: `content/crafting/axiom_heart_recipe.json`. Gate evidence:
`content/crafting/refinement_gate_bindings.json`. Generated source:
`verse/generated/axiom_refinement_recipes.verse`.

The 13 nonfinal recipes (RCP-001–012, RCP-014) now have generated
material/station definitions. A dedicated server-owned transaction consumes
inputs and credits the output in **one checked persistent profile replacement**.
The existing RCP-013 final forge remains the only path to MAT-030/Axiom Heart.
The generator never emits RCP-013 into the intermediate registry.

**Only RCP-012 is enabled at this stage.** Its full narrative prerequisite
set maps to existing durable evidence: Absolute ascension rank 2 and
ASC-TRIAL-008. Every other recipe has an unresolved narrative prerequisite
(e.g., named mastery or encounter proof). Those recipes are explicitly
`unbound` and fail closed rather than allowing resource-only bypasses.
Do not flip them to `bound` until canonical achievement IDs and authoritative
award paths are implemented, audited, and validated. This is an intentional
playability limitation, not a completed end-to-end crafting path.

Place `aeonfall_axiom_refinement_button_device` with a real UEFN button at
each station. Configure `RecipeId` and exact `StationId` from the generated
contract. The server checks both fields, profile state, trial flags, balances,
and persistence acknowledgement. The button is not an anti-cheat substitute
for correct editor placement and physical proximity; verify these in a
multiplayer Launch Session. Repeated crafts are intentional for stackable
intermediate materials and each requires a fresh complete debit.

Regenerate with `python tools/build_axiom_refinement_registry.py`, verify
with `--check`, and run `python -m unittest tests.test_axiom_refinement`.
The existing 68,420 raw-acquisition graph and canonical IDs are unchanged.
Source validation does **not** establish native Verse compilation, physical
station bindings, gameplay animations/VFX/audio, or multiplayer correctness.
