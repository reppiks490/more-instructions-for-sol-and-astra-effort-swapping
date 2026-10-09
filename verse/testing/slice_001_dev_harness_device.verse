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
        # Enough for all first-slice offers/recipes to be exercised repeatedly
        # across separate test profiles without editing the canonical prices.
        MaterialLedger.Add(Agent, "MAT-003", 2500)
        MaterialLedger.Add(Agent, "MAT-008", 2500)
        MaterialLedger.Add(Agent, "MAT-011", 20)
        Reputation.AddReputation(Agent, "FAC-002", 500)

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
