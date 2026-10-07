# Session runtime registry for canonical AEONFALL content.
# Registration is project-bound: generated/bootstrap code supplies definitions
# and bindings without changing persistent canonical IDs.

aeonfall_content_registry := class():

    var Definitions:[string]aeonfall_content_definition = map{}
    var Bindings:[string]aeonfall_runtime_binding = map{}

    RegisterDefinition(Definition:aeonfall_content_definition)<transacts>:logic=
        if:
            Definition.CanonicalId <> ""
            set Definitions[Definition.CanonicalId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "content.definition_registered",
                    SourceId := Definition.CanonicalId,
                    ContextId := Definition.RuntimeBindingId
                }
            )
            return true
        false

    RegisterBinding(Binding:aeonfall_runtime_binding)<transacts>:logic=
        if:
            Binding.CanonicalId <> ""
            set Bindings[Binding.CanonicalId] = Binding
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "content.binding_registered",
                    SourceId := Binding.CanonicalId,
                    ContextId := Binding.RuntimeBindingId
                }
            )
            return true
        false

    GetDefinition(CanonicalId:string)<decides><transacts>:aeonfall_content_definition=
        Definitions[CanonicalId]

    GetBinding(CanonicalId:string)<decides><transacts>:aeonfall_runtime_binding=
        Bindings[CanonicalId]

    IsEnabled(CanonicalId:string)<decides><transacts>:void=
        Definition := Definitions[CanonicalId]
        Definition.Enabled?

    IsReady(CanonicalId:string)<decides><transacts>:void=
        Definition := Definitions[CanonicalId]
        Binding := Bindings[CanonicalId]
        Definition.Enabled?
        Binding.RuntimeBindingId <> ""

AEONFALLContentRegistry:aeonfall_content_registry = aeonfall_content_registry{}
