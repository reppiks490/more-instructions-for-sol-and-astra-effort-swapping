using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Slice 001 Launch Session helper.
# IMPORTANT: Enabled defaults false. Keep disabled in production/published builds.
# This exists only to accelerate deterministic shop/crafting/progression testing.
aeonfall_slice_001_dev_harness_device := class(creative_device):

    @editable
    Enabled:logic = false

    @editable
    SeedEconomyButton:button_device = button_device{}

    @editable
    ActivateSepulchralButton:button_device = button_device{}

    @editable
    ActivateBeastCrownButton:button_device = button_device{}

    @editable
    SuccessMessage:hud_message_device = hud_message_device{}

    @editable
    FailureMessage:hud_message_device = hud_message_device{}

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    MaterialLedger:aeonfall_material_ledger = aeonfall_material_ledger{}
    Reputation:aeonfall_reputation_service = aeonfall_reputation_service{}

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            SeedEconomyButton.Disable()
            ActivateSepulchralButton.Disable()
            ActivateBeastCrownButton.Disable()
            return

        SeedEconomyButton.InteractedWithEvent.Subscribe(SeedEconomy)
        ActivateSepulchralButton.InteractedWithEvent.Subscribe(ActivateSepulchral)
        ActivateBeastCrownButton.InteractedWithEvent.Subscribe(ActivateBeastCrown)

    SeedEconomy(Agent:agent)<transacts>:void=
        # Dev-only grant. Build one immutable candidate and acknowledge one
        # persistent write before reporting success; no partial material or
        # reputation seeds are allowed if the profile is full or inactive.
        if:
            Player := player[Agent]
            Player.IsActive[]
            Old := ProfileService.GetProfile[Agent]
        then:
            var UpdatedMaterials:[string]int = Old.MaterialLedger
            var UpdatedReputation:[string]int = Old.FactionReputation
            if:
                set UpdatedMaterials["MAT-003"] = MaterialLedger.GetCount(Agent, "MAT-003") + 2500
                set UpdatedMaterials["MAT-008"] = MaterialLedger.GetCount(Agent, "MAT-008") + 2500
                set UpdatedMaterials["MAT-011"] = MaterialLedger.GetCount(Agent, "MAT-011") + 20
                set UpdatedReputation["FAC-002"] = Reputation.GetReputation(Agent, "FAC-002") + 500
            then:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    MaterialLedger := UpdatedMaterials
                    FactionReputation := UpdatedReputation
                Saved := ProfileService.TrySaveProfile(Player, Candidate)
                if (Saved?):
                    SuccessMessage.Show(Agent)
                    if:
                        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
                    then:
                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "dev.slice_001_economy_seeded",
                                SourceId := OwnerKey
                            }
                        )
                    return

        FailureMessage.Show(Agent)

    ActivateSepulchral(Agent:agent)<transacts>:void=
        ActivateClass(Agent, "CLS-006")

    ActivateBeastCrown(Agent:agent)<transacts>:void=
        ActivateClass(Agent, "CLS-007")

    ActivateClass(
        Agent:agent,
        ClassId:string
    )<transacts>:void=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            Activated := GetAEONFALLClassRuntime().ActivateClass(
                OwnerKey,
                ClassId
            )

            if (Activated?):
                SuccessMessage.Show(Agent)
                return

        FailureMessage.Show(Agent)
