# Canonical status-definition registry.
# Definitions are generated from validated slice content and registered during
# project bootstrap so adapters never hardcode status behavior by name.

aeonfall_status_registry := class():

    var Definitions:[string]aeonfall_status_definition = map{}

    Register(Definition:aeonfall_status_definition)<transacts>:logic=
        if:
            Definition.StatusId <> ""
            Definition.MaxStacks > 0
            Definition.BaseDurationSeconds >= 0.0
        then:
            if:
                Existing := Definitions[Definition.StatusId]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "status.definition_duplicate_rejected",
                        SourceId := Definition.StatusId
                    }
                )
                return false

            if:
                set Definitions[Definition.StatusId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "status.definition_registered",
                        SourceId := Definition.StatusId
                    }
                )
                return true

        false

    Get(StatusId:string)<decides><transacts>:aeonfall_status_definition=
        Definitions[StatusId]

    IsRegistered(StatusId:string)<decides><transacts>:void=
        Definition := Definitions[StatusId]
        Definition.StatusId <> ""

AEONFALLStatusRegistry:aeonfall_status_registry = aeonfall_status_registry{}
