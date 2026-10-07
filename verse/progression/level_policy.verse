# Canonical AEONFALL level curve.
# Pure helpers live outside services so persistence and runtime gameplay use
# exactly the same 1-1000 progression rules.

AEONFALLMaxLevel:int = 1000

AEONFALLXPForLevel(Level:int):int=
    if (Level <= 1):
        0
    else if (Level >= AEONFALLMaxLevel):
        500 * AEONFALLMaxLevel * AEONFALLMaxLevel
    else:
        500 * Level * Level

AEONFALLGetLevelForXP(XP:int)<transacts>:int=
    var Level:int = 1

    for (CandidateLevel := 2..AEONFALLMaxLevel):
        if (XP >= AEONFALLXPForLevel(CandidateLevel)):
            set Level = CandidateLevel

    Level
