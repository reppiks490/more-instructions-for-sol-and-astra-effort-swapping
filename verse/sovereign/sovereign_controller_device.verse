using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Fortnite.com/AI }
using { /Fortnite.com/Teams }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

SovereignHerald<localizes>:message = "SOVEREIGN UNMAKING. The sky has broken. One will now commands the abyss."
SovereignDemand<localizes>:message = "TRIBUTE OR UNMAKING. Pay 40 Ossuary Resin at the altar, or defy and stop the sovereign."
SovereignDefiant<localizes>:message = "DEFIANCE ACCEPTED. Stop the sovereign before the countdown ends."
SovereignPaid<localizes>:message = "TRIBUTE ACCEPTED. Your existence is spared for this manifestation."
SovereignUnmade<localizes>:message = "UNMADE. The sovereign has severed your place in reality."
SovereignReleased<localizes>:message = "REALITY RESTORED. The sovereign's manifestation has ended."
SovereignRejected<localizes>:message = "The sovereign power does not recognize you, or its manifestation is already active."
SovereignTributeRejected<localizes>:message = "Tribute refused: this quest is resolved, the ledger is insufficient, or the save was refused."
SovereignQuestTitle<localizes>:message = "Tribute or Unmaking"
SovereignQuestDescription<localizes>:message = "Pay 40 resin, or stop the sovereign."

aeonfall_sovereign_region_binding := class<concrete>:
    @editable
    RegionId:string = "REG-001"
    @editable
    Maelstrom:vfx_spawner_device = vfx_spawner_device{}
    @editable
    Rift:vfx_spawner_device = vfx_spawner_device{}
    @editable
    Monstrosities:npc_spawner_device = npc_spawner_device{}

