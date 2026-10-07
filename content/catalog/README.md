# AEONFALL Content Catalog

This directory contains the canonical authored definitions for major game entities.

## Rules
1. One permanent ID per major entity.
2. IDs are never reused.
3. All files must validate against `schemas/entity.schema.json`.
4. High-tier entities require meaningful mechanics, presentation, acquisition, and performance definitions.
5. Names alone do not count as authored content.
6. Custom crafting materials and minor quest objects may live under separate ledgers and do not count toward the 800-major-entity target.
7. Every entity progresses through:
   `concept → specified → prototype → implemented → vfx_ready → animation_ready → tested → production`.

## File Organization
- `weapons/`
- `armor/`
- `monsters/`
- `wildlife/`
- `npcs/`
- `bosses/`
- `relics/`
- `vehicles/`
- `skills/`
- `events/`

## Design Requirement
Higher rarity is not stat inflation. Legendary and above must gain increasingly distinctive:
- mechanics
- silhouettes
- animation language
- VFX language
- audio signatures
- acquisition challenges
- combat counterplay

## Performance Requirement
Every entity declares concurrency, VFX, replication, and streaming classes so high-spectacle content can be budgeted before implementation.
