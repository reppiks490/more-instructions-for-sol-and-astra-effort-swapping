using { /Verse.org/Simulation }

# Session Hall of Ascendants.
#
# This is deliberately NOT presented as a global cross-session leaderboard.
# It derives prestige from the persistent profiles of players currently
# connected to the session and exposes stable data for project-bound UI.

aeonfall_hall_entry := class:
    OwnerKey:string = ""
    Level:int = 1
    AscensionRank:int = 0
    CompletedTrialCount:int = 0
    MasteredClassCount:int = 0
    BossClearCount:int = 0
    WorldEventClearCount:int = 0
    IsZeroCandidate:logic = false
    ChoosingComplete:logic = false
    TranscendentHistoryCount:int = 0
    AuthorityDepth:int = 0

aeonfall_hall_of_ascendants_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    var Entries:[string]aeonfall_hall_entry = map{}
    RefreshIntervalSeconds:float = 5.0
    var RefreshRemainingSeconds:float = 5.0

    GetAuthorityDepth(Profile:aeonfall_player_profile)<transacts>:int=
        if (Profile.TranscendentState <> 1):
            return 0

        History:int = Profile.TranscendentHistoryCount

        if (History >= 8):
            return 8
        if (History >= 5):
            return 7
        if (History >= 3):
            return 6
        if (History >= 1):
            return 5

        # Axiom Break, World Devourer, and Omnipresence are available
        # immediately after the Choosing at history 0.
        3

    RefreshIfReady(Agent:agent)<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Profile := ProfileService.GetProfile[Agent]
        then:
            Entry := aeonfall_hall_entry:
                OwnerKey := OwnerKey
                Level := Profile.Level
                AscensionRank := Profile.AscensionRank
                CompletedTrialCount := Profile.CompletedTrialIds.Length
                MasteredClassCount := Profile.MasteredClassIds.Length
                BossClearCount := Profile.CompletedBossIds.Length
                WorldEventClearCount := Profile.CompletedWorldEventIds.Length
                IsZeroCandidate := Profile.IsZeroCandidate
                ChoosingComplete := Profile.TranscendentState = 1
                TranscendentHistoryCount := Profile.TranscendentHistoryCount
                AuthorityDepth := GetAuthorityDepth(Profile)

            if:
                set Entries[OwnerKey] = Entry
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "hall.entry_refreshed",
                        SourceId := OwnerKey,
                        Amount := Entry.TranscendentHistoryCount,
                        ContextId := "{Entry.AuthorityDepth}"
                    }
                )
                return true

        false

    GetEntry(OwnerKey:string)<decides><transacts>:aeonfall_hall_entry=
        Entries[OwnerKey]

    RemoveOwner(OwnerKey:string)<transacts>:void=
        var Updated:[string]aeonfall_hall_entry = map{}

        for (StoredOwner -> Entry : Entries):
            if (StoredOwner <> OwnerKey):
                if:
                    set Updated[StoredOwner] = Entry
                then:
                    set Updated = Updated

        set Entries = Updated

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "hall.entry_removed",
                SourceId := OwnerKey
            }
        )

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        set RefreshRemainingSeconds =
            RefreshRemainingSeconds - DeltaSeconds

        if (RefreshRemainingSeconds > 0.0):
            return

        set RefreshRemainingSeconds = RefreshIntervalSeconds

        var OwnerKeys:[]string = array{}
        for (OwnerKey -> Entry : Entries):
            set OwnerKeys = OwnerKeys + array{OwnerKey}

        for (OwnerKey : OwnerKeys):
            if:
                Agent := AEONFALLActorRegistry.GetAgent[OwnerKey]
            then:
                Refreshed := RefreshIfReady(Agent)
                if (Refreshed?):
                    Refreshed = true

AEONFALLHallOfAscendants:aeonfall_hall_of_ascendants_runtime =
    aeonfall_hall_of_ascendants_runtime{}
