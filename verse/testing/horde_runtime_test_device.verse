using { /Fortnite.com/Devices }
using { /Verse.org/Diagnostics }
using { /Verse.org/Simulation }

# Calls actual Verse gameplay logic. Disabled in production. These assertions
# have NOT run until the device compiles and runs inside a UEFN Launch Session.
aeonfall_horde_runtime_test_device := class(creative_device):
    @editable
    Enabled:logic = false
    var Failures:int = 0
    var Checks:int = 0

    Check(Label:string, Passed:logic):void=
        set Checks += 1
        if (not Passed?):
            set Failures += 1
            Print("HORDE FAIL: {Label}")

    CheckTier(Runtime:aeonfall_horde_runtime, Key:string, Expected:int):void=
        if (State := Runtime.GetBrood[Key], State.Tier = Expected):
            Check("tier {Expected}", true)
        else:
            Check("tier {Expected}", false)

    FeedAmount(Runtime:aeonfall_horde_runtime, Key:string, Amount:int, Trait:aeonfall_horde_trait):void=
        Id := Runtime.AddCorpse("test", Amount, Trait)
        Check("feed succeeds", Runtime.Feed(Key, Id))

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        Runtime := aeonfall_horde_runtime{}
        Check("register", Runtime.RegisterBrood("a", "test"))
        Check("duplicate registration", logic{not Runtime.RegisterBrood("a", "test")?})
        Check("empty actor", logic{not Runtime.RegisterBrood("", "test")?})
        Check("zero corpse rejected", logic{Runtime.AddCorpse("test", 0, aeonfall_horde_trait.None) = 0})
        Check("negative corpse rejected", logic{Runtime.AddCorpse("test", -1, aeonfall_horde_trait.None) = 0})
        Check("oversized corpse rejected", logic{Runtime.AddCorpse("test", 301, aeonfall_horde_trait.None) = 0})
        Check("unknown region rejected", logic{Runtime.AddCorpse("unknown", 20, aeonfall_horde_trait.None) = 0})
        Id := Runtime.AddCorpse("test", 19, aeonfall_horde_trait.None)
        Check("first consumer wins", Runtime.Feed("a", Id))
        Check("consumption replay rejected", logic{not Runtime.Feed("a", Id)?})
        CheckTier(Runtime, "a", 1)
        FeedAmount(Runtime, "a", 1, aeonfall_horde_trait.None)
        CheckTier(Runtime, "a", 2)
        FeedAmount(Runtime, "a", 40, aeonfall_horde_trait.Plated)
        CheckTier(Runtime, "a", 3)
        FeedAmount(Runtime, "a", 80, aeonfall_horde_trait.Sprinter)
        CheckTier(Runtime, "a", 4)
        FeedAmount(Runtime, "a", 160, aeonfall_horde_trait.Spitter)
        CheckTier(Runtime, "a", 4)
        Check("primary trait retained", logic{State := Runtime.GetBrood["a"], State.PrimaryTrait = aeonfall_horde_trait.Plated})
        Check("two trait cap", logic{State := Runtime.GetBrood["a"], State.SecondaryTrait = aeonfall_horde_trait.Sprinter})
        Check("open apex event", Runtime.SetApexEvent("test", true))
        FeedAmount(Runtime, "a", 299, aeonfall_horde_trait.None)
        CheckTier(Runtime, "a", 4)
        FeedAmount(Runtime, "a", 1, aeonfall_horde_trait.None)
        CheckTier(Runtime, "a", 5)
        Check("second brood", Runtime.RegisterBrood("b", "test"))
        for (N := 1..4):
            FeedAmount(Runtime, "b", 300, aeonfall_horde_trait.None)
        CheckTier(Runtime, "b", 4)
        Runtime.RemoveBrood("a")
        Check("close apex event", Runtime.SetApexEvent("test", false))
        FeedAmount(Runtime, "b", 1, aeonfall_horde_trait.None)
        CheckTier(Runtime, "b", 4)
        Check("reopen apex event", Runtime.SetApexEvent("test", true))
        FeedAmount(Runtime, "b", 1, aeonfall_horde_trait.None)
        CheckTier(Runtime, "b", 5)

        Check("other region", Runtime.RegisterBrood("foreign", "other"))
        ForeignCorpse := Runtime.AddCorpse("other", 20, aeonfall_horde_trait.None)
        Check("cross region feed", logic{not Runtime.Feed("b", ForeignCorpse)?})
        Check("cross region denial", logic{not Runtime.UseCorpse("test", ForeignCorpse, aeonfall_corpse_use.Burn)?})
        for (Use : array{aeonfall_corpse_use.Burn, aeonfall_corpse_use.Sanctify, aeonfall_corpse_use.Harvest, aeonfall_corpse_use.Necromancy}):
            BeforeDenial := Runtime.GetRegionalBiomass("test")
            DeniedId := Runtime.AddCorpse("test", 20, aeonfall_horde_trait.None)
            Check("corpse use wins", Runtime.UseCorpse("test", DeniedId, Use))
            Check("denial does not feed biomass", logic{Runtime.GetRegionalBiomass("test") = BeforeDenial})
            Check("denied corpse cannot feed", logic{not Runtime.Feed("b", DeniedId)?})
            Check("duplicate use rejected", logic{not Runtime.UseCorpse("test", DeniedId, Use)?})
        TimedId := Runtime.AddCorpse("test", 20, aeonfall_horde_trait.None)
        Runtime.TickAll(-1.0)
        Check("negative tick ignored", logic{Runtime.GetCorpse[TimedId]})
        Runtime.TickAll(59.99)
        Check("corpse live before expiry", logic{Runtime.GetCorpse[TimedId]})
        Runtime.TickAll(0.02)
        Check("expiry", logic{not Runtime.Feed("b", TimedId)?})
        NewId := Runtime.AddCorpse("test", 20, aeonfall_horde_trait.None)
        Check("ID never reused", logic{NewId > TimedId})
        Runtime.ClearRegion("test")
        Check("region brood cleanup", logic{not Runtime.GetBrood["b"]})
        Check("region corpse cleanup", logic{not Runtime.GetCorpse[NewId]})
        Check("region biomass cleanup", logic{Runtime.GetRegionalBiomass("test") = 0})
        Check("unrelated region preserved", logic{Runtime.GetBrood["foreign"]})

        Small := aeonfall_horde_runtime{Policy := aeonfall_horde_policy{MaxBrood := 1, MaxCorpses := 1}}
        Check("bounded register", Small.RegisterBrood("cap", "test"))
        Check("brood cap", logic{not Small.RegisterBrood("overflow", "test")?})
        FirstId := Small.AddCorpse("test", 20, aeonfall_horde_trait.None)
        Check("first corpse", logic{FirstId > 0})
        Check("corpse cap", logic{Small.AddCorpse("test", 20, aeonfall_horde_trait.None) = 0})
        Small.TickAll(60.0)
        Check("expired slot reusable", logic{Small.AddCorpse("test", 20, aeonfall_horde_trait.None) > FirstId})
        Invalid := aeonfall_horde_runtime{Policy := aeonfall_horde_policy{GorgedBiomass := 0}}
        Check("invalid policy rejected", logic{not Invalid.RegisterBrood("invalid", "test")?})
        Print("HORDE RESULT: {Checks} checks, {Failures} failures")
