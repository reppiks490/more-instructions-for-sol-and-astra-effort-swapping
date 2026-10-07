# Canonical Transcendent Zero Authority registry.

aeonfall_transcendent_authority_registry := class():

    var Definitions:[string]aeonfall_transcendent_authority_definition = map{}

    Register(
        Definition:aeonfall_transcendent_authority_definition
    )<transacts>:logic=
        if:
            Definition.AuthorityId <> ""
            Definition.DisplayName <> ""
            Definition.ActiveSeconds > 0.0
            Definition.ExhaustionSeconds > 0.0
            Definition.AbilityIds.Length > 0
            set Definitions[Definition.AuthorityId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "transcendent.authority_registered",
                    SourceId := Definition.AuthorityId,
                    ContextId := Definition.DisplayName
                }
            )
            return true

        false

    Get(
        AuthorityId:string
    )<decides><transacts>:aeonfall_transcendent_authority_definition=
        Definitions[AuthorityId]

    IsRegistered(AuthorityId:string)<decides><transacts>:void=
        Definition := Definitions[AuthorityId]
        Definition.AuthorityId <> ""

AEONFALLTranscendentAuthorityRegistry:aeonfall_transcendent_authority_registry =
    aeonfall_transcendent_authority_registry{}
