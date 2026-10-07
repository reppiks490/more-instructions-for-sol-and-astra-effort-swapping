# Canonical God/Absolute form registry.

aeonfall_ascended_form_registry := class():

    var Definitions:[string]aeonfall_ascended_form_definition = map{}

    Register(Definition:aeonfall_ascended_form_definition)<transacts>:logic=
        if:
            Definition.FormId <> ""
            Definition.TransformationId <> ""
            Definition.RequiredAscensionRank > 0
            Definition.ActiveSeconds > 0.0
            Definition.ExhaustionSeconds > 0.0
            Definition.AbilityIds.Length > 0
            set Definitions[Definition.FormId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ascended_form.definition_registered",
                    SourceId := Definition.FormId,
                    TargetId := Definition.TransformationId
                }
            )
            return true

        false

    Get(FormId:string)<decides><transacts>:aeonfall_ascended_form_definition=
        Definitions[FormId]

AEONFALLAscendedFormRegistry:aeonfall_ascended_form_registry =
    aeonfall_ascended_form_registry{}
