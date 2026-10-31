using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Stateless facade: the profile and session registries remain authoritative.
aeonfall_player_loadout_service := class:
    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    IsWeaponId(EntityId:string)<transacts>:logic=
        if (EntityId.Slice[0, 4] = "WPN-"):
            return true
        false

    CanActivateForPlayer(
        Player:player, OwnerKey:string, Definition:aeonfall_ability_definition
    )<transacts>:logic=
        if:
            Player.IsActive[]
            Profile := ProfileService.GetProfile[Player]
            RegisteredOwner := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
            RegisteredOwner = OwnerKey
        then:
            if:
                State := GetAEONFALLClassRuntime().GetState[OwnerKey]
                State.Active?
                State.AbilityIds.Find[Definition.AbilityId]
                Definition.RequiredClassId = "" or Definition.RequiredClassId = State.ClassId
            then:
                return true
            WeaponOwned := IsWeaponId(Definition.OwnerEntityId)
            if (WeaponOwned?):
                if:
                    Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]
                    Profile.EquippedWeaponIds.Find[Definition.OwnerEntityId]
                then:
                    return true
                return false
            # Skills outside the equipped class require their durable unlock.
            # Other capability owners, including owner-exclusive world powers,
            # use their own authenticated controller instead of this facade.
            if:
                Definition.OwnerEntityId.Slice[0, 4] = "SKL-"
                Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]
            then:
                return true
        false

    TrySelectClass(Player:player, ClassId:string)<transacts>:logic=
        if:
            Player.IsActive[]
            Profile := ProfileService.GetProfile[Player]
            Definition := GetAEONFALLClassRegistry().Get[ClassId]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            var Eligible:logic = true
            for (UnlockId : Definition.RequiredUnlockIds):
                if (not Profile.UnlockedEntityIds.Find[UnlockId]):
                    set Eligible = false
            if (Eligible?):
                # ClassRuntime atomically saves selection, passives and resource
                # history; repeated selection cannot refill class resources.
                return GetAEONFALLClassRuntime().ActivateClass(OwnerKey, ClassId)
        false

    TrySelectWeapon(Player:player, WeaponId:string)<transacts>:logic=
        if (CommitWeaponSelection[Player, WeaponId]):
            return true
        false

    CommitWeaponSelection(Player:player, WeaponId:string)<decides><transacts>:void=
        Player.IsActive[]
        IsWeaponId(WeaponId)?
        Old := ProfileService.GetProfile[Player]
        Old.UnlockedEntityIds.Find[WeaponId]
        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        # Durable ownership selects logical equipment. Physical item delivery
        # still requires an explicit project-bound adapter.
        for (AbilityId -> Definition : GetAEONFALLAbilityRegistry().Definitions):
            if (Definition.OwnerEntityId = WeaponId):
                Initialized := GetAEONFALLAbilityRuntime().Initialize(OwnerKey, Definition)
                Initialized?
        Candidate := aeonfall_player_profile:
            MakeAEONFALLPlayerProfile<constructor>(Old)
            EquippedWeaponIds := array{WeaponId}
        Saved := ProfileService.TrySaveProfile(Player, Candidate)
        Saved?

    # The starter unlock is durable. Its initial physical delivery is queued by
    # the device only after this checked save and an active character exists.
    EnsureStarter(Player:player, StarterWeaponId:string)<transacts>:logic=
        if (CommitStarter[Player, StarterWeaponId]):
            return true
        false

    CommitStarter(Player:player, StarterWeaponId:string)<decides><transacts>:void=
        Player.IsActive[]
        IsWeaponId(StarterWeaponId)?
        StarterWeaponId = "WPN-001"
        Old := ProfileService.GetProfile[Player]
        var Unlocks:[]string = Old.UnlockedEntityIds
        if (not Unlocks.Find[StarterWeaponId]):
            set Unlocks += array{StarterWeaponId}
        var Weapons:[]string = Old.EquippedWeaponIds
        if (Weapons.Length = 0):
            set Weapons = array{StarterWeaponId}
        Candidate := aeonfall_player_profile:
            MakeAEONFALLPlayerProfile<constructor>(Old)
            UnlockedEntityIds := Unlocks
            EquippedWeaponIds := Weapons
        Saved := ProfileService.TrySaveProfile(Player, Candidate)
        Saved?

    InitializeEquippedAbilities(Player:player)<transacts>:logic=
        if:
            Profile := ProfileService.GetProfile[Player]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            var Ready:logic = true
            for (AbilityId -> Definition : GetAEONFALLAbilityRegistry().Definitions):
                if:
                    Profile.EquippedWeaponIds.Find[Definition.OwnerEntityId]
                    Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]
                then:
                    Initialized := GetAEONFALLAbilityRuntime().Initialize(OwnerKey, Definition)
                    if (not Initialized?):
                        set Ready = false
            return Ready
        false

AEONFALLPlayerLoadoutService:aeonfall_player_loadout_service = aeonfall_player_loadout_service{}
