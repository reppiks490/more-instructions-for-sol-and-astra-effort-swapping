# Runtime-facing AEONFALL content identity contracts.
# Generated registration code will translate the canonical JSON catalog into
# project-bound definitions that reference actual UEFN assets/devices/prefabs.

aeonfall_content_family := enum:
    Weapon
    Armor
    Relic
    Monster
    Wildlife
    Npc
    Faction
    Boss
    Vehicle
    Skill
    Class
    Material
    Event
    Poi

aeonfall_content_tier := enum:
    Common
    Uncommon
    Rare
    Epic
    Legendary
    Mythic
    Exotic
    God
    Absolute
    TranscendentZero

aeonfall_content_definition := class:
    CanonicalId:string = ""
    DisplayName:string = ""
    Family:aeonfall_content_family = aeonfall_content_family.Weapon
    Tier:aeonfall_content_tier = aeonfall_content_tier.Common
    Role:string = ""
    DependencyIds:[]string = array{}
    RuntimeBindingId:string = ""
    Enabled:logic = true

aeonfall_runtime_binding := class:
    CanonicalId:string = ""
    RuntimeBindingId:string = ""
    PresentationBindingId:string = ""
    AudioBindingId:string = ""
    SpawnBindingId:string = ""
    InventoryBindingId:string = ""