# Configure owned devices, author the sky sequence and verified owner proof,
# then enable. A catalog entry alone cannot authenticate the unique owner.
aeonfall_sovereign_controller_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    Authority:aeonfall_sovereign_authority_device = aeonfall_sovereign_authority_device{}
    @editable
    DrawInput:input_trigger_device = input_trigger_device{}
    @editable
    VeilInput:input_trigger_device = input_trigger_device{}
    @editable
    DismissInput:input_trigger_device = input_trigger_device{}
    @editable
    Herald:hud_message_device = hud_message_device{}
    @editable
    Demand:hud_message_device = hud_message_device{}
    @editable
    Feedback:hud_message_device = hud_message_device{}
    @editable
    Quest:tracker_device = tracker_device{}
    @editable
    TributeAltar:button_device = button_device{}
    @editable
    DefianceAltar:button_device = button_device{}
    @editable
    RedVoidSky:cinematic_sequence_device = cinematic_sequence_device{}
    @editable
    Countdown:timer_device = timer_device{}
    @editable
    Regions:[]aeonfall_sovereign_region_binding = array{}
    @editable
    DurationSeconds:float = 180.0
    @editable
    MaxArmyMembers:int = 64
    @editable
    RiftBurstPerRegion:int = 4
    @editable
    MinimumExposureSeconds:float = 30.0
    @editable
    EnableUnmakingElimination:logic = false

    StopEvent:event() = event(){}
    var Running:logic = false
    var Token:int = 0
    var Runtime:?aeonfall_sovereign_runtime = false
    var Subscriptions:[]cancelable = array{}
    var OwnerDeathSubscription:?cancelable = false
    var HiddenCharacter:?fort_character = false
    var OriginalTeams:[agent]team = map{}
    var SeenCharacters:[player]fort_character = map{}

    ValidSettings()<transacts>:logic=
        if:
            Regions.Length > 0
            Regions.Length <= 8
            DurationSeconds >= 30.0
            DurationSeconds <= 600.0
            MaxArmyMembers > 0
            MaxArmyMembers <= 96
            RiftBurstPerRegion > 0
            RiftBurstPerRegion <= 4
            Regions.Length * RiftBurstPerRegion <= 32
            MinimumExposureSeconds >= 15.0
            MinimumExposureSeconds <= 60.0
            DrawInput <> VeilInput
            DrawInput <> DismissInput
            VeilInput <> DismissInput
            TributeAltar <> DefianceAltar
            Herald <> Demand
            Herald <> Feedback
            Demand <> Feedback
            not Countdown.IsStatePerAgent[]
        then:
            var SeenRegions:[]string = array{}
            var SeenSpawners:[]npc_spawner_device = array{}
            var SeenVFX:[]vfx_spawner_device = array{}
            for (Region : Regions):
                if (Region.RegionId = "" or Region.Maelstrom = Region.Rift):
                    return false
                if (SeenRegions.Find[Region.RegionId]):
                    return false
                if (SeenSpawners.Find[Region.Monstrosities]):
                    return false
                if (SeenVFX.Find[Region.Maelstrom] or SeenVFX.Find[Region.Rift]):
                    return false
                set SeenRegions += array{Region.RegionId}
                set SeenSpawners += array{Region.Monstrosities}
                set SeenVFX += array{Region.Maelstrom, Region.Rift}
            return true
        false

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        if (not ValidSettings()?):
            Print("AEONFALL sovereign controller rejected invalid or duplicate bindings.")
            return
        if (Service := GetAEONFALLSovereignRuntime[]):
            Acquired := Service.AcquireController(Self)
            if (not Acquired?):
                Print("AEONFALL sovereign controller rejected a duplicate physical controller.")
                return
            set Runtime = option{Service}
        else:
            return
        set Running = true
        # These are exclusively owned bindings, never ordinary encounter adds.
        CleanupPhysical()
        Quest.SetTitleText(SovereignQuestTitle)
        Quest.SetDescriptionText(SovereignQuestDescription)
        Quest.SetTarget(1)
        Countdown.SetMaxDuration(DurationSeconds)
        set Subscriptions = array{
            DrawInput.PressedEvent.Subscribe(Draw),
            VeilInput.PressedEvent.Subscribe(ToggleVeil),
            DismissInput.PressedEvent.Subscribe(Dismiss),
            TributeAltar.InteractedWithEvent.Subscribe(Tribute),
            DefianceAltar.InteractedWithEvent.Subscribe(Defy),
            GetPlayspace().PlayerAddedEvent().Subscribe(PlayerJoined),
            GetPlayspace().PlayerRemovedEvent().Subscribe(PlayerLeft)
        }
        race:
            MaintenanceLoop()
            StopEvent.Await()

    AuthorizedOwner(Agent:agent)<decides><transacts>:player=
        Running?
        Player := player[Agent]
        Player.IsActive[]
        Character := Agent.GetFortCharacter[]
        Character.IsActive[]
        Authorized := Authority.CanWield(Player)
        Authorized?
        Player

    Draw(Agent:agent):void=
        if (Player := AuthorizedOwner[Agent], Service := Runtime?, OriginalTeams.Length = 0):
            Bound := Service.BindVerifiedOwner(Player)
            if (not Bound?):
                Feedback.Show(Agent, SovereignRejected, 4.0)
                return
            if (Started := Service.Begin[Self, Player, DurationSeconds, MaxArmyMembers]):
                set Token = Started
                if (Character := Player.GetFortCharacter[]):
                    Listener := aeonfall_sovereign_owner_death_listener{Controller := Self, Generation := Started}
                    DeathSubscription := Character.EliminatedEvent().Subscribe(Listener.OnEliminated)
                    set OwnerDeathSubscription = option{DeathSubscription}
                for (Other : GetPlayspace().GetPlayers()):
                    Herald.Show(Other, SovereignHerald, 8.0)
                    PlayerJoined(Other)
                RedVoidSky.Play()
                Countdown.Start()
                spawn{Manifest(Started)}
                return
        Feedback.Show(Agent, SovereignRejected, 4.0)

    Manifest(Generation:int)<suspends>:void=
        if (Service := Runtime?):
            Sleep(2.0)
            if (not Running? or not Service.IsCurrent(Generation)?):
                return
            for (Region : Regions):
                Region.Maelstrom.Enable()
            Sleep(2.0)
            if (not Running? or not Service.IsCurrent(Generation)?):
                return
            for (Region : Regions):
                Region.Rift.Enable()
                # Timer spawning must be disabled in the authored spawners.
                # The finite burst is the only spawn producer for these rigs.
                Region.Monstrosities.Reset()
                Region.Monstrosities.Enable()
                for (Index := 1..RiftBurstPerRegion):
                    if (Service.IsCurrent(Generation)?):
                        Region.Monstrosities.Spawn()

    PlayerJoined(Player:player):void=
        if (Running?, Service := Runtime?, Service.IsCurrent(Token)?):
            Enrolled := Service.Enroll(Player, Token)
            if (Enrolled?):
                ShowParticipantSnapshot(Player, Service)
                Herald.Show(Player, SovereignHerald, 8.0)

    ShowParticipantSnapshot(Player:player, Service:aeonfall_sovereign_runtime):void=
        if (State := Service.GetParticipant[Player, Token]):
            if (Character := Player.GetFortCharacter[]):
                if (set SeenCharacters[Player] = Character):
                    set Token = Token
            if (State.State = aeonfall_sovereign_quest_state.Tributed):
                Demand.Hide(Player)
                Quest.Remove(Player)
                Feedback.Show(Player, SovereignPaid, 8.0)
            else:
                Quest.Reset(Player)
                Quest.Assign(Player)
                if (State.State = aeonfall_sovereign_quest_state.Defiant):
                    Demand.Show(Player, SovereignDefiant, 0.0)
                else:
                    Demand.Show(Player, SovereignDemand, 0.0)

    Tribute(Agent:agent):void=
        if:
            Running?
            Service := Runtime?
            Player := player[Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            Service.PayTribute[Player, Token, "MAT-008", 40]
        then:
            Demand.Hide(Agent)
            Quest.Complete(Agent)
            Feedback.Show(Agent, SovereignPaid, 8.0)
        else:
            Feedback.Show(Agent, SovereignTributeRejected, 5.0)

    Defy(Agent:agent):void=
        if:
            Running?
            Service := Runtime?
            Player := player[Agent]
            Player.IsActive[]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            Service.Defy[Player, Token]
        then:
            Demand.Show(Agent, SovereignDefiant, 0.0)

    ToggleVeil(Agent:agent):void=
        if (Player := AuthorizedOwner[Agent], Service := Runtime?):
            Bound := Service.BindVerifiedOwner(Player)
            if (not Bound?):
                return
            if (Existing := HiddenCharacter?):
                Existing.Show()
                set HiddenCharacter = false
            else if (Character := Agent.GetFortCharacter[]):
                Character.Hide()
                set HiddenCharacter = option{Character}
            return
        Feedback.Show(Agent, SovereignRejected, 4.0)

    RevealOwner():void=
        if (Character := HiddenCharacter?):
            Character.Show()
        set HiddenCharacter = false

    Dismiss(Agent:agent):void=
        if (Player := AuthorizedOwner[Agent], Service := Runtime?, Service.IsOwner(Player)?):
            Finish(Token, true)

    PlayerLeft(Player:player):void=
        if (Service := Runtime?, Service.IsOwner(Player)?):
            RevealOwner()
            Finish(Token, true)

    MaintenanceLoop()<suspends>:void=
        loop:
            Sleep(0.25)
            if (not Running?):
                return
            if (Hidden := HiddenCharacter?):
                if (not Hidden.IsActive[]):
                    RevealOwner()
            if (Service := Runtime?, Sovereign := Service.Owner?):
                Authorized := Authority.CanWield(Sovereign)
                if (not Authorized?):
                    RevealOwner()
                    Finish(Token, true)
                else if (Service.IsCurrent(Token)?):
                    if:
                        Sovereign.IsActive[]
                        Character := Sovereign.GetFortCharacter[]
                        Character.IsActive[]
                    then:
                        RecruitRegisteredMonsters(Service)
                        for (Player -> State : Service.Participants):
                            if (Player.IsActive[], CurrentCharacter := Player.GetFortCharacter[], CurrentCharacter.IsActive[]):
                                if (Previous := SeenCharacters[Player], Previous = CurrentCharacter):
                                    set Token = Token
                                else:
                                    ShowParticipantSnapshot(Player, Service)
                        if (GetSimulationElapsedTime() >= Service.Deadline):
                            Finish(Token, false)
                    else:
                        RevealOwner()
                        Finish(Token, true)
            if (Service := Runtime?, not Service.Active?, OriginalTeams.Length > 0):
                RestoreTeams()
            # Refuse an accidental timer-spawning rig instead of leaking NPCs.
            for (Region : Regions):
                if (Region.Monstrosities.GetAgents().Length > RiftBurstPerRegion):
                    Region.Monstrosities.Disable()
                    Region.Monstrosities.DespawnAll(false)

    IsMonsterCanonical(Id:string)<transacts>:logic=
        if (Id.Length >= 4, Id[0] = 'M', Id[1] = 'O', Id[2] = 'N', Id[3] = '-'):
            return true
        false

    RecruitRegisteredMonsters(Service:aeonfall_sovereign_runtime):void=
        if (Sovereign := Service.Owner?, OwnerTeam := GetPlayspace().GetTeamCollection().GetTeam[Sovereign]):
            Teams := GetPlayspace().GetTeamCollection()
            for (Key -> Agent : GetAEONFALLActorRegistry().AgentByKey):
                if:
                    Canonical := GetAEONFALLActorRegistry().GetCanonicalId[Key]
                    IsMonsterCanonical(Canonical)?
                    not player[Agent]
                    Character := Agent.GetFortCharacter[]
                    Character.IsActive[]
                    Character.GetNavigatable[]
                    Slot := Service.ClaimArmy[Agent, Token]
                then:
                    if (not OriginalTeams[Agent]):
                        if (OldTeam := Teams.GetTeam[Agent]):
                            if (set OriginalTeams[Agent] = OldTeam):
                                if (Teams.AddToTeam[Agent, OwnerTeam]):
                                    set Token = Token
                                else:
                                    Service.RemoveArmyMember(Agent)
                                    DropOriginalTeam(Agent)
                            else:
                                Service.RemoveArmyMember(Agent)
                        else:
                            Service.RemoveArmyMember(Agent)
            # Despawn/death releases finite command slots and stored handles.
            var Kept:[agent]team = map{}
            for (Agent -> OldTeam : OriginalTeams):
                if (Character := Agent.GetFortCharacter[], Character.IsActive[]):
                    if (set Kept[Agent] = OldTeam):
                        set Kept = Kept
                else:
                    Service.RemoveArmyMember(Agent)
            set OriginalTeams = Kept

    DropOriginalTeam(Agent:agent)<transacts>:void=
        var Kept:[agent]team = map{}
        for (Other -> OldTeam : OriginalTeams, Other <> Agent):
            if (set Kept[Other] = OldTeam):
                set Kept = Kept
        set OriginalTeams = Kept

    Finish(Generation:int, Stopped:logic):void=
        if (Service := Runtime?, Service.Resolve[Generation, Stopped, MinimumExposureSeconds]):
            if (Subscription := OwnerDeathSubscription?):
                Subscription.Cancel()
            set OwnerDeathSubscription = false
            CleanupPhysical()
            RevealOwner()
            set SeenCharacters = map{}
            for (Player -> State : Service.Participants):
                if (Player.IsActive[]):
                    Demand.Hide(Player)
                    Quest.Remove(Player)
                    if (State.State = aeonfall_sovereign_quest_state.Unmade):
                        Feedback.Show(Player, SovereignUnmade, 12.0)
                        # Authored opt-in outcome: only an explicit defiant.
                        # Never delete profiles, materials or account progress.
                        if:
                            EnableUnmakingElimination?
                            State.MayBeEliminated?
                            Character := Player.GetFortCharacter[]
                            Character.IsActive[]
                        then:
                            Character.Damage(1000000.0)
                    else if (State.State = aeonfall_sovereign_quest_state.Tributed):
                        Feedback.Show(Player, SovereignPaid, 8.0)
                    else:
                        Feedback.Show(Player, SovereignReleased, 8.0)

    CleanupPhysical():void=
        RedVoidSky.Stop()
        for (Region : Regions):
            Region.Maelstrom.Disable()
            Region.Rift.Disable()
            Region.Monstrosities.Disable()
            Region.Monstrosities.DespawnAll(false)
        Countdown.Reset()
        RestoreTeams()

    RestoreTeams():void=
        Teams := GetPlayspace().GetTeamCollection()
        var Pending:[agent]team = map{}
        for (Agent -> OldTeam : OriginalTeams):
            if (Character := Agent.GetFortCharacter[], Character.IsActive[]):
                if (Navigation := Character.GetNavigatable[]):
                    Navigation.StopNavigation()
                if (Teams.AddToTeam[Agent, OldTeam]):
                    set Token = Token
                else:
                    if (set Pending[Agent] = OldTeam):
                        set Pending = Pending
        # Failed physical restores remain owned for the next maintenance tick.
        set OriginalTeams = Pending

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if (Subscription := OwnerDeathSubscription?):
            Subscription.Cancel()
        set OwnerDeathSubscription = false
        if (Service := Runtime?, Service.OwnsController(Self)?):
            CleanupPhysical()
            RevealOwner()
            for (Player : GetPlayspace().GetPlayers()):
                Demand.Hide(Player)
                Quest.Remove(Player)
            Service.ReleaseController(Self)
        set Runtime = false
        set SeenCharacters = map{}

aeonfall_sovereign_owner_death_listener := class:
    Controller:aeonfall_sovereign_controller_device
    Generation:int

    OnEliminated(Result:elimination_result):void=
        Controller.Finish(Generation, true)
