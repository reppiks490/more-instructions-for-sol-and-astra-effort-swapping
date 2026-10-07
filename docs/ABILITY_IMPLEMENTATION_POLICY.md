# AEONFALL — Ability Implementation Policy

## Decision
AEONFALL core gameplay does **not** depend on Fortnite's Experimental Ability System or Template Abilities for the production path.

Epic's current documentation marks the Ability System and Template Abilities as Experimental and states that projects using them cannot currently be published. AEONFALL therefore keeps ability identity, targeting, resource state, cooldowns, statuses, encounter rules, and presentation bindings in its own runtime contracts.

## Production Path
Production abilities are assembled from publishable project-bound mechanisms available in the target UEFN release, such as:
- Verse gameplay services;
- Creative devices;
- custom weapon/item components where publication is supported;
- Character Definitions / NPC behavior;
- Scene Graph components and prefabs where supported;
- project-bound VFX, audio, animation, collision, and projectile adapters.

The core runtime only decides **whether** an ability may activate, spends its resource, emits canonical events, and tracks lifetime/state. A binding adapter performs the actual Fortnite/Scene Graph/device effect.

## Experimental Adapter
A future `experimental_ability_adapter` may bridge canonical AEONFALL abilities into Epic's Ability API after Epic makes that path publishable. No persistent data, canonical ID, class design, boss logic, or progression system may depend on that adapter.

## Rule
If an Epic feature is Experimental or explicitly unpublishable, it may be prototyped in an isolated adapter but cannot become a required dependency for the production island.
