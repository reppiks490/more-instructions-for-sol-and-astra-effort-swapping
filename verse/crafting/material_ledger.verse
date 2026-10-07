using { /Verse.org/Simulation }

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

    SetCount(Agent:agent, MaterialId:string, Count:int):void=
        ProfileService.SetMaterialCount(Agent, MaterialId, Count)

    Add(Agent:agent, MaterialId:string, Amount:int):void=
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
