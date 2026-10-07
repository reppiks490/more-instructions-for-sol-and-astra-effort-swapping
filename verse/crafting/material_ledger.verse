using { /Verse.org/Simulation }

# Persistent sparse material ledger facade.
# Material IDs are canonical strings (MAT-###) supplied by the content registry.
aeonfall_material_ledger := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    GetCount(Agent:agent, MaterialId:string)<decides><transacts>:int=
        Profile := ProfileService.GetProfile[Agent]
        Count := Profile.MaterialLedger[MaterialId]
        Count

    SetCount(Agent:agent, MaterialId:string, Count:int):void=
        ProfileService.SetMaterialCount(Agent, MaterialId, Count)

    Add(Agent:agent, MaterialId:string, Amount:int):void=
        if:
            Amount > 0
            Current := GetCount[Agent, MaterialId]
        then:
            SetCount(Agent, MaterialId, Current + Amount)

    Spend(Agent:agent, MaterialId:string, Amount:int)<decides>:void=
        Amount > 0
        Current := GetCount[Agent, MaterialId]
        Current >= Amount
        SetCount(Agent, MaterialId, Current - Amount)
