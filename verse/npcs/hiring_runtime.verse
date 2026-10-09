using { /Verse.org/Verse }
using { /Verse.org/Simulation }

# Hireable contract registry and recruitment runtime.
# First recruitment enforces authored gates. Once a hireable is permanently
# unlocked in the player profile, future session recruitment only needs a live
# NPC instance and available squad capacity.
aeonfall_hireable_registry := class():

    var Definitions:[string]aeonfall_companion_contract = map{}

    Register(Definition:aeonfall_companion_contract)<transacts>:logic=
        if:
            Definition.EntityId <> ""
            Definition.Kind = aeonfall_companion_kind.Hireable
            Definition.RequiredReputation >= 0
            set Definitions[Definition.EntityId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "hireable.definition_registered",
                    SourceId := Definition.EntityId,
                    TargetId := Definition.FactionId
                }
            )
            return true

        false

    Get(NpcId:string)<decides><transacts>:aeonfall_companion_contract=
        Definitions[NpcId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLHireableRegistrySessions:weak_map(session, aeonfall_hireable_registry) = map{}

GetAEONFALLHireableRegistry()<transacts>:aeonfall_hireable_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLHireableRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_hireable_registry{}
    if (set AEONFALLHireableRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLHireableRegistry in its session")

aeonfall_hiring_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    ReputationService:aeonfall_reputation_service = aeonfall_reputation_service{}

    MeetsFirstRecruitmentRequirements(
        OwnerKey:string,
        Definition:aeonfall_companion_contract
    )<transacts>:logic=
        if:
            OwnerAgent := GetAEONFALLActorRegistry().GetAgent[OwnerKey]
            OwnerPlayer := player[OwnerAgent]
            Profile := ProfileService.GetProfile[OwnerPlayer]
        then:
            if:
                Profile.HireableUnlockIds.Find[Definition.EntityId]
            then:
                return true

            var Eligible:logic = true

            if:
                Definition.FactionId <> ""
                Definition.RequiredReputation > 0
            then:
                if:
                    ReputationService.MeetsReputation[
                        OwnerPlayer,
                        Definition.FactionId,
                        Definition.RequiredReputation
                    ]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            for (UnlockId : Definition.RequiredUnlockIds):
                if:
                    Profile.UnlockedEntityIds.Find[UnlockId]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            for (BossId : Definition.RequiredBossIds):
                if:
                    Profile.CompletedBossIds.Find[BossId]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            for (EventId : Definition.RequiredWorldEventIds):
                if:
                    Profile.CompletedWorldEventIds.Find[EventId]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            return Eligible

        false

    TryHire(
        OwnerKey:string,
        NpcRuntimeKey:string
    )<transacts>:logic=
        if:
            NpcId := GetAEONFALLActorRegistry().GetCanonicalId[NpcRuntimeKey]
            Definition := GetAEONFALLHireableRegistry().Get[NpcId]
            MeetsFirstRecruitmentRequirements(OwnerKey, Definition)?
            GetAEONFALLCompanionRuntime().CanBind(
                OwnerKey,
                NpcRuntimeKey
            )?
        then:
            Hired := GetAEONFALLCompanionRuntime().BindHireable(
                OwnerKey,
                NpcRuntimeKey,
                NpcId
            )

            if (Hired?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "hireable.recruited",
                        SourceId := OwnerKey,
                        TargetId := NpcRuntimeKey,
                        ContextId := NpcId
                    }
                )
                return true

        false

AEONFALLHiringRuntime:aeonfall_hiring_runtime = aeonfall_hiring_runtime{}
