using { /Verse.org/Simulation }

# Shared ownership/order runtime for hireables, tameables, and authored summons.
# Character Definitions and npc_behavior remain responsible for actual movement,
# combat, navigation, and animation. This service owns authoritative squad state.
aeonfall_companion_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    var Bindings:[string]aeonfall_companion_binding = map{}
    var States:[string]aeonfall_companion_runtime_state = map{}

    OrderId(Order:aeonfall_companion_order):string=
        if (Order = aeonfall_companion_order.Follow):
            "Follow"
        else if (Order = aeonfall_companion_order.Guard):
            "Guard"
        else if (Order = aeonfall_companion_order.FocusTarget):
            "FocusTarget"
        else if (Order = aeonfall_companion_order.HoldPosition):
            "HoldPosition"
        else if (Order = aeonfall_companion_order.Flank):
            "Flank"
        else:
            "Retreat"

    GetBinding(CompanionKey:string)<decides><transacts>:aeonfall_companion_binding=
        Bindings[CompanionKey]

    GetState(CompanionKey:string)<decides><transacts>:aeonfall_companion_runtime_state=
        States[CompanionKey]

    CountActive(OwnerKey:string)<transacts>:int=
        var Count:int = 0
        for (CompanionKey -> Binding : Bindings):
            if:
                Binding.OwnerKey = OwnerKey
                Binding.Active?
            then:
                set Count += 1
        Count

    CountActiveEntity(
        OwnerKey:string,
        CanonicalId:string
    )<transacts>:int=
        var Count:int = 0
        for (CompanionKey -> Binding : Bindings):
            if:
                Binding.OwnerKey = OwnerKey
                Binding.CanonicalId = CanonicalId
                Binding.Active?
            then:
                set Count += 1
        Count

    GetCompanionLimit(OwnerKey:string)<transacts>:int=
        if:
            ClassState := AEONFALLClassRuntime.GetState[OwnerKey]
            ClassState.Active?
            Definition := AEONFALLClassRegistry.Get[ClassState.ClassId]
        then:
            if (Definition.BaseMaxCompanions > 0):
                Definition.BaseMaxCompanions
            else:
                1
        else:
            1

    CanBind(
        OwnerKey:string,
        CompanionKey:string
    )<transacts>:logic=
        if:
            AEONFALLActorRegistry.IsRegistered[OwnerKey]
            AEONFALLActorRegistry.IsRegistered[CompanionKey]
            CountActive(OwnerKey) < GetCompanionLimit(OwnerKey)
        then:
            if:
                Existing := Bindings[CompanionKey]
                Existing.Active?
            then:
                false
            else:
                true
        else:
            false

    BindTamed(
        OwnerKey:string,
        CompanionKey:string,
        SpeciesId:string,
        ReservationId:string,
        SourceAbilityId:string
    )<transacts>:logic=
        if:
            SpeciesId <> ""
            ReservationId <> ""
            CanBind(OwnerKey, CompanionKey)?
            CanonicalId := AEONFALLActorRegistry.GetCanonicalId[CompanionKey]
            CanonicalId = SpeciesId
        then:
            Binding := aeonfall_companion_binding:
                OwnerKey := OwnerKey
                CompanionKey := CompanionKey
                CanonicalId := SpeciesId
                Kind := aeonfall_companion_kind.Tameable
                ReservationId := ReservationId
                SourceAbilityId := SourceAbilityId
                Active := true

            State := aeonfall_companion_runtime_state:
                EntityId := SpeciesId
                CurrentOrder := aeonfall_companion_order.Follow
                IsHired := false
                IsTamed := true
                IsActive := true
                IsDowned := false

            if:
                set Bindings[CompanionKey] = Binding
                set States[CompanionKey] = State
            then:
                if:
                    BondStatus := AEONFALLStatusRegistry.Get["STS-008"]
                then:
                    Applied := AEONFALLStatusRuntime.ApplyStatus(
                        CompanionKey,
                        BondStatus,
                        OwnerKey,
                        1
                    )
                    if (Applied?):
                        Applied = true

                if:
                    OwnerAgent := AEONFALLActorRegistry.GetAgent[OwnerKey]
                then:
                    if:
                        OwnerPlayer := player[OwnerAgent]
                    then:
                        ProfileService.RecordTamedSpecies(
                            OwnerPlayer,
                            SpeciesId
                        )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "companion.tamed",
                        SourceId := OwnerKey,
                        TargetId := CompanionKey,
                        ContextId := SpeciesId,
                        Amount := CountActive(OwnerKey)
                    }
                )
                return true

        false

    BindHireable(
        OwnerKey:string,
        CompanionKey:string,
        NpcId:string
    )<transacts>:logic=
        if:
            NpcId <> ""
            CanBind(OwnerKey, CompanionKey)?
            CanonicalId := AEONFALLActorRegistry.GetCanonicalId[CompanionKey]
            CanonicalId = NpcId
            Definition := AEONFALLHireableRegistry.Get[NpcId]
            CountActiveEntity(OwnerKey, NpcId) < Definition.MaxSimultaneousPerPlayer
        then:
            Binding := aeonfall_companion_binding:
                OwnerKey := OwnerKey
                CompanionKey := CompanionKey
                CanonicalId := NpcId
                Kind := aeonfall_companion_kind.Hireable
                ReservationId := ""
                SourceAbilityId := ""
                Active := true

            State := aeonfall_companion_runtime_state:
                EntityId := NpcId
                CurrentOrder := aeonfall_companion_order.Follow
                IsHired := true
                IsTamed := false
                IsActive := true
                IsDowned := false

            if:
                set Bindings[CompanionKey] = Binding
                set States[CompanionKey] = State
            then:
                if:
                    OwnerAgent := AEONFALLActorRegistry.GetAgent[OwnerKey]
                then:
                    if:
                        OwnerPlayer := player[OwnerAgent]
                    then:
                        ProfileService.UnlockHireable(
                            OwnerPlayer,
                            NpcId
                        )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "companion.hired",
                        SourceId := OwnerKey,
                        TargetId := CompanionKey,
                        ContextId := NpcId,
                        Amount := CountActive(OwnerKey)
                    }
                )
                return true

        false

    SetOrder(
        OwnerKey:string,
        CompanionKey:string,
        NewOrder:aeonfall_companion_order
    )<transacts>:logic=
        if:
            Binding := Bindings[CompanionKey]
            Binding.Active?
            Binding.OwnerKey = OwnerKey
            Old := States[CompanionKey]
            Old.IsActive?
        then:
            var OrderAllowed:logic = true

            if (Binding.Kind = aeonfall_companion_kind.Hireable):
                if:
                    Definition := AEONFALLHireableRegistry.Get[Binding.CanonicalId]
                    Definition.AllowedOrderIds.Find[OrderId(NewOrder)]
                then:
                    set OrderAllowed = true
                else:
                    set OrderAllowed = false

            if (not OrderAllowed?):
                return false

            Updated := aeonfall_companion_runtime_state:
                EntityId := Old.EntityId
                CurrentOrder := NewOrder
                IsHired := Old.IsHired
                IsTamed := Old.IsTamed
                IsActive := Old.IsActive
                IsDowned := Old.IsDowned

            if:
                set States[CompanionKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "companion.order_changed",
                        SourceId := OwnerKey,
                        TargetId := CompanionKey,
                        ContextId := "{NewOrder}"
                    }
                )
                return true

        false

    SetDowned(
        CompanionKey:string,
        Downed:logic
    )<transacts>:logic=
        if:
            Old := States[CompanionKey]
            Old.IsActive?
        then:
            Updated := aeonfall_companion_runtime_state:
                EntityId := Old.EntityId
                CurrentOrder := Old.CurrentOrder
                IsHired := Old.IsHired
                IsTamed := Old.IsTamed
                IsActive := Old.IsActive
                IsDowned := Downed

            if:
                set States[CompanionKey] = Updated
            then:
                return true

        false

    ReleaseCompanion(
        OwnerKey:string,
        CompanionKey:string,
        Reason:string
    )<transacts>:logic=
        if:
            Binding := Bindings[CompanionKey]
            Binding.OwnerKey = OwnerKey
            Binding.Active?
        then:
            var UpdatedBindings:[string]aeonfall_companion_binding = map{}
            var UpdatedStates:[string]aeonfall_companion_runtime_state = map{}
            var Valid:logic = true

            for (StoredKey -> StoredBinding : Bindings):
                if (StoredKey <> CompanionKey):
                    if:
                        set UpdatedBindings[StoredKey] = StoredBinding
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            for (StoredKey -> StoredState : States):
                if (StoredKey <> CompanionKey):
                    if:
                        set UpdatedStates[StoredKey] = StoredState
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (Valid?):
                set Bindings = UpdatedBindings
                set States = UpdatedStates

                if (Binding.ReservationId <> ""):
                    Released := AEONFALLClassRuntime.ReleaseReservation(
                        Binding.ReservationId
                    )
                    if (Released?):
                        Released = true

                RemovedBond := AEONFALLStatusRuntime.RemoveStatus(
                    CompanionKey,
                    "STS-008"
                )
                if (RemovedBond?):
                    RemovedBond = true

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "companion.released",
                        SourceId := OwnerKey,
                        TargetId := CompanionKey,
                        ContextId := Reason,
                        Amount := CountActive(OwnerKey)
                    }
                )
                return true

        false

AEONFALLCompanionRuntime:aeonfall_companion_runtime = aeonfall_companion_runtime{}
