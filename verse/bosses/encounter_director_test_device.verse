using { /Fortnite.com/Devices }
using { /Verse.org/Diagnostics }
using { /Verse.org/Simulation }

# Disabled in production. These assertions execute the actual Verse gate logic
# only when this device is compiled and run in a UEFN Launch Session.
aeonfall_encounter_director_test_device := class(creative_device):
    @editable
    Enabled:logic = false
    var Checks:int = 0
    var Failures:int = 0

    Check(Label:string, Passed:logic):void=
        set Checks += 1
        if (not Passed?):
            set Failures += 1
            Print("ENCOUNTER DIRECTOR FAIL: {Label}")

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        if (Definition := GetSlice001EncounterDirector["BOS-005"]):
            Mason := aeonfall_encounter_director_runtime{Definition := Definition}
            Check("mason starts", Mason.Start())
            Check("duplicate start rejected", logic{not Mason.Start()?})
            Check("unknown objective rejected", logic{not Mason.RecordObjective(0, "unknown")?})
            Check("future objective rejected", logic{not Mason.RecordObjective(2, "OBJ-BOS005-PUNISH-WHISTLE")?})
            Check("premature death signal rejected", logic{not Mason.RecordSignal(0, "SIG-BOS005-DEFEATED")?})
            Check("unknown weakpoint rejected", logic{not Mason.RecordWeakPoint(0, "unknown")?})
            Check("weakpoint accepted", Mason.RecordWeakPoint(0, "WP-BOS005-RED-HAND"))
            Check("weakpoint replay rejected", logic{not Mason.RecordWeakPoint(0, "WP-BOS005-RED-HAND")?})
            Check("weakpoint cannot bypass phase", logic{not Mason.CanResolvePhase()?})
            Check("unresolved phase cannot advance", logic{not Mason.Advance()?})
            Check("corpse denial accepted", Mason.RecordObjective(0, "OBJ-BOS005-DENY-CORPSES"))
            Check("objective replay rejected", logic{not Mason.RecordObjective(0, "OBJ-BOS005-DENY-CORPSES")?})
            Check("objective alternative resolves", Mason.CanResolvePhase())
            Check("sequential advance", Mason.Advance())
            Check("outgoing phase input rejected", logic{not Mason.RecordObjective(0, "OBJ-BOS005-DENY-CORPSES")?})
            Check("first anchor", Mason.RecordObjective(1, "OBJ-BOS005-BREAK-STAIR-A"))
            Check("second anchor", Mason.RecordObjective(1, "OBJ-BOS005-BREAK-STAIR-B"))
            Check("two anchors insufficient", logic{not Mason.CanResolvePhase()?})
            Check("third anchor", Mason.RecordObjective(1, "OBJ-BOS005-BREAK-STAIR-C"))
            Check("three anchors resolve", Mason.CanResolvePhase())
            Check("mason enters final", Mason.Advance())
            Check("repeated authored weakpoint accepted in new phase", Mason.RecordWeakPoint(2, "WP-BOS005-RED-HAND"))
            Check("final mechanic accepted", Mason.RecordObjective(2, "OBJ-BOS005-PUNISH-WHISTLE"))
            Check("final objective cannot award victory", logic{not Mason.CanComplete()?})
            Check("final death accepted", Mason.RecordSignal(2, "SIG-BOS005-DEFEATED"))
            Check("final death enables completion", Mason.CanComplete())
            Check("final cannot advance out of bounds", logic{not Mason.Advance()?})
            Mason.Stop()
            Check("terminal input rejected", logic{not Mason.RecordSignal(2, "SIG-BOS005-DEFEATED")?})
            Check("restart supported", Mason.Start())
            Check("restart resets phase and counters", logic{Mason.PhaseIndex = 0, not Mason.CanResolvePhase()?})
            Check("health alternative accepted", Mason.RecordSignal(0, "SIG-BOS005-HEALTH-70"))
            Check("health alternative resolves", Mason.CanResolvePhase())
            Mason.Stop()
        else:
            Check("mason definition exists", false)

        if (Definition := GetSlice001EncounterDirector["BOS-006"]):
            Saint := aeonfall_encounter_director_runtime{Definition := Definition}
            Check("saint starts", Saint.Start())
            Check("saint health threshold", Saint.RecordSignal(0, "SIG-BOS006-HEALTH-70"))
            Check("saint requires failed bite as well", logic{not Saint.CanResolvePhase()?})
            Check("saint failed bite", Saint.RecordObjective(0, "OBJ-BOS006-BAIT-POUNCE"))
            Check("saint AND gate resolves", Saint.CanResolvePhase())
            Check("saint advances", Saint.Advance())
            Check("halo alternative", Saint.RecordObjective(1, "OBJ-BOS006-BREAK-STOLEN-HALO"))
            Check("halo OR gate resolves", Saint.CanResolvePhase())
            Saint.Stop()
        else:
            Check("saint definition exists", false)

        if (Definition := GetSlice001EncounterDirector["BOS-011"]):
            King := aeonfall_encounter_director_runtime{Definition := Definition}
            Check("king starts", King.Start())
            Check("treasury alternative", King.RecordSignal(0, "SIG-BOS011-TREASURY-THRESHOLD"))
            Check("king enters treasury", King.Advance())
            Check("treasury anchor A", King.RecordObjective(1, "OBJ-BOS011-BREAK-TREASURY-A"))
            Check("one treasury anchor insufficient", logic{not King.CanResolvePhase()?})
            Check("treasury anchor B", King.RecordObjective(1, "OBJ-BOS011-BREAK-TREASURY-B"))
            Check("king enters decrees", King.Advance())
            Check("first decree", King.RecordObjective(2, "OBJ-BOS011-SOLVE-DECREES"))
            Check("second decree", King.RecordObjective(2, "OBJ-BOS011-SOLVE-DECREES"))
            Check("two decrees insufficient", logic{not King.CanResolvePhase()?})
            Check("third decree", King.RecordObjective(2, "OBJ-BOS011-SOLVE-DECREES"))
            Check("three decrees resolve", King.CanResolvePhase())
            Check("fourth decree rejected", logic{not King.RecordObjective(2, "OBJ-BOS011-SOLVE-DECREES")?})
            Check("king enters final", King.Advance())
            King.Stop()
        else:
            Check("king definition exists", false)

        if (Definition := GetSlice001EncounterDirector["EVT-011"]):
            Market := aeonfall_encounter_director_runtime{Definition := Definition}
            Check("market starts", Market.Start())
            Check("future market signal rejected", logic{not Market.RecordSignal(0, "SIG-EVT011-LEDGER-DESTROYED")?})
            Check("first lot", Market.RecordSignal(0, "SIG-EVT011-LOT-RESOLVED"))
            Check("second lot", Market.RecordSignal(0, "SIG-EVT011-LOT-RESOLVED"))
            Check("two lots insufficient", logic{not Market.CanResolvePhase()?})
            Check("third lot", Market.RecordSignal(0, "SIG-EVT011-LOT-RESOLVED"))
            Check("fourth lot rejected", logic{not Market.RecordSignal(0, "SIG-EVT011-LOT-RESOLVED")?})
            Check("market enters auction", Market.Advance())
            Check("influence threshold", Market.RecordSignal(1, "SIG-EVT011-INFLUENCE-RESOLVED"))
            Check("market enters clean ledger", Market.Advance())
            Check("auction alternative", Market.RecordSignal(2, "SIG-EVT011-AUCTION-RESOLVED"))
            Check("market enters crash", Market.Advance())
            Check("market requires ledger destruction", logic{not Market.CanComplete()?})
            Check("ledger destruction", Market.RecordSignal(3, "SIG-EVT011-LEDGER-DESTROYED"))
            Check("market can complete", Market.CanComplete())
            Market.Stop()
            Check("failure stops ingress", logic{not Market.RecordObjective(3, "OBJ-EVT011-EXTRACT-REWARDS")?})
        else:
            Check("market definition exists", false)
        Check("unknown encounter lookup fails", logic{not GetSlice001EncounterDirector["unknown"]})
        Print("ENCOUNTER DIRECTOR RESULT: {Checks} checks, {Failures} failures")
