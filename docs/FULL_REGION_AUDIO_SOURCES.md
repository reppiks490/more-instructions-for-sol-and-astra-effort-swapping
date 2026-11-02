# AEONFALL — Original audio source identities across ALL 13 regions

**Scope:** 39 actual generated 16-bit PCM WAV files (13 region identities × 3
original functional cue roles), supporting the complete-universe-first
directive. This work supplies *real source audio*, not source-only text
descriptions. It does **not** imply 13 complete produced soundscapes, sound
device import, a native soundtrack, NPC audio, gameplay trigger binding or
Fortnite mobile playback.

## New distinct audio source packages

Each region has an original deterministic sound-source identity, encoded by
a separate pitch structure and modulation contour. The generator produces:

- **Ambient**: a 4-second phase-periodic tonal environment layer. It is a
  calm regional identity bed and is appropriate as one component of a
  final environmental mix, not a final seamless production music score.
- **Danger**: a 1.2-second clearly bounded, rising region-specific warning.
  This should pair with an icon/shape warning and readable combat telegraph,
  not replace visuals.
- **Navigation**: a 420-millisecond short waypoint/region confirmation
  tone, paired with accessible route text or another non-audio cue.

| Region | Original source character |
|---|---|
| REG-001 The Ossuary March | Bone resonance and blackwater pressure |
| REG-002 Black Sun Meridian | Dry eclipse gong and solar wind |
| REG-003 Crownless Tempest | Conductors and electrical arcing |
| REG-004 Leviathan Red Coast | Submerged leviathan lament and tidal swell |
| REG-005 Worldroot Cathedral | Wooden harmonics and canopy breath |
| REG-006 Court of Broken Hours | Fractured clock chimes and temporal beating |
| REG-007 Infernal Ledgerlands | Furnace harmonics and iron pulse |
| REG-008 Glass Wyrm Expanse | Crystal/glass resonance and shard shimmer |
| REG-009 Hollow Astral Synod | Orrery and celestial low bell |
| REG-010 Null Cartography | Null-phase displacement |
| REG-011 Titan's Last Orchard | Fossil resonance and heavy ground groan |
| REG-012 The Axiom Scar | Axiom law dissonance |
| REG-013 Threshold of Zero | Minimal distant singularity tone |

The source synthesis is original mathematical PCM, without external
samples, commercial music, paid generators, model calls or licensing claims
for third-party work.

## Reproducible real WAV build

```powershell
python tools/build_all_region_audio.py --output dist/full_universe_region_audio
python tools/validate_all_region_audio.py --output dist/full_universe_region_audio
python -m unittest discover -s tests -p "test_all_region_audio.py" -v
```

The [dedicated complete-region sound workflow](../.github/workflows/full-universe-region-audio.yml)
generates a real source archive containing 39 WAV binaries and a manifest.
Source code remains durable after the GitHub Actions artifact expires.

All audio is signed **mono 16-bit PCM at 24,000Hz**, exported via a strict
44-byte RIFF/WAVE header with exact sample count and no hidden timestamps.
There are 39 distinct source hashes; the sound validator parses the actual
WAV binary, checks every sample and SHA-256 checksum, checks the intended
duration, overall bounded peak amplitude and RMS, validates loop-edge
continuity, and verifies each region-specific PCM source. Corrupt headers,
truncation, region swaps, fake native import proof and dishonest source
metrics must fail.

These modest PCM levels and 24kHz sample rate are only source authoring
controls. **No LUFS meter, calibrated hearing safety test, platform audio
mix or UEFN compression tests have been performed.** Final designers must
measure audio with actual sound equipment and platform mix.

## Required native gameplay/audio work remains

Before region-level `vfx_audio` source delivery can be reviewed as
complete, designers still need full region-environment music/ambience
layers, event/stinger coverage, footsteps, character/creature sounds,
mechanical soundbanks, unique quest and boss cues, actual particle/VFX
source assets, streaming and spatialization strategies, reduced-effects
fallback, subtitles, audio priority arbitration, and a cross-device
accessibility review.

UEFN native integration must import, configure and bind audio sources to
supported Audio Player and other verified devices and actual event
triggers. Validate in real Fortnite mobile gameplay: positional audio,
voice-chat interference, on/off transitions, fade/loop discontinuities,
multiple-client replication, volume controls, caption equivalents and
runtime audio memory use.

The `content/implementation/universe_source_delivery_inventory.json`
registry must **not** credit a complete reviewed regional `vfx_audio`
package merely because 3 tonal WAV sources exist. This work advances
a distinct piece of the full 840-entity/13-region audio source substrate,
not its UEFN-native release gate.

Existing five hourly Omnigod loops remain unchanged, with Codex banned.
No live island publication, new spending, deleted branches, owner
entitlement change or external audio service is involved.
