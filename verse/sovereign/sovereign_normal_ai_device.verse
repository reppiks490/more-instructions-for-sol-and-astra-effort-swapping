using { /Fortnite.com/AI }
using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# A concrete bounded normal-state navigation provider for the starter NPCs.
# The NPC follows its authored patrol anchors while the sovereign is dormant.
# Combat damage/animations remain authored Character Definition behavior;
# this provider does not manufacture a melee attack API.
aeonfall_sovereign_normal_ai_device := class(creative_device):
    @editable
    PatrolAnchors:[]creative_prop = array{}
    @editable
    ReachRadiusCm:float = 200.0
    var NextAnchorByAgent:[agent]int = map{}

    RunStep(Agent:agent)<suspends>:void=
        if:
            PatrolAnchors.Length > 0
            ReachRadiusCm >= 100.0
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            Navigation := Character.GetNavigatable[]
        then:
            var Index:int = 0
            if (Stored := NextAnchorByAgent[Agent]):
                set Index = Stored
            if (Index >= PatrolAnchors.Length):
                set Index = 0
            if (Anchor := PatrolAnchors[Index], Anchor.IsValid[]):
                Destination := MakeNavigationTarget(Anchor.GetTransform().Translation)
                Result := Navigation.NavigateTo(
                    Destination,
                    ?MovementType := movement_types.Walking,
                    ?ReachRadius := ReachRadiusCm,
                    ?AllowPartialPath := true
                )
                if (Result = navigation_result.Reached):
                    if (set NextAnchorByAgent[Agent] = Index + 1):
                        set Index = Index
        Sleep(0.1)

    Forget(Agent:agent)<transacts>:void=
        var Kept:[agent]int = map{}
        for (Other -> Index : NextAnchorByAgent, Other <> Agent):
            if (set Kept[Other] = Index):
                set Kept = Kept
        set NextAnchorByAgent = Kept

    OnEnd<override>():void=
        set NextAnchorByAgent = map{}
