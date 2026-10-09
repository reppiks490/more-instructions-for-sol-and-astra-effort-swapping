using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Authored ordinary corpse rewards. Boss-only MAT-011 cannot be harvested.
# Each corpse is allocated by an actual NPC elimination, has a physical
# position and lifetime, and can be consumed by exactly one brood or player.
aeonfall_corpse_harvest_device := class(creative_device):
    @editable
    Ecology:aeonfall_horde_ecology_adapter_device = aeonfall_horde_ecology_adapter_device{}
    @editable
    HarvestButton:button_device = button_device{}
    @editable
    Feedback:hud_message_device = hud_message_device{}
    @editable
    HarvestRangeCm:float = 250.0

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    var Subscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        if (HarvestRangeCm > 0.0, HarvestRangeCm <= 500.0):
            Bound := HarvestButton.InteractedWithEvent.Subscribe(OnHarvest)
            set Subscription = option{Bound}
        else:
            Print("AEONFALL corpse harvest rejected invalid range.")

    OnHarvest(Agent:agent):void=
        if (CommitHarvest[Agent]):
            Ecology.PrunePositions()
            Feedback.Show(
                Agent, AEONFALLGameplayMessage("Remains harvested: materials, reputation and XP earned"), 3.0
            )
        else:
            Feedback.Show(
                Agent, AEONFALLGameplayMessage("No available remains nearby, or reward could not be saved"), 3.0
            )

    # Persistence, corpse consumption, resources and the feedback event commit
    # together. A refused persistent save or event admission leaves the corpse
    # available and gives no materials, XP, reputation, meter or class charge.
    CommitHarvest(Agent:agent)<decides><transacts>:void=
        Ecology.Running?
        Player := player[Agent]
        Player.IsActive[]
        Character := Agent.GetFortCharacter[]
        Character.IsActive[]
        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        Position := Character.GetTransform().Translation
        CorpseId := Ecology.FindNearest(Position)?
        CorpsePosition := Ecology.CorpsePositions[CorpseId]
        Distance(Position, CorpsePosition) <= HarvestRangeCm
        Corpse := GetAEONFALLHordeRuntime().GetCorpse[CorpseId]
        Corpse.RegionId = Ecology.RegionId
        Corpse.RemainingSeconds > 0.0
        Old := ProfileService.GetProfile[Player]

        var Materials:[string]int = Old.MaterialLedger
        OldBone:int = if (Value := Materials["MAT-008"]): Value else: 0
        OldIron:int = if (Value := Materials["MAT-003"]): Value else: 0
        set Materials["MAT-008"] = OldBone + 12
        set Materials["MAT-003"] = OldIron + 4
        var Reputation:[string]int = Old.FactionReputation
        OldReputation:int = if (Value := Reputation["FAC-002"]): Value else: 0
        set Reputation["FAC-002"] = OldReputation + 5
        NewXP:int = Old.XP + 20
        Candidate := aeonfall_player_profile:
            MakeAEONFALLPlayerProfile<constructor>(Old)
            MaterialLedger := Materials
            FactionReputation := Reputation
            XP := NewXP
            Level := AEONFALLGetLevelForXP(NewXP)

        Used := GetAEONFALLHordeRuntime().UseCorpse(
            Ecology.RegionId, CorpseId, aeonfall_corpse_use.Harvest
        )
        Used?
        Saved := ProfileService.TrySaveProfile(Player, Candidate)
        Saved?

        # Crown command slots are reserved capacity, never harvest currency.
        if (ClassState := GetAEONFALLClassRuntime().GetState[OwnerKey]):
            if (ClassState.Active?, ClassState.ClassId = "CLS-006"):
                Added := GetAEONFALLClassRuntime().AddResource(OwnerKey, 20)
                Added?

        if:
            Old.UnlockedEntityIds.Find["WPN-003"]
            Old.EquippedWeaponIds.Find["WPN-003"]
            Definition := GetAEONFALLAbilityRegistry().Get["ABL-009"]
        then:
            Initialized := GetAEONFALLAbilityRuntime().Initialize(OwnerKey, Definition)
            Initialized?
            Filled := GetAEONFALLAbilityRuntime().AddMeter(OwnerKey, Definition, 25)
            Filled?

        Admitted := AEONFALLRuntimeBus.TryEmit(aeonfall_runtime_event{
            EventType := "progression.corpse_harvested",
            SourceId := OwnerKey,
            TargetId := Ecology.RegionId,
            ContextId := "{CorpseId}",
            Amount := 20
        })
        Admitted?

    OnEnd<override>():void=
        if (Bound := Subscription?):
            Bound.Cancel()
        set Subscription = false
