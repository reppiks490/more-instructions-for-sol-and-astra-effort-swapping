using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_taming.json

Slice001TamingDefinitions:[]aeonfall_taming_definition = array{
    aeonfall_taming_definition{
        SpeciesId := "WLD-001",
        DisplayName := "Mirrorhorn Hart",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.Approach, aeonfall_taming_step_kind.Calm, aeonfall_taming_step_kind.Track},
        MaxChallengeSeconds := 55.0,
        FailureEventId := "taming.failure.mirrorhorn_enraged",
        SuccessEventId := "taming.success.mirrorhorn"
    },
    aeonfall_taming_definition{
        SpeciesId := "WLD-006",
        DisplayName := "Marrow Hound",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.DenyCorpse, aeonfall_taming_step_kind.Evade, aeonfall_taming_step_kind.Calm},
        MaxChallengeSeconds := 50.0,
        FailureEventId := "taming.failure.marrow_hound_enraged",
        SuccessEventId := "taming.success.marrow_hound"
    },
    aeonfall_taming_definition{
        SpeciesId := "WLD-007",
        DisplayName := "Tombshell Beetle",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.Feed, aeonfall_taming_step_kind.Protect, aeonfall_taming_step_kind.Calm},
        MaxChallengeSeconds := 70.0,
        FailureEventId := "taming.failure.tombshell_withdraws",
        SuccessEventId := "taming.success.tombshell"
    },
    aeonfall_taming_definition{
        SpeciesId := "WLD-008",
        DisplayName := "Ossuary Crane",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.Track, aeonfall_taming_step_kind.Approach, aeonfall_taming_step_kind.Calm},
        MaxChallengeSeconds := 60.0,
        FailureEventId := "taming.failure.ossuary_crane_flees",
        SuccessEventId := "taming.success.ossuary_crane"
    },
    aeonfall_taming_definition{
        SpeciesId := "WLD-009",
        DisplayName := "Graveburrow Mole",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.Track, aeonfall_taming_step_kind.Feed, aeonfall_taming_step_kind.Protect},
        MaxChallengeSeconds := 65.0,
        FailureEventId := "taming.failure.graveburrow_retreats",
        SuccessEventId := "taming.success.graveburrow"
    },
    aeonfall_taming_definition{
        SpeciesId := "WLD-010",
        DisplayName := "Reliquary Stag",
        RequiredClassId := "CLS-007",
        AbilityId := "ABL-003",
        Steps := array{aeonfall_taming_step_kind.Approach, aeonfall_taming_step_kind.Protect, aeonfall_taming_step_kind.Calm, aeonfall_taming_step_kind.Track},
        MaxChallengeSeconds := 85.0,
        FailureEventId := "taming.failure.reliquary_stag_rampage",
        SuccessEventId := "taming.success.reliquary_stag"
    },
}

aeonfall_slice_001_taming_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : Slice001TamingDefinitions):
            Registered := GetAEONFALLTamingRegistry().Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.taming_registration_failed",
                        SourceId := Definition.SpeciesId
                    }
                )
