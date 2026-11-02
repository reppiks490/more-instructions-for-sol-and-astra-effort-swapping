"""Blender headless conversion of the Omnigod *source* rigid-skinned GLB to FBX.

Run under an installed Blender environment (bpy required), not plain Python:
  blender --background --python tools/blender_export_omnigod_fbx.py -- \
    --source dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.glb \
    --output dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.fbx

This script has NOT been executed in UEFN or a native Blender install by CI.
Inspect bone axes/scale, material slots, skinning and animation Actions in a
real DCC before importing to UEFN. This is not an authored humanoid skeleton.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main():
    try:
        import bpy
    except ImportError as error:
        raise RuntimeError("Run this script inside Blender with bpy available.") from error
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    opts=parser.parse_args(args)
    source=opts.source.expanduser().resolve()
    output=opts.output.expanduser().resolve()
    if not source.is_file() or source.suffix.lower()!=".glb":
        raise RuntimeError("Expected the checked AEONFALL rigid-skinned GLB")
    if output.suffix.lower()!=".fbx":
        raise RuntimeError("Expected an FBX export output path")
    if source==output:
        raise RuntimeError("Refusing to overwrite source")
    # Temporary background scene only. This does not touch any user .blend
    # file or the original source asset.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    rigs=[obj for obj in bpy.data.objects if obj.type=="ARMATURE"]
    meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]
    if len(rigs)!=1 or len(meshes)!=13:
        raise RuntimeError(f"Expected one armature and 13 skinned meshes; got {len(rigs)} rig(s), {len(meshes)} meshes")
    rig=rigs[0]
    required={"J_OMNI_"+part for part in (
        "Torso","Crown","Pauldron_L","Pauldron_R","Reactor","Gauntlet_L",
        "Gauntlet_R","Hips","Greave_L","Greave_R","AxiomCore","Eclipse","SiegeBlade"
    )}
    if not required.issubset(set(rig.data.bones.keys())):
        raise RuntimeError("Imported mechanical rig has missing bones")
    for obj in meshes:
        if not any(mod.type=="ARMATURE" and mod.object==rig for mod in obj.modifiers):
            raise RuntimeError(f"Missing armature skin modifier: {obj.name}")
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in rigs+meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    result=bpy.ops.export_scene.fbx(
        filepath=str(output),use_selection=True,
        object_types={"ARMATURE","MESH"},global_scale=1.0,
        apply_unit_scale=True,axis_forward="-Y",axis_up="Z",
        add_leaf_bones=False,primary_bone_axis="Y",secondary_bone_axis="X",
        bake_anim=True,bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,
        use_mesh_modifiers=True
    )
    if "FINISHED" not in result or not output.is_file() or output.stat().st_size<1024:
        raise RuntimeError("FBX export failed or output was empty")
    print(f"Exported {len(meshes)} skin meshes, {len(required)} mechanical plate bones to {output}")
    print("UEFN import and actual locomotion animation have NOT been tested.")


if __name__=="__main__":
    main()
