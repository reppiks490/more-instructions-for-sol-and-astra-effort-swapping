# AEONFALL — Boss Framework

## Boss Hierarchy

### Mini Boss
Short encounter, one signature mechanic, one escalation state.

### Boss
Dedicated arena/route, multiple mechanics, at least two phases.

### Super Boss
Optional high-difficulty encounter with mechanics that demand role coordination and mastery.

### Mythic Boss
World-event-grade presentation, multi-region or multi-objective phases, unique crafting/progression links.

### God-Class Boss
A world landmark or regional catastrophe. Encounter changes multiple systems and may require several simultaneous teams/objectives.

### Absolute-Class Encounter
Not merely a larger health pool. Local encounter rules are temporarily replaced by authored doctrine mechanics.

### Transcendent Trial Entity
Used only for Zero Candidate/Choosing content and protected from ordinary farming.

## Distributed Colossus Architecture
For skyscraper/continent-scale creatures:

### Visual Shell
Low-cost distant representation visible across regions.

### Encounter Brain
Authoritative phase state, health model, victory/failure state.

### Body Regions
Separate encounter sectors such as:
- head/crown
- arms
- armor cities
- spine
- heart vents
- internal organs
- locomotion anchors

### Sector Controllers
Each region manages:
- local weak points
- hazards
- adds
- traversal
- destruction state
- local presentation

### Shared Phase Logic
Sector success contributes to global thresholds.

No single squad should be able to trivialize a continent-class encounter by camping one weak point.

## Failure Design
Failure should usually:
- change next phase difficulty,
- consume resources,
- close a damage window,
- mutate encounter state,

rather than immediately reset an hour-long event.

## Team Scaling
Scaling may adjust:
- number of simultaneous objectives
- add density
- weak-point uptime
- support resources
- damage requirements

Avoid simply multiplying health by player count.

## Boss Reward Rule
Bosses should unlock systems:
- recipes
- materials
- class mastery
- faction changes
- traversal
- new event states
- Axiom components

A boss should feel consequential even after its loot becomes familiar.
