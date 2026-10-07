using { /Verse.org/Simulation }

# One material requirement used by recipes and shop transactions.
aeonfall_material_cost := class:
    MaterialId:string = ""
    Amount:int = 0

# Persistent sparse material ledger facade.
# Material IDs are canonical strings (MAT-###) supplied by the content registry.
aeonfall_material_ledger := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    # Missing ledger keys are intentionally treated as zero so first acquisition works.
    GetCount(Agent:agent, MaterialId:string)<transacts>:int=
        var Result:int = 0
        if:
            Profile := ProfileService.GetProfile[Agent]
            Stored := Profile.MaterialLedger[MaterialId]
        then:
            set Result = Stored
        Result

    SetCount(Agent:agent, MaterialId:string, Count:int)<transacts>:void=
        ProfileService.SetMaterialCount(Agent, MaterialId, Count)

    Add(Agent:agent, MaterialId:string, Amount:int)<transacts>:void=
        if:
            Amount > 0
        then:
            Current := GetCount(Agent, MaterialId)
            SetCount(Agent, MaterialId, Current + Amount)

    Spend(Agent:agent, MaterialId:string, Amount:int)<decides><transacts>:void=
        Amount > 0
        Current := GetCount(Agent, MaterialId)
        Current >= Amount
        SetCount(Agent, MaterialId, Current - Amount)


    # Checks a whole cost vector after coalescing duplicate material IDs.
    CanAffordMany(Agent:agent, Costs:[]aeonfall_material_cost)<transacts>:logic=
        var RequiredTotals:[string]int = map{}
        var Valid:logic = true

        for (Cost : Costs):
            if:
                Cost.Amount > 0
            then:
                if:
                    Existing := RequiredTotals[Cost.MaterialId]
                then:
                    if:
                        set RequiredTotals[Cost.MaterialId] = Existing + Cost.Amount
                    then:
                    else:
                        set Valid = false
                else:
                    if:
                        set RequiredTotals[Cost.MaterialId] = Cost.Amount
                    then:
                    else:
                        set Valid = false
            else:
                set Valid = false

        if (Valid?):
            for (MaterialId -> RequiredAmount : RequiredTotals):
                Current := GetCount(Agent, MaterialId)
                if (Current < RequiredAmount):
                    set Valid = false

        Valid

    # Applies a whole material spend to a candidate ledger, then persists once.
    # Nothing is written if any required material is missing.
    TrySpendMany(Agent:agent, Costs:[]aeonfall_material_cost)<transacts>:logic=
        if:
            Profile := ProfileService.GetProfile[Agent]
        then:
            var RequiredTotals:[string]int = map{}
            var UpdatedLedger:[string]int = Profile.MaterialLedger
            var Valid:logic = true

            for (Cost : Costs):
                if:
                    Cost.Amount > 0
                then:
                    if:
                        Existing := RequiredTotals[Cost.MaterialId]
                    then:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Existing + Cost.Amount
                        then:
                        else:
                            set Valid = false
                    else:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Cost.Amount
                        then:
                        else:
                            set Valid = false
                else:
                    set Valid = false

            if (Valid?):
                for (MaterialId -> RequiredAmount : RequiredTotals):
                    var Current:int = 0
                    if:
                        Stored := UpdatedLedger[MaterialId]
                    then:
                        set Current = Stored

                    if:
                        Current >= RequiredAmount
                    then:
                        if:
                            set UpdatedLedger[MaterialId] = Current - RequiredAmount
                        then:
                        else:
                            set Valid = false
                    else:
                        set Valid = false

            if (Valid?):
                ProfileService.SetMaterialLedger(Agent, UpdatedLedger)
                return true

        false
