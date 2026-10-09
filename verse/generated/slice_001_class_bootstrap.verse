using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_classes.json

Slice001ClassDefinitions:[]aeonfall_class_definition = array{
    aeonfall_class_definition{
        ClassId := "CLS-006",
        DisplayName := "Sepulchral Sovereign",
        AbilityIds := array{"ABL-001", "ABL-002"},
        PassiveStatusIds := array{},
        ResourceId := "corpse_charge",
        MaxResource := 100,
        BaseMaxCompanions := 2,
        RequiredUnlockIds := array{}
    },
    aeonfall_class_definition{
        ClassId := "CLS-007",
        DisplayName := "Beast-Crown",
        AbilityIds := array{"ABL-003"},
        PassiveStatusIds := array{},
        ResourceId := "crown_bond",
        MaxResource := 3,
        BaseMaxCompanions := 3,
        RequiredUnlockIds := array{}
    },
}

aeonfall_slice_001_class_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : Slice001ClassDefinitions):
            Registered := GetAEONFALLClassRegistry().Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.class_registration_failed",
                        SourceId := Definition.ClassId
                    }
                )
