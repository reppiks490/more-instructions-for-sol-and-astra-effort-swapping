using { /Verse.org/Simulation }

# One power, with two inputs: unveil the sovereign event and toggle the veil.
# The veil is a mode of UNI-001, not a separately unlockable ordinary ability.
aeonfall_sovereign_quest_state := enum:
    Demanded
    Defiant
    Tributed
    Unmade
    Released

aeonfall_sovereign_participant := class:
    Generation:int = 0
    State:aeonfall_sovereign_quest_state = aeonfall_sovereign_quest_state.Demanded
    JoinedAt:float = 0.0
    MayBeEliminated:logic = false

aeonfall_sovereign_command := class:
    Owner:player
    Generation:int
    Slot:int

# Editable regional bindings must point to actual placed native devices.
# Their defaults are deliberately inert until the controller is enabled.
