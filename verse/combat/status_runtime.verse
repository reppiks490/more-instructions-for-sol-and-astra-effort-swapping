# Session status state runtime.
# Gameplay adapters translate these canonical states into actual movement,
# damage, VFX, device, character, or Scene Graph effects.

aeonfall_status_runtime := class():

    EventBus:aeonfall_event_bus = AEONFALLRuntimeBus
    StatusRegistry:aeonfall_status_registry = AEONFALLStatusRegistry
    var StatusesByTarget:[string][]aeonfall_status_instance = map{}

    # Both the canonical map write and its physical command must commit. A full
    # queue fails this helper and rolls back the map write in the caller's
    # failure context, including earlier applications in ApplyBatch.
    CommitStatusChange(
        TargetKey:string, Updated:[]aeonfall_status_instance, Event:aeonfall_runtime_event
    )<decides><transacts>:void=
        set StatusesByTarget[TargetKey] = Updated
        Admitted := EventBus.TryEmit(Event)
        Admitted?

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
    )<transacts>:logic=
        if:
            TargetKey <> ""
            Definition.StatusId <> ""
            Definition.MaxStacks > 0
            Definition.BaseDurationSeconds >= 0.0
        then:
            Existing := GetStatuses(TargetKey)
            var Updated:[]aeonfall_status_instance = array{}
            var Found:logic = false
            var Changed:logic = false

            for (Instance : Existing):
                if (Instance.StatusId = Definition.StatusId):
                    set Found = true

                    if (Definition.StackRule = aeonfall_status_stack_rule.RejectDuplicate):
                        set Updated = Updated + array{Instance}

                    else if (Definition.StackRule = aeonfall_status_stack_rule.RefreshDuration):
                        set Changed = true
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

                        # Even at the stack cap, a valid reapplication refreshes
                        # duration and source/magnitude by design.
                        set Changed = true
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
                        # ReplaceIfStronger is a true compare-and-replace rule.
                        # A weaker/equal reapplication is rejected so the
                        # calling ability does not spend resources for no
                        # effective status change.
                        if (Magnitude > Instance.Magnitude):
                            set Changed = true
                            set Updated = Updated + array{
                                aeonfall_status_instance{
                                    StatusId := Instance.StatusId,
                                    SourceId := SourceId,
                                    StackCount := Instance.StackCount,
                                    Magnitude := Magnitude,
                                    RemainingSeconds := Definition.BaseDurationSeconds
                                }
                            }
                        else:
                            set Updated = Updated + array{Instance}
                else:
                    set Updated = Updated + array{Instance}

            if:
                not Found?
            then:
                set Changed = true
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
                Changed?
                CommitStatusChange[TargetKey, Updated, aeonfall_runtime_event{
                    EventType := "status.applied",
                    SourceId := SourceId,
                    TargetId := TargetKey,
                    ContextId := Definition.StatusId,
                    Amount := Magnitude
                }]
            then:
                return true

            EventBus.Emit(
                aeonfall_runtime_event{
                    EventType := "status.application_rejected",
                    SourceId := SourceId,
                    TargetId := TargetKey,
                    ContextId := Definition.StatusId,
                    Amount := Magnitude
                }
            )

        false

    # Called in a failure context: all status changes AND queued presentation
    # events roll back if any status is missing or rejects application. Existing
    # stacks are restored, not removed as an approximate "undo" operation.
    ApplyBatch(
        TargetKey:string, StatusIds:[]string, SourceId:string, Magnitude:int
    )<decides><transacts>:void=
        var Seen:[]string = array{}
        for (StatusId : StatusIds):
            not Seen.Find[StatusId]
            Definition := StatusRegistry.Get[StatusId]
            Applied := ApplyStatus(TargetKey, Definition, SourceId, Magnitude)
            Applied?
            set Seen += array{StatusId}

    RemoveStatus(TargetKey:string, StatusId:string)<transacts>:logic=
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
            CommitStatusChange[TargetKey, Updated, aeonfall_runtime_event{
                EventType := "status.removed",
                TargetId := TargetKey,
                ContextId := StatusId
            }]
        then:
            return true

        false

    CommitStatusTick(TargetKey:string, DeltaSeconds:float)<decides><transacts>:void=
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
                    Admitted := EventBus.TryEmit(
                        aeonfall_runtime_event{
                            EventType := "status.expired",
                            SourceId := Instance.SourceId,
                            TargetId := TargetKey,
                            ContextId := Instance.StatusId
                        }
                    )
                    if (not Admitted?):
                        # Retain its positive remaining duration. Writing zero
                        # would turn a timed status into a persistent status;
                        # keeping the instance retries expiry on the next tick.
                        set Updated = Updated + array{Instance}

        # Roll back expiry admissions if the corresponding map write fails.
        set StatusesByTarget[TargetKey] = Updated

    Tick(TargetKey:string, DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return
        if:
            CommitStatusTick[TargetKey, DeltaSeconds]
        then:
            return

    ClearTarget(TargetKey:string)<transacts>:void=
        if:
            set StatusesByTarget[TargetKey] = array{}
        then:
            # Forced canonical cleanup must not wait for presentation capacity.
            # The bridge's tracked-agent reconciliation handles a lost command.
            EventBus.Emit(
                aeonfall_runtime_event{
                    EventType := "status.target_cleared",
                    TargetId := TargetKey
                }
            )

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        # Snapshot keys so per-target atomic commits do not mutate an iterated
        # collection, and share the same expiry/retry policy with Tick.
        var TargetKeys:[]string = array{}
        for (TargetKey -> Existing : StatusesByTarget):
            set TargetKeys += array{TargetKey}
        for (TargetKey : TargetKeys):
            Tick(TargetKey, DeltaSeconds)

AEONFALLStatusRuntime:aeonfall_status_runtime = aeonfall_status_runtime{}
