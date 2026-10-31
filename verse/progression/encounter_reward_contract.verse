# Encounter completion reward definitions.

aeonfall_encounter_reward_kind := enum:
    Boss
    WorldEvent

aeonfall_encounter_reward_definition := class:
    EncounterId:string = ""
    Kind:aeonfall_encounter_reward_kind = aeonfall_encounter_reward_kind.Boss
    XP:int = 0
    MasteryPoints:int = 0
    UnlockEntityIds:[]string = array{}
    MaterialRewards:[]aeonfall_material_cost = array{}
    FirstClearOnly:logic = true
