#!/usr/bin/env python3
"""Deterministic ORIGINAL Omnigod manifestation blockout, not a playable NPC.

Generates separate static, original armor geometry plus an assembled glTF preview.
Reuse the Ossuary's tested watertight-mesh/OBJ/GLB encoder; do not change
canonical AEONFALL entities, persistent profiles, native UEFN assets or access.
Coordinate convention: X east, Y north, Z up in meters. Positive Y is rear.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ossuary_starter_assets as geometry

DEFAULT_OUTPUT = ROOT / "dist/omnigod_manifestation"
PACK_ID = "AEONFALL-OMNIGOD-MANIFESTATION-SOURCE-001"
# Independent material indices, resolved by a temporary palette override only
# during encoding. Generated emissive channels are NOT actual UEFN lights/VFX.
MATERIALS = [
    ("AbyssalObsidian", (0.028, 0.018, 0.045, 1.0), 0.83, 0.36, None),
    ("BlackIron", (0.072, 0.054, 0.087, 1.0), 0.88, 0.29, None),
    ("BloodCrimson", (0.43, 0.018, 0.050, 1.0), 0.62, 0.28, None),
    ("AxiomViolet", (0.35, 0.075, 0.64, 1.0), 0.22, 0.36, (0.42, 0.14, 0.7)),
    ("SolarRift", (0.78, 0.025, 0.115, 1.0), 0.18, 0.26, (0.72, 0.05, 0.12)),
    ("BoneChrome", (0.47, 0.42, 0.50, 1.0), 0.78, 0.37, None),
    ("VoidVein", (0.075, 0.018, 0.12, 1.0), 0.43, 0.28, (0.13, 0.02, 0.25)),
    ("AncientGold", (0.38, 0.23, 0.11, 1.0), 0.70, 0.28, None),
]
# Each anchor is in Unreal centimeters, and the corresponding mesh uses its
# OWN local pivot. These are not skeletal sockets or an imported character rig.
ANCHORS = {
    "Torso": ((0, 0, 289), "chest_core", "chassis"),
    "Crown": ((0, -7, 425), "head", "shell"),
    "Pauldron_L": ((-115, 0, 362), "shoulder_l", "shell"),
    "Pauldron_R": ((115, 0, 362), "shoulder_r", "shell"),
    "Reactor": ((0, 63, 288), "spine", "reactor"),
    "Gauntlet_L": ((-131, -19, 236), "hand_l", "weapon_armor"),
    "Gauntlet_R": ((131, -19, 236), "hand_r", "weapon_armor"),
    "Hips": ((0, 0, 196), "pelvis", "shell"),
    "Greave_L": ((-57, 0, 88), "foot_l", "shell"),
    "Greave_R": ((57, 0, 88), "foot_r", "shell"),
    "AxiomCore": ((0, -72, 302), "chest_core", "emissive"),
    "Eclipse": ((0, 108, 349), "back_vfx", "cosmetic"),
    "SiegeBlade": ((216, -48, 110), "weapon_r", "weapon"),
}
MAX_TRIANGLES_PER_PACK = 9000
MAX_PARTS = 16


def create_parts():
    parts = []
    def new(suffix: str, purpose: str):
        mesh = geometry.Mesh("SM_AEON_OMNI_" + suffix, purpose)
        parts.append(mesh)
        return mesh

    m = new("Torso", "Broad tank chassis; interlocked black iron, crimson ribs and central chest recess.")
    m.box((0, 0, 0), (2.12, 1.26, 2.08), 0, "central_tank_chest")
    m.box((0, -0.73, 0.23), (1.78, 0.22, 1.34), 1, "upper_armor_wall")
    for sign in (-1, 1):
        m.xz_extrusion(((sign*0.72,-0.85),(sign*1.18,-0.62),(sign*1.35,0.43),
                        (sign*0.80,0.93)), 0.34, 1, f"rib_shield_{sign}")
        m.box((sign*0.80,-0.84,0.23), (0.12,0.10,1.45),2,f"crimson_chest_trace_{sign}")
        m.box((sign*0.32,-0.88,-0.57),(0.12,.06,.45),3,f"violet_sternum_trace_{sign}")
    m.box((0,-0.91,0.26),(0.98,.11,.72),0,"axiom_socket_bezel")
    m.box((0,.54,.15),(1.30,.28,1.85),1,"spine_attach")

    m = new("Crown", "Horned diabolical helm, articulated silhouette with closed source solids.")
    m.box((0,0,0),(0.93,0.95,0.92),0,"skull_vault")
    m.xz_extrusion(((-0.60,-.08),(-.42,-.72),(0,-.84),(.42,-.72),(.60,-.08),
                    (.45,.16),(-.45,.16)),.69,1,"lower_jaw")
    m.box((0,-0.55,.06),(.79,.11,.22),5,"visor_bridge")
    for sign in (-1,1):
        m.xz_extrusion(((sign*.08,.05),(sign*.37,.17),(sign*.38,.30),(sign*.10,.22)),
                       .07,3,f"eye_slit_{sign}")
        # Convex triangular blade segments rather than a concave swept
        # polygon. Closed, consistently oriented solids survive OBJ/GLB export.
        m.xz_extrusion(((sign*.36,.33),(sign*.85,.42),(sign*1.07,1.67)),
                       .34,0,f"outer_horn_{sign}")
        m.xz_extrusion(((sign*.17,.37),(sign*.51,.41),(sign*.43,1.17)),
                       .25,5,f"inner_horn_{sign}")
    m.box((0,-.52,-.51),(.20,.12,.60),2,"central_crimson_fang")

    for sign,suffix in ((-1,"L"),(1,"R")):
        m=new("Pauldron_"+suffix,"Detached siege-plate shoulder; asymmetric bevels, crimson stripes and intimidation spines.")
        m.box((0,0,-.03),(1.46,1.46,1.04),1,"shoulder_carapace")
        m.xz_extrusion(((sign*-.89,.30),(sign*.16,.57),(sign*.92,.34),
                        (sign*1.12,-.32),(sign*.69,-.58),(sign*-.75,-.43)),
                       1.30,0,"outer_siege_shell")
        m.xz_extrusion(((sign*-.21,.47),(sign*.10,.87),(sign*.40,1.30),
                        (sign*.30,.63)),.28,5,"titan_spine_inner")
        m.xz_extrusion(((sign*.46,.23),(sign*.74,.84),(sign*.93,1.50),
                        (sign*.87,.38)),.25,0,"titan_spine_outer")
        m.box((0,-.83,.11),(1.19,.12,.13),2,"blood_edge")
        m.box((sign*.36,-.92,-.25),(.11,.05,.43),3,"violet_reactor_trace")

    m=new("Reactor","Detached spinal power-turbine assembly with emissive exhaust vents.")
    m.box((0,0,0),(.70,.73,1.73),1,"reactor_block")
    for sign in (-1,1):
        m.xz_extrusion(((sign*.22,-.60),(sign*.84,-.90),
                        (sign*.93,.72),(sign*.37,.54)),.43,0,f"back_vane_{sign}")
        m.box((sign*.63,.35,.10),(.12,.12,1.17),4,f"red_exhaust_{sign}")
        m.box((sign*.35,.41,.52),(.13,.11,.56),3,f"violet_conduit_{sign}")
    m.box((0,.47,0),(.35,.10,1.45),7,"ancient_seal")

    for sign,suffix in ((-1,"L"),(1,"R")):
        m=new("Gauntlet_"+suffix,"Massive armored fist and three weaponized claws.")
        m.box((0,0,.10),(.90,.98,1.53),1,"forearm_shell")
        m.box((0,-.62,.18),(.76,.18,1.32),0,"front_guard")
        m.box((0,-.74,.30),(.68,.06,.15),2,"blood_lock")
        for finger in (-1,0,1):
            x=finger*.33
            m.taper((x,-.33),.19,.13,-1.20,-.51,5,f"claw_joint_{finger}",6)
            m.taper((x,-.33),.13,.018,-1.73,-1.20,0,f"claw_tip_{finger}",6)
        m.box((sign*.43,-.43,.32),(.10,.10,.88),3,"purple_plasma_seam")

    m=new("Hips","Flared armored belt, segmented demonic skirt and rear actuator.")
    m.box((0,0,.12),(1.68,1.25,.88),0,"pelvic_core")
    m.box((0,-.75,.04),(1.29,.17,.66),7,"royal_belt")
    for sign in (-1,1):
        m.xz_extrusion(((sign*.42,.44),(sign*1.14,.14),
                        (sign*1.25,-.99),(sign*.54,-.73)),.63,1,f"skirt_fang_{sign}")
        m.box((sign*.66,-.88,-.26),(.10,.10,.60),2,f"skirt_seam_{sign}")

    for sign,suffix in ((-1,"L"),(1,"R")):
        m=new("Greave_"+suffix,"Fortress-leg shield with wedge toe and armored ankle.")
        m.box((0,0,.16),(.80,.88,1.65),1,"leg_bulk")
        m.xz_extrusion(((-.43,.87),(.42,.79),(.53,-.48),(-.50,-.61)),.76,0,"outer_shin")
        m.box((0,-.47,-.41),(.80,1.23,.42),0,"oversized_boot")
        m.xz_extrusion(((-.32,-.35),(.32,-.35),(.53,-.75),(-.51,-.75)),1.24,5,"toe_keel")
        m.box((sign*.25,-.54,.17),(.12,.09,1.12),2,"blood_shin_trace")

    m=new("AxiomCore","Isolated chest-origin ember/crystal; can be animated separately.")
    m.taper((0,0),.41,.27,-.24,.18,4,"crimson_heart_lower",8)
    m.taper((0,0),.27,.03,.18,.56,3,"violet_heart_spike",8)
    for sign in (-1,1):
        m.box((sign*.39,-.08,.07),(.10,.13,.62),5,f"core_spur_{sign}")
    m.box((0,-.28,-.05),(.52,.10,.23),6,"void_conduit")

    m=new("Eclipse","Rear cosmetic ring of 16 detachable void-sun plates; no collision.")
    for segment in range(16):
        a=segment*math.tau/16
        b=(segment+1)*math.tau/16
        inner,outer=1.67,2.12
        ring=((inner*math.cos(a),inner*math.sin(a)),
              (outer*math.cos(a),outer*math.sin(a)),
              (outer*math.cos(b),outer*math.sin(b)),
              (inner*math.cos(b),inner*math.sin(b)))
        # xz extrusion expects (x,z); the hole remains physically open.
        m.xz_extrusion(ring,.14,0,f"eclipse_plate_{segment}")
        if segment%2 == 0:
            m.xz_extrusion((((outer+.02)*math.cos(a), (outer+.02)*math.sin(a)),
                            ((outer+.26)*math.cos(a), (outer+.26)*math.sin(a)),
                            ((outer+.24)*math.cos(b), (outer+.24)*math.sin(b)),
                            ((outer+.02)*math.cos(b), (outer+.02)*math.sin(b))),
                           .08,4,f"crimson_corona_{segment}")

    m=new("SiegeBlade","Creator-only ornamental double-edged sword mesh, NOT a weapon grant.")
    m.box((0,0,.22),(.28,.31,.94),1,"weapon_grip")
    m.box((0,0,.79),(1.50,.40,.28),7,"titan_crossguard")
    m.xz_extrusion(((-.48,.83),(-.48,2.79),(-.24,3.48),(0,3.93),
                    (.24,3.48),(.48,2.79),(.48,.83)),.18,5,"sword_edge")
    m.xz_extrusion(((-.23,.93),(-.21,3.05),(0,3.48),
                    (.21,3.05),(.23,.93)),.24,0,"void_blade_spine")
    m.box((0,-.21,2.17),(.10,.08,2.10),4,"crimson_edge")
    m.box((0,-.27,1.16),(.22,.09,.27),3,"axiom_hilt")
    geometry.check_geometry(parts)
    return parts


def build_placements(parts):
    if {p.name.removeprefix("SM_AEON_OMNI_") for p in parts} != set(ANCHORS):
        raise ValueError("anchor/mesh component mismatch")
    placements=[]
    for part in parts:
        suffix=part.name.removeprefix("SM_AEON_OMNI_")
        location, socket, role=ANCHORS[suffix]
        placements.append({
            "name":"Prototype_"+suffix, "mesh":part.name,
            "location_cm":list(location), "rotation_deg":[0,0,0],
            "scale":[1,1,1], "zone":"Omnigod_Dormant_Throne",
            "role":role,"planned_socket":socket,
            "collision":"disabled_for_cosmetic_proxy"
        })
    return placements


def generate(output: Path):
    output=output.resolve()
    (output/"meshes").mkdir(parents=True,exist_ok=True)
    parts=create_parts()
    placements=build_placements(parts)
    triangles=sum(sum(len(indices)//3 for indices in p.material_indices.values()) for p in parts)
    if not 10 <= len(parts) <= MAX_PARTS or triangles > MAX_TRIANGLES_PER_PACK:
        raise ValueError("blockout geometry has exceeded source package budget")
    # The Ossuary exporter shares geometry code, but our material palette
    # must not alter its global state for other generators or unit tests.
    old_palette=geometry.MATERIALS
    try:
        geometry.MATERIALS=MATERIALS
        for mesh in parts:
            (output/"meshes"/(mesh.name+".glb")).write_bytes(geometry.encode_glb([mesh]))
            geometry.write_obj(mesh,output/"meshes"/(mesh.name+".obj"))
        (output/"omnigod_dormant_assembly.glb").write_bytes(
            geometry.encode_glb(parts,placements))
    finally:
        geometry.MATERIALS=old_palette
    files=[]
    for f in sorted(output.rglob("*")):
        if f.is_file() and f.suffix in (".glb",".obj",".mtl"):
            data=f.read_bytes()
            files.append({"path":f.relative_to(output).as_posix(),
                          "sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
    manifest={
        "schema_version":1, "pack_id":PACK_ID, "status":"original_static_blockout_editor_import_not_run",
        "provenance":{"original":True,"source_generator":"tools/build_omnigod_manifestation_assets.py",
                      "shared_geometry_encoder":"tools/build_ossuary_starter_assets.py",
                      "external_geometry":False},
        "canonical_fusion_mode":"FUS-001", "titan_mode":"FUS-002",
        "npc_possession_implemented":False,"skeletal_mesh_implemented":False,
        "owner_entitlement_granted":False,
        "native_uefn_import":"not_run","verse_compile":"not_run","launch_session":"not_run",
        "visual_intent":"colossal obsidian machine-demon with crimson/violet reactor, 16-piece eclipse and ancient siege weapon",
        "materials":[{"name":m[0],"rgba":m[1],"metallic":m[2],
                      "roughness":m[3],"emission":m[4]} for m in MATERIALS],
        "coordinate_system":{"source":"meters X east Y north Z up",
                             "obj":"centimeters X east Y north Z up",
                             "glb":"glTF2 meters Y up, source (x,y,z) -> (x,z,-y)",
                             "local_pivots":"each armor module local origin; placements in Unreal cm"},
        "parts":[{"id":p.name,"purpose":p.purpose,
                  "triangles":sum(len(v)//3 for v in p.material_indices.values()),
                  "bounds_m":p.bounds()} for p in parts],
        "placements":placements,
        "import":{"preferred":"separate modules; rig/retarget manually before custom NPC implementation",
                  "assembly":"omnigod_dormant_assembly.glb is a static composition preview only",
                  "collision":"disable cosmetic static-mesh collision; actual NPC uses tested capsule/navmesh",
                  "materials":"UEFN shader/emissive/Niagara authoring required; MTL/GLB materials are preview-only",
                  "animation":"rig the detachables in a DCC; add skeleton, animations and NPC Character Definition in UEFN",
                  "sequencer_visibility":"NPC replaceable bindings require Everyone; keep owner-only player cinematic separate"},
        "budget":{"parts":len(parts),"unique_triangles":triangles,"maximum_triangles":MAX_TRIANGLES_PER_PACK,
                  "source_meshes":len(parts),"physical_spawns":0},
        "files":files,
        "limitations":[
            "Geometry and 3D preview are generated; no skeletal mesh, runtime animation or Fortnite outfit.",
            "No UE project files or native NPC Character Definition, collision, cooked asset or VFX graphs.",
            "This source pack is NOT evidence of an imported/possessed NPC, real-world rule override, or successful Launch Session.",
            "Performance, LOD, materials, socket alignment and physics require in-editor verification."
        ]}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=p.parse_args()
    result=generate(args.output)
    print(json.dumps(result["budget"],sort_keys=True))
    print(f"Generated original Omnigod manifestation source: {args.output}")


if __name__=="__main__":
    main()
