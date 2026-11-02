using { /Fortnite.com/AI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Attach ONLY to the dedicated Titan proxy NPC Character Definition.
# This behavior exclusively owns navigation; the player never possesses it.
# No attack/damage calls occur here, and no persistent state is written.
aeonfall_titan_proxy_behavior := class(npc_behavior):
    OnBegin<override>()<suspends>:void=
        if:
            Agent := GetAgent[]
            Character := Agent.GetFortCharacter[]
            Navigation := Character.GetNavigatable[]
        then:
            Service := GetAEONFALLTitanProxyCommands()
            var SeenSequence:int = 0
            var BoundOnce:logic = false
            var StartupChecks:int = 0
            loop:
                Sleep(0.15)
                if (Service.BoundNpc(Agent)?):
                    set BoundOnce = true
                    if (Command := Service.GetNewMove[Agent, SeenSequence]):
                        set SeenSequence = Command.Sequence
                        # A finite, interruptible move; a new command is
                        # processed only after this attempt is bounded.
                        race:
                            block:
                                Result := Navigation.NavigateTo(
                                    MakeNavigationTarget(Command.Destination),
                                    ?MovementType := movement_types.Walking,
                                    ?ReachRadius := 150.0,
                                    ?AllowPartialPath := false
                                )
                            block:
                                Sleep(2.0)
                        Navigation.StopNavigation()
                else:
                    if (BoundOnce?):
                        Navigation.StopNavigation()
                        return
                    set StartupChecks += 1
                    if (StartupChecks >= 40):
                        # No late, unsolicited NPC may roam indefinitely.
                        Navigation.StopNavigation()
                        return

    OnEnd<override>():void=
        if (Agent := GetAgent[], Character := Agent.GetFortCharacter[],
            Navigation := Character.GetNavigatable[]):
            Navigation.StopNavigation()
