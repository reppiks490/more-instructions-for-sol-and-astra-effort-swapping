using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }
using { /UnrealEngine.com/Temporary/SpatialMath }

AEONFALLGameplayMessage<localizes>(Text:string):message = "{Text}"

# A server-side selector for authored NPC populations. Bind a Creative Input
# Action to SelectInput. Only the configured canonical NPC IDs can be selected.
# Range and view cone are checked here; this API does not provide a raycast.
aeonfall_actor_target_selector_device := class(creative_device):
    @editable
    SelectInput:input_trigger_device = input_trigger_device{}
    @editable
    TargetCanonicalIds:[]string = array{"MON-043", "BOS-005"}
    @editable
    MaximumDistanceCm:float = 2500.0
    @editable
    MinimumForwardCosine:float = 0.94
    @editable
    SelectionLifetimeSeconds:float = 8.0
    @editable
    Feedback:hud_message_device = hud_message_device{}

    var Subscription:?cancelable = false
    var NextSelectionNumber:int = 0

    OnBegin<override>()<suspends>:void=
        if:
            MaximumDistanceCm > 0.0
            MaximumDistanceCm <= 10000.0
            MinimumForwardCosine > 0.0
            MinimumForwardCosine <= 1.0
            SelectionLifetimeSeconds > 0.0
            SelectionLifetimeSeconds <= 30.0
            TargetCanonicalIds.Length > 0
        then:
            Bound := SelectInput.PressedEvent.Subscribe(OnPressed)
            set Subscription = option{Bound}
        else:
            Print("AEONFALL target selector rejected invalid settings.")

    OnPressed(Agent:agent):void=
        if:
            player[Agent]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
        then:
            Origin := Character.GetViewLocation()
            Forward := Character.GetViewRotation().GetForwardAxis()
            var NearestKey:string = ""
            var BestDistance:float = MaximumDistanceCm
            for (Key -> Candidate : GetAEONFALLActorRegistry().AgentByKey):
                if:
                    Key <> OwnerKey
                    not player[Candidate]
                    CanonicalId := GetAEONFALLActorRegistry().GetCanonicalId[Key]
                    TargetCanonicalIds.Find[CanonicalId]
                    IsUnboundNPC(Key)?
                    TargetCharacter := Candidate.GetFortCharacter[]
                    TargetCharacter.IsActive[]
                then:
                    Delta := TargetCharacter.GetTransform().Translation - Origin
                    Range := Distance(Origin, TargetCharacter.GetTransform().Translation)
                    if:
                        Range > 0.0
                        Range <= BestDistance
                        DotProduct(Delta, Forward) >= Range * MinimumForwardCosine
                    then:
                        set NearestKey = Key
                        set BestDistance = Range
            if (NearestKey <> ""):
                set NextSelectionNumber += 1
                Selected := GetAEONFALLTargetingRuntime().SetRuntimeTarget(
                    OwnerKey, NearestKey,
                    "SEL::" + OwnerKey + "::" + "{NextSelectionNumber}",
                    SelectionLifetimeSeconds
                )
                if (Selected?):
                    Feedback.Show(Agent, AEONFALLGameplayMessage("Target selected"), 2.0)
                    return
            Cleared := GetAEONFALLTargetingRuntime().Clear(OwnerKey)
            Feedback.Show(Agent, AEONFALLGameplayMessage("No eligible target in your view"), 2.0)

    IsUnboundNPC(Key:string)<transacts>:logic=
        if (Binding := GetAEONFALLCompanionRuntime().GetBinding[Key]):
            if (Binding.Active?):
                return false
        true

    OnEnd<override>():void=
        if (Bound := Subscription?):
            Bound.Cancel()
        set Subscription = false
