using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/transcendent/ascension_trials.json

AEONFALLAscensionTrialDefinitions:[]aeonfall_ascension_trial_definition = array{
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-001",
        Index := 1,
        DisplayName := "Severance",
        RequiredPreviousTrialId := "",
        ObjectiveIds := array{"OBJ-ASC001-ENTER-ALONE", "OBJ-ASC001-SURVIVE-THREE-ARCHETYPES", "OBJ-ASC001-CLEAR-WITHOUT-COMPANION"},
        TimeLimitSeconds := 1200.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := false,
        AllowsGodAbilities := false,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-002",
        Index := 2,
        DisplayName := "Collection",
        RequiredPreviousTrialId := "ASC-TRIAL-001",
        ObjectiveIds := array{"OBJ-ASC002-DEPOSIT-ECOLOGY-TRIBUTE", "OBJ-ASC002-DEPOSIT-FACTION-TRIBUTE", "OBJ-ASC002-DEPOSIT-BOSS-TRIBUTE", "OBJ-ASC002-DEPOSIT-WORLD-EVENT-TRIBUTE"},
        TimeLimitSeconds := 1800.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := true,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-003",
        Index := 3,
        DisplayName := "Hunter",
        RequiredPreviousTrialId := "ASC-TRIAL-002",
        ObjectiveIds := array{"OBJ-ASC003-HUNT-ELDRITCH", "OBJ-ASC003-HUNT-INFERNAL", "OBJ-ASC003-HUNT-COLOSSAL", "OBJ-ASC003-HUNT-NECROMANTIC", "OBJ-ASC003-HUNT-MYTHICAL"},
        TimeLimitSeconds := 2100.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := true,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-004",
        Index := 4,
        DisplayName := "Dominion",
        RequiredPreviousTrialId := "ASC-TRIAL-003",
        ObjectiveIds := array{"OBJ-ASC004-WIN-FACTION-CONFLICT", "OBJ-ASC004-STABILIZE-CORRUPTED-REGION", "OBJ-ASC004-HOLD-TWO-OBJECTIVES", "OBJ-ASC004-PRESERVE-NEUTRAL-POPULATION"},
        TimeLimitSeconds := 2400.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := true,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-005",
        Index := 5,
        DisplayName := "Memory",
        RequiredPreviousTrialId := "ASC-TRIAL-004",
        ObjectiveIds := array{"OBJ-ASC005-RECOGNIZE-THREE-REMIXED-BOSS-PATTERNS", "OBJ-ASC005-SOLVE-SEQUENCE-WITHOUT-HUD-PROMPT", "OBJ-ASC005-CLEAR-MEMORY-ECHO"},
        TimeLimitSeconds := 2400.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := false,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-006",
        Index := 6,
        DisplayName := "Genesis",
        RequiredPreviousTrialId := "ASC-TRIAL-005",
        ObjectiveIds := array{"OBJ-ASC006-BUILD-DEFENSIVE-NETWORK", "OBJ-ASC006-PROTECT-THREE-NODES", "OBJ-ASC006-REPAIR-BROKEN-LINK", "OBJ-ASC006-WIN-USING-CREATED-SPACE"},
        TimeLimitSeconds := 2700.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := true,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-007",
        Index := 7,
        DisplayName := "Restraint",
        RequiredPreviousTrialId := "ASC-TRIAL-006",
        ObjectiveIds := array{"OBJ-ASC007-SPARE-OPTIONAL-TARGET", "OBJ-ASC007-DISABLE-WITHOUT-ULTIMATE", "OBJ-ASC007-SAVE-ALLY-OBJECTIVE", "OBJ-ASC007-CLEAR-UNDER-POWER-CAP"},
        TimeLimitSeconds := 3000.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := true,
        AllowsGodAbilities := false,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-008",
        Index := 8,
        DisplayName := "Sacrifice",
        RequiredPreviousTrialId := "ASC-TRIAL-007",
        ObjectiveIds := array{"OBJ-ASC008-SEAL-HIGHEST-TIER-LOADOUT", "OBJ-ASC008-OFFER-SOVEREIGN-SIGILS", "OBJ-ASC008-CLEAR-WITH-REDUCED-SLOTS", "OBJ-ASC008-RECOVER-SEALED-RELICS"},
        TimeLimitSeconds := 3300.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := false,
        AllowsCompanions := false,
        AllowsGodAbilities := false,
        AllowsAbsoluteAbilities := false
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-009",
        Index := 9,
        DisplayName := "Convergence",
        RequiredPreviousTrialId := "ASC-TRIAL-008",
        ObjectiveIds := array{"OBJ-ASC009-STABILIZE-REGION-A", "OBJ-ASC009-STABILIZE-REGION-B", "OBJ-ASC009-STABILIZE-REGION-C", "OBJ-ASC009-DEFEAT-CONVERGENCE-WARDEN", "OBJ-ASC009-OPEN-AXIOM-FORGE"},
        TimeLimitSeconds := 3600.0,
        RequiresAxiomHeart := false,
        UnlocksAxiomForge := true,
        AllowsCompanions := true,
        AllowsGodAbilities := true,
        AllowsAbsoluteAbilities := true
    },
    aeonfall_ascension_trial_definition{
        TrialId := "ASC-TRIAL-010",
        Index := 10,
        DisplayName := "The Final Witness",
        RequiredPreviousTrialId := "ASC-TRIAL-009",
        ObjectiveIds := array{"OBJ-ASC010-WITNESS-FORCE", "OBJ-ASC010-WITNESS-SHELTER", "OBJ-ASC010-WITNESS-CHOICE", "OBJ-ASC010-WITNESS-COMPANY", "OBJ-ASC010-FINAL-WITNESS"},
        TimeLimitSeconds := 3600.0,
        RequiresAxiomHeart := true,
        UnlocksAxiomForge := false,
        AllowsCompanions := false,
        AllowsGodAbilities := false,
        AllowsAbsoluteAbilities := false
    },
}

aeonfall_ascension_trial_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : AEONFALLAscensionTrialDefinitions):
            Registered := GetAEONFALLAscensionTrialRegistry().Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.ascension_trial_registration_failed",
                        SourceId := Definition.TrialId
                    }
                )
