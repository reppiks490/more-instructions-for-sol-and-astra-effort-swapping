# Omnigod FUS-001: binary-backed 13-plate Sequencer source handoff

This is an offline, source-first deliverable for issues #84 and #88, NOT a
playable prototype or native UEFN asset. The 840-entity, 13-region universe
remains mandatory. Do not credit these specialist assets as reviewed entity packs.

After generating the original geometry, cinematic GLB, WAV cues, and WebVTT
presentation handoff, run:

    python tools/build_omnigod_sequence_tracks.py --output dist/omnigod_cinematics
    python tools/build_omnigod_sequence_tracks.py --output dist/omnigod_cinematics --validate-only
    python -m unittest discover -s tests -p "test_omnigod_sequence_tracks.py" -v

Three generated files: sequencer_track_handoff.json,
sequencer_track_handoff.csv, and sequencer_track_manifest.json.
The tool checks the actual generated GLB's 13 named modules, three clips,
13 translation channels and Eclipse rotation, binary float32 keyframe times,
source hashes, audio/caption owner bindings, and honest native status.
Two phases contain 26 plate tracks, 130 translation keys, 10 camera keys,
three audio starts and three subtitle starts: 146 actual edit-decision rows.

CSV is an editor-readable edit decision list, NOT a native Sequencer import
format. Native UEFN work is still required:

1. Import and retarget the actual skeletal source; verify rig, animation,
   Character Definition, pivots and cm/m coordinate conversion in UEFN.
2. Author two Level Sequences: owner-only camera/audio/subtitles, and
   Everyone-visible replaceable NPC plate presentation. Do not attach a
   replaceable NPC binding to the owner's camera.
3. Author and bind Niagara effects separately. Near 80 particles/2 systems,
   mid 24/1, far 0/0 are UNMEASURED source design ceilings, not measured
   Fortnite mobile performance. Preserve readable noncolor cues.
4. Canonical trusted owner and generation must authorize every cue.
   Cancellation, revocation, logout and separation must stop all owned
   camera/audio/VFX/NPC presentation BEFORE canonical abort. Visuals never
   authorize damage, privileges, NPC possession or hit receipts.
5. Implement reduced-motion static camera (900 cm / 55 degrees), zero
   flashes, no camera shake, captions and touch-safe HUD. Verify in editor.
6. Compile Verse, bind Sequencer/Niagara, test two-client visibility and
   cleanup, mobile frame-time and actual 300 MiB cooked publishing memory
   in native UEFN before claiming any engine success.

FUS-002 remains a separate disabled Titan experiment. No Codex usage,
paid third-party assets, island publication or native tests were involved.
