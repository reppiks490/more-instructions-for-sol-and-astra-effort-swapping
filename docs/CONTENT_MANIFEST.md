# AEONFALL — Content Manifest

## Canonical IDs
- WPN-### weapons
- ARM-### armor
- REL-### relics/artifacts
- MON-### monsters
- WLD-### wildlife/tameables
- NPC-### hireable/major NPCs
- FAC-### factions
- BOS-### bosses
- VEH-### vehicles
- SKL-### skills
- CLS-### classes
- MAT-### crafting materials
- EVT-### world events
- POI-### locations

IDs are permanent and never recycled.

## Initial 800-Entity Allocation
| Family | Target |
|---|---:|
| Weapons | 180 |
| Armor / major set pieces | 120 |
| Monsters / demons / eldritch / necromantic entities | 170 |
| Wildlife / tameables | 60 |
| Hireable / major NPCs | 60 |
| Bosses / mini / super / mythic / world | 80 |
| Relics / artifacts | 45 |
| Vehicles / advanced variants | 25 |
| Classes / major skill entities | 30 |
| World-event / special map-effect entities | 30 |
| **Total** | **800** |

Crafting materials, quest objects, and ordinary consumables are tracked separately and do not count toward the 800.

## Minimum Hireable Expansion
- Epic: 12+
- Legendary: 6+
- Mythic: 5+
- Exotic: 3+
- God: 2+
- Absolute / Transcendent-associated characters: governed by endgame rules

## Status Pipeline
concept → specified → prototype → implemented → vfx_ready → animation_ready → tested → production

## Required High-Tier Definition Fields
Every high-tier entity must define visual silhouette, lore identity, combat role, core mechanic, signature mechanic, counterplay, progression/evolution, animation package, VFX package, audio cues, loot/crafting links, performance budget, and Verse/UEFN dependencies.
