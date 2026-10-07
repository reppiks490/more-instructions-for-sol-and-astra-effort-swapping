# AEONFALL class runtime contracts.

aeonfall_class_definition := class:
    ClassId:string = ""
    DisplayName:string = ""
    AbilityIds:[]string = array{}
    PassiveStatusIds:[]string = array{}
    ResourceId:string = ""
    MaxResource:int = 0
    BaseMaxCompanions:int = 0
    RequiredUnlockIds:[]string = array{}

aeonfall_class_runtime_state := class:
    ClassId:string = ""
    CurrentResource:int = 0
    MaxResource:int = 0
    AbilityIds:[]string = array{}
    Active:logic = false


aeonfall_class_resource_reservation := class:
    RequestId:string = ""
    OwnerKey:string = ""
    ClassId:string = ""
    Amount:int = 0
    HoldWhileActive:logic = false
