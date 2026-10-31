using { /Fortnite.com/AI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Use on the actual Character Definitions for world monsters and rift NPCs.
# It owns navigation; a second independent combat/navigation loop must not
# override these commands. NormalAI supplies the authored non-sovereign loop.
# Existing actors are recruited through the session registry without respawn.
aeonfall_sovereign_monster_behavior := class(npc_behavior):
    @editable
    CanonicalId:string = "MON-043"
    @editable
    NormalAI:aeonfall_sovereign_normal_ai_device = aeonfall_sovereign_normal_ai_device{}

    var RuntimeKey:string = ""
    var OwnedIdentity:logic = false

    OnBegin<override>()<suspends>:void=
        if:
            Agent := GetAgent[]
            Character := Agent.GetFortCharacter[]
            Navigation := Character.GetNavigatable[]
        then:
            if (Existing := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]):
                set RuntimeKey = Existing
            else if (Registered := GetAEONFALLActorRegistry().Register[CanonicalId, Agent]):
                set RuntimeKey = Registered
                set OwnedIdentity = true
            else:
                return
            loop:
                if (not Character.IsActive[]):
                    return
                if:
                    Service := GetAEONFALLSovereignRuntime[]
                    Command := Service.GetCommand[Agent]
                    OwnerCharacter := Command.Owner.GetFortCharacter[]
                    OwnerCharacter.IsActive[]
                then:
                    # Four close formation quadrants, with additional depth.
                    var Offset:vector3 = vector3{X := 350.0, Y := 350.0}
                    if (Command.Slot >= 16 and Command.Slot < 32):
                        set Offset = vector3{X := -350.0, Y := 350.0}
                    else if (Command.Slot >= 32 and Command.Slot < 48):
                        set Offset = vector3{X := -350.0, Y := -350.0}
                    else if (Command.Slot >= 48):
                        set Offset = vector3{X := 350.0, Y := -350.0}
                    Destination := MakeNavigationTarget(OwnerCharacter.GetTransform().Translation + Offset)
                    # Bound each navigation await so cancellation, movement,
                    # defeat and authority revocation are observed promptly.
                    race:
                        block:
                            Result := Navigation.NavigateTo(
                                Destination,
                                ?MovementType := movement_types.Running,
                                ?ReachRadius := 150.0,
                                ?AllowPartialPath := true
                            )
                            Sleep(0.1)
                        Sleep(0.5)
                    Navigation.StopNavigation()
                else:
                    # The native normal-AI provider must also use short,
                    # interruptible navigation. This is a real authored device
                    # adapter, not an invented native behavior resume method.
                    race:
                        NormalAI.RunStep(Agent)
                        Sleep(0.5)
                    Navigation.StopNavigation()
                Sleep(0.1)

    OnEnd<override>():void=
        if (Agent := GetAgent[]):
            NormalAI.Forget(Agent)
            if (Service := GetAEONFALLSovereignRuntime[]):
                Service.RemoveArmyMember(Agent)
            if (Character := Agent.GetFortCharacter[], Navigation := Character.GetNavigatable[]):
                Navigation.StopNavigation()
        if (OwnedIdentity?, RuntimeKey <> ""):
            Removed := GetAEONFALLActorRegistry().Unregister(RuntimeKey)
