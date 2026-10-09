using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Authoritative corpse allocation and consumption. No suspension between check
# and commit. Range/navigation and physical mutations belong to the adapter.
aeonfall_horde_runtime := class():
    Policy:aeonfall_horde_policy = aeonfall_horde_policy{}
    var Brood:[string]aeonfall_horde_brood = map{}
    var Corpses:[int]aeonfall_horde_corpse = map{}
    var RegionalBiomass:[string]int = map{}
    var ApexEventOpen:[string]logic = map{}
    var NextCorpseId:int = 0

    ValidPolicy()<transacts>:logic=
        if:
            Policy.MaxBrood > 0
            Policy.MaxBrood <= 128
            Policy.MaxCorpses > 0
            Policy.MaxCorpses <= 128
            Policy.CorpseLifetimeSeconds > 0.0
            Policy.GorgedBiomass > 0
            Policy.RemadeBiomass > Policy.GorgedBiomass
            Policy.ApostateBiomass > Policy.RemadeBiomass
            Policy.CrownedBiomass > Policy.ApostateBiomass
            Policy.RegionalApexBiomass >= Policy.CrownedBiomass
        then:
            return true
        false

    RegisterBrood(ActorKey:string, RegionId:string)<transacts>:logic=
        if:
            ValidPolicy()?
            ActorKey <> ""
            RegionId <> ""
            not Brood[ActorKey]
            Brood.Length < Policy.MaxBrood
            RegisterRegion(RegionId)?
            set Brood[ActorKey] = aeonfall_horde_brood{ActorKey := ActorKey, RegionId := RegionId}
        then:
            return true
        false

    RegisterRegion(RegionId:string)<transacts>:logic=
        if (RegionId = "" or not ValidPolicy()? ):
            return false
        if (RegionalBiomass[RegionId]):
            return true
        if:
            RegionalBiomass.Length < Policy.MaxBrood
            set RegionalBiomass[RegionId] = 0
            set ApexEventOpen[RegionId] = false
        then:
            return true
        false

    GetBrood(ActorKey:string)<decides><transacts>:aeonfall_horde_brood=
        Brood[ActorKey]

    GetCorpse(CorpseId:int)<decides><transacts>:aeonfall_horde_corpse=
        Corpses[CorpseId]

    AddCorpse(RegionId:string, Biomass:int, Trait:aeonfall_horde_trait)<transacts>:int=
        if:
            ValidPolicy()?
            RegionId <> ""
            RegionalBiomass[RegionId]
            Biomass > 0
            Biomass <= Policy.CrownedBiomass
            Corpses.Length < Policy.MaxCorpses
        then:
            Id := NextCorpseId + 1
            if:
                set Corpses[Id] = aeonfall_horde_corpse{
                    CorpseId := Id,
                    RegionId := RegionId,
                    Biomass := Biomass,
                    Trait := Trait,
                    RemainingSeconds := Policy.CorpseLifetimeSeconds
                }
            then:
                set NextCorpseId = Id
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "horde.corpse_created", TargetId := RegionId,
                    ContextId := "{Id}", Amount := Biomass
                })
                return Id
        0

    GetRegionalBiomass(RegionId:string)<transacts>:int=
        if (Amount := RegionalBiomass[RegionId]):
            return Amount
        0

    SetApexEvent(RegionId:string, Open:logic)<transacts>:logic=
        if:
            RegionId <> ""
            # Only registered regions may allocate session state.
            RegionalBiomass[RegionId]
            set ApexEventOpen[RegionId] = Open
        then:
            return true
        false

    HasRegion(RegionId:string)<transacts>:logic=
        for (Key -> Member : Brood):
            if (Member.RegionId = RegionId):
                return true
        false

    HasApex(RegionId:string)<transacts>:logic=
        for (Key -> Member : Brood):
            if (Member.RegionId = RegionId, Member.Tier = 5):
                return true
        false

    NextTier(Old:aeonfall_horde_brood, Biomass:int, RegionTotal:int)<transacts>:int=
        if (Old.Tier = 1, Biomass >= Policy.GorgedBiomass):
            return 2
        if (Old.Tier = 2, Biomass >= Policy.RemadeBiomass):
            return 3
        if (Old.Tier = 3, Biomass >= Policy.ApostateBiomass):
            return 4
        if:
            Old.Tier = 4
            Biomass >= Policy.CrownedBiomass
            RegionTotal >= Policy.RegionalApexBiomass
            Open := ApexEventOpen[Old.RegionId]
            Open?
            not HasApex(Old.RegionId)?
        then:
            return 5
        Old.Tier

    Feed(ActorKey:string, CorpseId:int)<transacts>:logic=
        if:
            Old := Brood[ActorKey]
            Corpse := Corpses[CorpseId]
            Corpse.RegionId = Old.RegionId
            Corpse.RemainingSeconds > 0.0
        then:
            Total := GetRegionalBiomass(Old.RegionId) + Corpse.Biomass
            Biomass := Old.Biomass + Corpse.Biomass
            Tier := NextTier(Old, Biomass, Total)
            var Primary:aeonfall_horde_trait = Old.PrimaryTrait
            var Secondary:aeonfall_horde_trait = Old.SecondaryTrait
            if (Tier >= 3, Corpse.Trait <> aeonfall_horde_trait.None):
                if (Primary = aeonfall_horde_trait.None):
                    set Primary = Corpse.Trait
                else if (Primary <> Corpse.Trait, Secondary = aeonfall_horde_trait.None):
                    set Secondary = Corpse.Trait
            Updated := aeonfall_horde_brood{
                ActorKey := Old.ActorKey, RegionId := Old.RegionId,
                Tier := Tier, Biomass := Biomass,
                PrimaryTrait := Primary, SecondaryTrait := Secondary
            }
            if:
                set Brood[ActorKey] = Updated
                set RegionalBiomass[Old.RegionId] = Total
            then:
                RemoveCorpse(CorpseId)
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "horde.fed", SourceId := ActorKey,
                    TargetId := Old.RegionId, ContextId := "{CorpseId}", Amount := Corpse.Biomass
                })
                if (Tier > Old.Tier):
                    AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                        EventType := "horde.evolved", SourceId := ActorKey,
                        TargetId := Old.RegionId, Amount := Tier
                    })
                return true
        false

    UseCorpse(RegionId:string, CorpseId:int, Use:aeonfall_corpse_use)<transacts>:logic=
        if:
            Corpse := Corpses[CorpseId]
            Corpse.RegionId = RegionId
            Corpse.RemainingSeconds > 0.0
        then:
            RemoveCorpse(CorpseId)
            Kind:string =
                if (Use = aeonfall_corpse_use.Burn):
                    "horde.corpse_burned"
                else if (Use = aeonfall_corpse_use.Sanctify):
                    "horde.corpse_sanctified"
                else if (Use = aeonfall_corpse_use.Harvest):
                    "horde.corpse_harvested"
                else:
                    "horde.corpse_necromancy"
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := Kind, TargetId := RegionId,
                ContextId := "{CorpseId}", Amount := Corpse.Biomass
            })
            return true
        false

    RemoveCorpse(CorpseId:int)<transacts>:void=
        var Kept:[int]aeonfall_horde_corpse = map{}
        for (Id -> Corpse : Corpses):
            if (Id <> CorpseId):
                if (set Kept[Id] = Corpse):
                    set Kept = Kept
        set Corpses = Kept

    RemoveBrood(ActorKey:string)<transacts>:void=
        var Kept:[string]aeonfall_horde_brood = map{}
        for (Key -> Member : Brood):
            if (Key <> ActorKey):
                if (set Kept[Key] = Member):
                    set Kept = Kept
        set Brood = Kept

    ClearRegion(RegionId:string)<transacts>:void=
        var KeptBrood:[string]aeonfall_horde_brood = map{}
        var KeptCorpses:[int]aeonfall_horde_corpse = map{}
        var KeptBiomass:[string]int = map{}
        var KeptEvents:[string]logic = map{}
        for (Key -> Member : Brood):
            if (Member.RegionId <> RegionId):
                if (set KeptBrood[Key] = Member):
                    set KeptBrood = KeptBrood
        for (Id -> Corpse : Corpses):
            if (Corpse.RegionId <> RegionId):
                if (set KeptCorpses[Id] = Corpse):
                    set KeptCorpses = KeptCorpses
        for (Key -> Amount : RegionalBiomass):
            if (Key <> RegionId):
                if (set KeptBiomass[Key] = Amount):
                    set KeptBiomass = KeptBiomass
        for (Key -> Open : ApexEventOpen):
            if (Key <> RegionId):
                if (set KeptEvents[Key] = Open):
                    set KeptEvents = KeptEvents
        set Brood = KeptBrood
        set Corpses = KeptCorpses
        set RegionalBiomass = KeptBiomass
        set ApexEventOpen = KeptEvents

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return
        var Kept:[int]aeonfall_horde_corpse = map{}
        for (Id -> Corpse : Corpses):
            Remaining := Corpse.RemainingSeconds - DeltaSeconds
            if (Remaining > 0.0):
                if (set Kept[Id] = aeonfall_horde_corpse{
                    CorpseId := Id, RegionId := Corpse.RegionId,
                    Biomass := Corpse.Biomass, Trait := Corpse.Trait,
                    RemainingSeconds := Remaining
                }):
                    set Kept = Kept
            else:
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "horde.corpse_expired", TargetId := Corpse.RegionId,
                    ContextId := "{Id}"
                })
        set Corpses = Kept

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLHordeRuntimeSessions:weak_map(session, aeonfall_horde_runtime) = map{}

GetAEONFALLHordeRuntime()<transacts>:aeonfall_horde_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLHordeRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_horde_runtime{}
    if (set AEONFALLHordeRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLHordeRuntime in its session")
