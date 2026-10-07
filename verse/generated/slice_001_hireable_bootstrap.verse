using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_hireables.json

Slice001HireableDefinitions:[]aeonfall_companion_contract = array{
    aeonfall_companion_contract{
        EntityId := "NPC-003",
        FactionId := "",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 0,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{"BOS-011"},
        RequiredWorldEventIds := array{"EVT-011"},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "HoldPosition", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-008",
        FactionId := "FAC-003",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 300,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "Flank", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-009",
        FactionId := "FAC-001",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 75,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "HoldPosition"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-010",
        FactionId := "FAC-004",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 75,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "HoldPosition", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-012",
        FactionId := "FAC-003",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 100,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "FocusTarget", "HoldPosition", "Flank", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-016",
        FactionId := "FAC-001",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 125,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "HoldPosition", "Flank"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-023",
        FactionId := "FAC-004",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 250,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{"BOS-011"},
        RequiredWorldEventIds := array{},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "HoldPosition", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
    aeonfall_companion_contract{
        EntityId := "NPC-051",
        FactionId := "FAC-007",
        Kind := aeonfall_companion_kind.Hireable,
        RequiredReputation := 200,
        RequiredUnlockIds := array{},
        RequiredBossIds := array{"BOS-011"},
        RequiredWorldEventIds := array{"EVT-011"},
        AbilityIds := array{},
        AllowedOrderIds := array{"Follow", "Guard", "FocusTarget", "HoldPosition", "Flank", "Retreat"},
        MaxSimultaneousPerPlayer := 1,
        CanEnterBossArenas := true,
        CanBeRevived := true
    },
}

aeonfall_slice_001_hireable_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : Slice001HireableDefinitions):
            Registered := AEONFALLHireableRegistry.Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.hireable_registration_failed",
                        SourceId := Definition.EntityId
                    }
                )
