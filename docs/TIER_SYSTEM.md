# AEONFALL — Tier System

## Ladder
Common → Uncommon → Rare → Epic → Legendary → Mythic → Exotic → God → Absolute → Transcendent Zero

## Rule
Higher tiers must add qualitative mechanics, animation/VFX language, acquisition complexity, and encounter influence—not just larger stats.

### Epic
Strong specialization plus one memorable signature mechanic.

### Legendary
Multiple interacting mechanics, bespoke VFX, stronger animation language, and a secondary state/combo behavior.

### Mythic
Encounter-defining behavior, cinematic signature abilities, unique acquisition, special UI/audio treatment.

### Exotic
Rule-bending specialization with unusual mechanical identity.

### God
World-scale thematic power, transformation/domain mechanics, elaborate VFX and animation packages.

Current runtime contract:
- permanent eligibility: `AscensionRank >= 1`;
- temporary form: **45 seconds**;
- session exhaustion: **120 seconds**;
- exact transformation ID: `ASCENDED_GOD`;
- canonical world-bending abilities: **Storm Genesis, Gravity Throne, Phoenix Ascension, Celestial Mandate, Titanheart Edict**.

### Absolute
Temporarily bends local encounter rules and must feel categorically above God-tier content.

Current runtime contract:
- permanent eligibility: `AscensionRank >= 2`;
- temporary form: **30 seconds**;
- session exhaustion: **240 seconds**;
- exact transformation ID: `ASCENDED_ABSOLUTE`;
- canonical abilities: **Chrono Rupture, Void Dominion, Axiom Dominion, Boundary Rewrite, Sovereign Paradox**.

### Transcendent Zero
Breaks the normal tier model. Access is not a normal purchase or level unlock.

Current runtime contract:
- the Choosing permanently unlocks activation eligibility but does not persist an active transformation;
- only one transformation may be active at once;
- each Authority has its own 16–30 second active window and 300–600 second session exhaustion;
- every Authority ability requires an exact `TRANSCENDENT_ZERO::AUTH-###` identity;
- ending a transformation cancels pending two-phase ability requests and terminates active Authority abilities;
- active/exhaustion state is session-only; progression and activation history remain persistent.

## Zero Candidate Qualification
Qualification may require max-level progression, extensive class mastery, God and Absolute progression, designated world-boss clears, major faction completion, hidden discoveries, ten escalating Ascension Trials, construction of the Axiom Heart, and completion of the Choosing.

## Axiom Heart
The final craft represents tens of thousands of acquired/refined components through nested refinement rather than one enormous physical inventory recipe.

Core ingredient families include Void Shards, Celestial Fragments, Titan Bone, Infernal Embers, Chrono Crystals, Leviathan Scales, Machine Cores, Necrotic Essences, Mythic Beast Hearts, Dimensional Catalysts, Boss Souls, World Event Cores, Sovereign Sigils, Absolute Relics, Primordial Keys, Reality Anchors, and the Seed of Zero.

## Canonical Transcendent Authorities
1. Axiom Break
2. World Devourer
3. Omnipresence
4. Causality Rejection
5. Genesis Engine
6. Pantheon
7. The Last Word
8. Reality Engine

Implementations must use supported UEFN/Verse mechanics and systemic simulation where literal engine-level modification is unavailable.


## Authority Progression
After the Choosing:
- history 0 → Axiom Break, World Devourer, Omnipresence
- history 1+ → adds Causality Rejection and Genesis Engine
- history 3+ → adds Pantheon
- history 5+ → adds The Last Word
- history 8+ → adds Reality Engine

Only a Transcendent Authority that reaches its full natural duration increments persistent `TranscendentHistoryCount`, exactly once. Manual cancel, teardown, or interrupted sessions do not advance Authority Depth. The Hall of Ascendants derives Authority Depth from these gates for players currently connected to the session.

## Runtime Safety Rule
God, Absolute, and Transcendent Zero share one authoritative transformation context and are mutually exclusive. Transformation-only abilities also carry an exact required transformation ID, preventing cross-tier or cross-Authority ability leakage.

The current repository declares and validates all God/Absolute/Transcendent adapter bindings, but physical UEFN effect graphs are still a production binding task. No effect is considered implemented until its project adapter succeeds in UEFN and passes Launch Session tests.
