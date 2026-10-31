using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_rewards.json

Slice001EncounterRewardDefinitions:[]aeonfall_encounter_reward_definition = array{
    aeonfall_encounter_reward_definition{
        EncounterId := "BOS-005",
        Kind := aeonfall_encounter_reward_kind.Boss,
        XP := 5000,
        MasteryPoints := 1,
        UnlockEntityIds := array{"WPN-122"},
        MaterialRewards := array{
            aeonfall_material_cost{
                MaterialId := "MAT-008",
                Amount := 30
            },
        },
        FirstClearOnly := true
    },
    aeonfall_encounter_reward_definition{
        EncounterId := "BOS-006",
        Kind := aeonfall_encounter_reward_kind.Boss,
        XP := 6500,
        MasteryPoints := 1,
        UnlockEntityIds := array{"WPN-126"},
        MaterialRewards := array{
            aeonfall_material_cost{
                MaterialId := "MAT-004",
                Amount := 40
            },
        },
        FirstClearOnly := true
    },
    aeonfall_encounter_reward_definition{
        EncounterId := "BOS-011",
        Kind := aeonfall_encounter_reward_kind.Boss,
        XP := 20000,
        MasteryPoints := 5,
        UnlockEntityIds := array{"WPN-124", "ARM-002"},
        MaterialRewards := array{
            aeonfall_material_cost{
                MaterialId := "MAT-011",
                Amount := 1
            },
            aeonfall_material_cost{
                MaterialId := "MAT-008",
                Amount := 100
            },
        },
        FirstClearOnly := true
    },
    aeonfall_encounter_reward_definition{
        EncounterId := "EVT-011",
        Kind := aeonfall_encounter_reward_kind.WorldEvent,
        XP := 8000,
        MasteryPoints := 2,
        UnlockEntityIds := array{},
        MaterialRewards := array{
            aeonfall_material_cost{
                MaterialId := "MAT-008",
                Amount := 50
            },
            aeonfall_material_cost{
                MaterialId := "MAT-003",
                Amount := 25
            },
        },
        FirstClearOnly := true
    },
}

aeonfall_slice_001_reward_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : Slice001EncounterRewardDefinitions):
            Registered := GetAEONFALLEncounterRewardRegistry().Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.encounter_reward_registration_failed",
                        SourceId := Definition.EncounterId
                    }
                )
