# Bounded session ecology; records are independent of physical NPC assets.
aeonfall_horde_policy := class:
    MaxBrood:int = 128
    MaxCorpses:int = 128
    CorpseLifetimeSeconds:float = 60.0
    GorgedBiomass:int = 20
    RemadeBiomass:int = 60
    ApostateBiomass:int = 140
    CrownedBiomass:int = 300
    RegionalApexBiomass:int = 600

aeonfall_horde_trait := enum:
    None
    Plated
    Sprinter
    Spitter
    Burrower
    Screamer
    CorpseCarrier

aeonfall_corpse_use := enum:
    Burn
    Sanctify
    Harvest
    Necromancy

aeonfall_horde_brood := class:
    ActorKey:string = ""
    RegionId:string = ""
    Tier:int = 1
    Biomass:int = 0
    PrimaryTrait:aeonfall_horde_trait = aeonfall_horde_trait.None
    SecondaryTrait:aeonfall_horde_trait = aeonfall_horde_trait.None

aeonfall_horde_corpse := class:
    CorpseId:int = 0
    RegionId:string = ""
    Biomass:int = 0
    Trait:aeonfall_horde_trait = aeonfall_horde_trait.None
    RemainingSeconds:float = 0.0
