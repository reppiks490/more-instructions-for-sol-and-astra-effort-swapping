# Session status state runtime.
# Gameplay adapters translate these canonical states into actual movement,
# damage, VFX, device, character, or Scene Graph effects.

aeonfall_status_runtime := class():

    var StatusesByTarget:[string][]aeonfall_status_instance = map{}

    GetStatuses(TargetKey:string)<transacts>:[]aeonfall_status_instance=
        if (Statuses := StatusesByTarget[TargetKey]):
            Statuses
        else:
            array{}

    HasStatus(TargetKey:string, StatusId:string)<transacts>:logic=
        for (Instance : GetStatuses(TargetKey)):
            if (Instance.StatusId = StatusId):
                return true
        false

    ApplyStatus(
        TargetKey:string,
        Definition:aeonfall_status_definition,
        SourceId:string,
        Magnitude:int
    ):logic=
        if:
            TargetKey <> ""
            Definition.StatusId <> ""
            Definition.MaxStacks > 0
            Definition.BaseDurationSeconds >= 0.0
        then:
            Existing := GetStatuses(TargetKey)
            var Updated:[]aeonfall_status_instance = array{}
            var Found:logic = false

            for (Instance : Existing):
                if (Instance.StatusId = Definition.StatusId):
                    set Found = true

                    if (Definition.StackRule = aeonfall_status_stack_rule.RejectDuplicate):
                        set Updated = Updated + array{Instance}
                    else if (Definition.StackRule = aeonfall_status_stack_rule.RefreshDuration):
                        set Updated = Updated + array{
                            aeonfall_status_instance{
                                StatusId := Instance.StatusId,
                                SourceId := SourceId,
                                StackCount := Instance.StackCount,
                                Magnitude := Magnitude,
                                RemainingSeconds := Definition.BaseDurationSeconds
                            }
                        }
                    else if (Definition.StackRule = aeonfall_status_stack_rule.AddStack):
                        NewStacks:int =
                            if (Instance.StackCount + 1 > Definition.MaxStacks):
                                Definition.MaxStacks
                            else:
                                Instance.StackCount + 1
                        set Updated = Updated + array{
                            aeonfall_status_instance{
                                StatusId := Instance.StatusId,
                                SourceId := SourceId,
                                StackCount := NewStacks,
                                Magnitude := Magnitude,
                                RemainingSeconds := Definition.BaseDurationSeconds
                            }
                        }
                    else:
                        NewMagnitude:int =
                            if (Magnitude > Instance.Magnitude):
                                Magnitude
                            else:
                                Instance.Magnitude
                        set Updated = Updated + array{
                            aeonfall_status_instance{
                                StatusId := Instance.StatusId,
                                SourceId := SourceId,
                                StackCount := Instance.StackCount,
                                Magnitude := NewMagnitude,
                                RemainingSeconds := Definition.BaseDurationSeconds
                            }
                        }
                else:
                    set Updated = Updated + array{Instance}

            if:
                not Found?
            then:
                set Updated = Updated + array{
                    aeonfall_status_instance{
                        StatusId := Definition.StatusId,
                        SourceId := SourceId,
                        StackCount := 1,
                        Magnitude := Magnitude,
                        RemainingSeconds := Definition.BaseDurationSeconds
                    }
                }

            if:
                set StatusesByTarget[TargetKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "status.applied",
                        SourceId := SourceId,
                        TargetId := TargetKey,
                        ContextId := Definition.StatusId,
                        Amount := Magnitude
                    }
                )
                return true

        false

    RemoveStatus(TargetKey:string, StatusId:string):logic=
        Existing := GetStatuses(TargetKey)
        var Updated:[]aeonfall_status_instance = array{}
        var Removed:logic = false

        for (Instance : Existing):
            if (Instance.StatusId = StatusId):
                set Removed = true
            else:
                set Updated = Updated + array{Instance}

        if:
            Removed?
            set StatusesByTarget[TargetKey] = Updated
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "status.removed",
                    TargetId := TargetKey,
                    ContextId := StatusId
                }
            )
            return true

        false

    Tick(TargetKey:string, DeltaSeconds:float):void=
        if (DeltaSeconds <= 0.0):
            return

        Existing := GetStatuses(TargetKey)
        var Updated:[]aeonfall_status_instance = array{}

        for (Instance : Existing):
            if (Instance.RemainingSeconds <= 0.0):
                set Updated = Updated + array{Instance}
            else:
                Remaining:float = Instance.RemainingSeconds - DeltaSeconds
                if (Remaining > 0.0):
                    set Updated = Updated + array{
                        aeonfall_status_instance{
                            StatusId := Instance.StatusId,
                            SourceId := Instance.SourceId,
                            StackCount := Instance.StackCount,
                            Magnitude := Instance.Magnitude,
                            RemainingSeconds := Remaining
                        }
                    }
                else:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "status.expired",
                            SourceId := Instance.SourceId,
                            TargetId := TargetKey,
                            ContextId := Instance.StatusId
                        }
                    )

        if:
            set StatusesByTarget[TargetKey] = Updated
        then:
            return
    ClearTarget(TargetKey:string):void=
        if:
            set StatusesByTarget[TargetKey] = array{}
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "status.target_cleared",
                    TargetId := TargetKey
                }
            )

AEONFALLStatusRuntime:aeonfall_status_runtime = aeonfall_status_runtime{}
