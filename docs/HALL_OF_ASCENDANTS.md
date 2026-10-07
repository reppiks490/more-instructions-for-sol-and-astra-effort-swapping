# AEONFALL — Hall of Ascendants

The Hall of Ascendants is the prestige surface for AEONFALL's endgame progression.

## What is persistent
Each player's profile already persists:
- level and XP;
- class mastery;
- boss/world-event/trial completion;
- Zero Candidate state;
- Axiom Heart completion;
- Ascension Rank;
- Choosing completion through `TranscendentState = 1`;
- Transcendent activation history.

## What the Hall currently represents
The first runtime implementation is a **session Hall**. For each connected player it derives:
- Level
- Ascension Rank
- Trials completed
- Mastered classes
- Boss clears
- World-event clears
- Zero Candidate state
- Choosing completion
- Transcendent history
- Authority Depth

Authority Depth follows the current canonical gates:
- Choosing complete + history 0 → first 3 Authorities
- history 1+ → 5 Authorities
- history 3+ → 6
- history 5+ → 7
- history 8+ → all 8 including Reality Engine

## Boundary
This is not falsely described as a global leaderboard. UEFN project UI can render the current session Hall from this runtime. A true cross-session/global ranking should only be added if a supported persistent/backend leaderboard path is deliberately integrated and tested.
