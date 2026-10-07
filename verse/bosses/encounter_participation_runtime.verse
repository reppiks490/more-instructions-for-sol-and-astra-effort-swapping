# Tracks human-player participation in boss/world-event encounter spaces.
# Runtime keys are used instead of player objects so teardown stays centralized
# in the actor registry.

aeonfall_encounter_participation_runtime := class():

    var ParticipantKeysByEncounter:[string][]string = map{}

    Add(
        EncounterId:string,
        RuntimeKey:string
    )<transacts>:logic=
        if:
            EncounterId <> ""
            RuntimeKey <> ""
        then:
            var Existing:[]string = array{}
            if:
                Stored := ParticipantKeysByEncounter[EncounterId]
            then:
                set Existing = Stored

            if:
                Existing.Find[RuntimeKey]
            then:
                return false

            if:
                set ParticipantKeysByEncounter[EncounterId] =
                    Existing + array{RuntimeKey}
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "encounter.participant_joined",
                        SourceId := EncounterId,
                        TargetId := RuntimeKey,
                        Amount := Existing.Length + 1
                    }
                )
                return true

        false

    Remove(
        EncounterId:string,
        RuntimeKey:string
    )<transacts>:logic=
        var Existing:[]string = array{}
        if:
            Stored := ParticipantKeysByEncounter[EncounterId]
        then:
            set Existing = Stored
        else:
            return false

        var Updated:[]string = array{}
        var Removed:logic = false

        for (Key : Existing):
            if (Key = RuntimeKey):
                set Removed = true
            else:
                set Updated = Updated + array{Key}

        if:
            Removed?
            set ParticipantKeysByEncounter[EncounterId] = Updated
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "encounter.participant_left",
                    SourceId := EncounterId,
                    TargetId := RuntimeKey,
                    Amount := Updated.Length
                }
            )
            return true

        false

    GetParticipants(
        EncounterId:string
    )<transacts>:[]string=
        if:
            Stored := ParticipantKeysByEncounter[EncounterId]
        then:
            Stored
        else:
            array{}

    ClearEncounter(EncounterId:string)<transacts>:void=
        if:
            set ParticipantKeysByEncounter[EncounterId] = array{}
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "encounter.participants_cleared",
                    SourceId := EncounterId
                }
            )

    RemoveRuntimeKey(RuntimeKey:string)<transacts>:void=
        var UpdatedMap:[string][]string = map{}

        for (EncounterId -> Existing : ParticipantKeysByEncounter):
            var Updated:[]string = array{}

            for (Key : Existing):
                if (Key <> RuntimeKey):
                    set Updated = Updated + array{Key}

            if:
                set UpdatedMap[EncounterId] = Updated
            then:
                set UpdatedMap = UpdatedMap

        set ParticipantKeysByEncounter = UpdatedMap

AEONFALLEncounterParticipation:aeonfall_encounter_participation_runtime =
    aeonfall_encounter_participation_runtime{}
