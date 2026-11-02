# Living World — faction pressure and regional battle admission

## Two linked ecological consequences

REG-001 uses the existing canonical session-owned `FactionInfluence` map to
determine whether a faction is strong enough to launch a **new** invasion.
The optional `min_aggressor_influence` field is an integer in 0..100; zero
retains the prior hostility/corruption-only behavior. A nonzero requirement
reads the aggressor's own influence in an initialized region. Missing map
entries fail closed. Authored data rejects non-faction aggressors with nonzero
influence requirements.

| Invasion | Aggressor | Initial influence | Required |
| --- | --- | ---: | ---: |
| Null Cartel Extraction | FAC-002 | 35 | 30 |
| Iron Mercy Purge | FAC-004 | 25 | 20 |
| Synod Grave Experiment | FAC-007 | 15 | 15 |
| Grave Scavenger Surge | ECOL-NECROTIC | n/a | 0 |
| Devouring Moon Precursor | ECOL-GRAVEFEEDING | n/a | 0 |

The existing faction-conflict result changes winner influence by +20 and
loser influence by -10, using the canonical 0..100 clamp. Thus a territorial
loss can deny **future** faction invasions and a recovery can restore them,
without increasing monster stats or spawn counts. All existing hostility,
corruption, objective and single-invasion event-reservation rules still apply.

## Regional battle exclusivity

Invasion admission refuses an already-active faction conflict; faction-war
admission reciprocally refuses an active invasion or another faction conflict
in the same region. Direct conflict starts fail closed unless canonical region
state has been initialized. Both checks occur before activating state or
physical spawn requests. No additional coordinator, spawner or persistent
player record is introduced.

Neither corruption cleansing nor influence change retroactively cancels
an active encounter. Other regions retain independent admission. These guards
do **not** cover unrelated ambient/horde/boss/global-event spawners; physical
device ownership and aggregate streaming budgets remain project obligations.

## UEFN physical and multiplayer verification

Bind separate encounter-owned NPC Spawners and configure physical live limits
within the existing authored wave reserves; REG-001's invasion maximum remains
20 AI. Keep distant populations abstract and materialize only when players
and streaming cells make them relevant.

Launch Session acceptance, including two players in different cells:

1. Confirm faction invasion refusals at 29/30, 19/20 and 14/15 influence, and
   that failed admissions generate no spawn requests or event reservations.
2. Resolve a faction war, observe the existing +20/-10 transfer, and recheck
   later invasion eligibility. Changes must not terminate an active invasion.
3. Start two faction wars in one region; start an invasion during a war; start
   a war during an invasion. Only one regional battle should admit, in both
   event orders. Unrelated regions must still work.
4. Start a conflict before canonical region initialization and confirm there
   is no active state; repeat after initialization and after normal completion.
5. Inspect physical live AI, ownership leases, cell unload/re-entry, cleanup
   and measured frame/memory impact. No despawn should affect other owners.

Repository tests validate source and authored-data invariants only. They do
not prove native Verse compilation, project-bound bindings, streaming behavior
or multiplayer replication. Record those results in UEFN separately.
