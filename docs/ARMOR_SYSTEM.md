# AEONFALL — Armor and Equipment Contract

## Platform Boundary
AEONFALL armor is implemented as gameplay equipment, not as an assumed unrestricted replacement for Fortnite character cosmetics.

Current Epic custom-item systems support item entities that can be equipped and unequipped, stored in custom inventories, and extended with Verse components.

Official references:
- https://dev.epicgames.com/documentation/fortnite/item-component-in-fortnite
- https://dev.epicgames.com/documentation/en-us/fortnite/inventory-component-in-fortnite

Full-body cosmetic replacement, arbitrary skeletal attachments, and transformation presentation must be validated in the actual UEFN project before being promoted from specification to implementation.

## Equipment Model
Target gameplay slots:
- helm
- chest
- gauntlets
- legs
- boots
- mantle
- relic
- class core

Not every visual set must occupy every slot. Major armor catalog entries may represent:
- one signature piece,
- a multi-piece set,
- a transformation shell,
- or a class-specific equipment package.

## Runtime Responsibilities
The armor runtime owns:
- equipped canonical IDs
- tier
- set membership
- passive modifiers
- triggered mechanics
- cooldowns
- transformation eligibility
- mutually exclusive effects
- encounter-safe caps
- VFX/animation presentation hooks

## Set Bonus Philosophy
Set bonuses must add mechanics rather than only percentages.

Example progression:
- 2-piece: utility identity
- 3-piece: resource loop
- 4-piece: active mechanic
- 5-piece: encounter interaction
- full set: transformation/signature ability

## Rarity Doctrine
Epic:
- one strong gameplay identity
- readable VFX accent
- one signature trigger

Legendary:
- interacting mechanics
- distinct animation/VFX state
- stronger acquisition requirement

Mythic:
- encounter-linked mechanics
- conditional transformation or active state
- custom HUD feedback

Exotic:
- unusual rule-bending specialization
- intentionally narrow but dramatic identity

God:
- bounded domain/command mechanics
- cinematic activation
- world-boss or ascension provenance

Absolute:
- temporary local-doctrine alteration using supported authored systems
- strict duration and protected-system exclusions

Transcendent Zero:
- not ordinary equipment progression
- any armor manifestation is tied to the temporary Transcendent state and its Authorities

## Monetization Design Flag
The current game-design rule is:
- Epic tier is broadly earnable/unlocked.
- Legendary and above may require the official premium entitlement layer plus their in-world acquisition conditions.
- Development/creator testing may use an explicit test entitlement path only where Epic-supported workflows allow it.
- No hidden payment bypass is part of the production design.

## Performance
Armor presentation must declare:
- equipped-instance VFX band
- distance fallback
- transformation cleanup
- attachment count
- animation-layer cost
- replication requirements

High-tier armor may look extravagant while still reducing to lightweight distant presentation.
