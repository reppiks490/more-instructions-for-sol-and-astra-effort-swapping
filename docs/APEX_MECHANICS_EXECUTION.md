# AEONFALL — God / Absolute apex execution contracts

The canonical identities remain in `content/transcendent/ascended_forms.json`; the binding inventory remains in `ascended_form_adapter_bindings.json`. The new `ascended_ability_mechanics.json` specifies ten **different** bounded mechanical behaviors without adding abilities. All cue IDs are **planned cues**, not shipped Unreal assets. No experimental Ability API dependency is introduced.

## Fail-closed integration boundary

`aeonfall_trigger_ability_adapter_device` is a generic fire-and-report trigger. It cannot prove a boss immunity check, position/navmesh check, whitelisted objective ownership, spawned-object quota, or effect lifetime. Consequently it now **rejects any ability with nonempty `RequiredTransformationId`**, returning `apex_requires_specialized_preflight` before triggering a device. This covers God, Absolute, and Transcendent Zero. It prevents an unverified graph from reporting a successful apex effect and consuming canonical resources. The existing canonical adapter bindings remain `binding_required`; they do **not** claim functional physical effects.

A future specialized adapter must check the exact registered owner/target and transformation identity, finite range and geometry, encounter-controlled immunity and objective permissions, per-owner/per-region live-instance quotas, lifetime cleanup, and deterministic one-use-per-form budgets **before** it emits a successful adapter result. Rejections must not consume resources. The generic adapter must never be toggled to bypass these checks. A transformation ends all its pending/active ability requests; late callbacks must be ignored.

## Complete generic-adapter perimeter

The shared Verse predicate `AEONFALLRequiresSpecializedTransformationPreflight` checks **three independent signals**: exact `RequiredTransformationId`, `RequiresTransformationContext`, and `TransformationOnly` resource policy. This prevents a legacy or malformed definition with an empty transformation ID from escaping the apex boundary. The generic trigger, status-batch and composite status+trigger adapters now reject transformed requests **before any status application or physical trigger**. The native prop-spawn adapter and Royal Scent challenge adapter also reject transformed definitions before reservation/spawn or mark/challenge creation. A rejected request reports failure (or fails preflight) so canonical charges, cooldown and class resources are not committed.

This is defense in depth, **not** a specialized God/Absolute/Zero implementation. Every actual apex effect still requires a separate adapter with authoritative immunity, placement, instance/lifetime, use-per-form, and encounter ownership checks. Editor-side `RequireRegisteredTarget` flags are not substitutes for these checks. Source guard tests protect this perimeter; only a native UEFN compile and multiplayer Launch Session can prove engine behavior.

## Distinct mechanic / counterplay language

God uses storm territory, gravity pressure, self recovery, ally shielding, and short fortitude. Absolute uses a slow window, temporary construct suppression, one whitelisted objective-rule change, validated traversal, and a combination domain only when the encounter authorizes it. Each has its own telegraph/impact/exit VFX, two-stage audio and actionable counterplay recorded in the JSON manifest. No permanent world edit, global rewind, universal invulnerability, unrestricted boss control, or arbitrary teleport is permitted.

Class synergy explicitly references the first-slice `CLS-006` Sepulchral Sovereign and `CLS-007` Beast-Crown. It changes tactical placement, information and cover; it does not multiply apex budgets or create a back door to class resources. The Axiom Heart and ten-trial/Choosing prerequisites remain separate from these temporary forms; neither a crafted Heart nor a trigger graph grants Transcendent Zero.

## UEFN acceptance path

Implement dedicated Verse/Creative/Scene Graph adapters behind the existing canonical IDs; bind actual VFX/audio/animation in the editor; test success, rejection, simultaneous requests, immune boss states, invalid destination, phase teardown, respawn, and multiplayer. The mechanics JSON's `uses_per_form=1` is a **required adapter budget**, not yet enforced by a physical apex adapter. Do not change `implementation_state` to implemented until editor compile and Fortnite Launch Session evidence exists. Run `python tools/validate_apex_mechanics.py` and the unit mutation tests for source-level checks; neither substitutes for native validation.
