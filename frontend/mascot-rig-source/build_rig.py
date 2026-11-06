"""Build frontend/public/mascot/mascot-rigged.glb.

Run with:
  blender --background --factory-startup --python-exit-code 1 \
    --python frontend/mascot-rig-source/build_rig.py

The skinned Idle FBX supplies the character and skeleton. The other four FBX
files supply animation only. Textures are reused from the existing optimized
mascot.glb, which has the same UV layout. The result is decimated for the web;
run gltf-transform afterwards to compress the result.
"""

import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.dirname(HERE)
STATIC_GLB = os.path.join(FRONTEND, "public", "mascot", "mascot.glb")
OUTPUT = os.path.join(HERE, "mascot-rigged.raw.glb")
DECIMATE_RATIO = 0.085

CLIPS = [
    ("Breathing Idle.fbx", "Idle"),
    ("Start Walking.fbx", "Walk"),
    ("Waving.fbx", "Wave"),
    ("Pointing Forward.fbx", "Point"),
    ("Jumping.fbx", "Jump"),
]

EXPECTED_BONES = 33


def log(*args):
    print("[mascot-rig]", *args, flush=True)


def action_curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def action_summary(action):
    curves = list(action_curves(action))
    paths = sorted({fc.data_path for fc in curves})
    return {
        "name": action.name,
        "range": tuple(round(v, 2) for v in action.frame_range),
        "curves": len(curves),
        "bones": sorted(
            {
                fc.data_path.split('"')[1]
                for fc in curves
                if fc.data_path.startswith('pose.bones["') and '"' in fc.data_path
            }
        ),
        "paths": paths[:6],
    }


def find_active_action(armature):
    if armature.animation_data and armature.animation_data.action:
        return armature.animation_data.action
    candidates = [
        action
        for action in bpy.data.actions
        if any(True for _ in action_curves(action))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda action: len(list(action_curves(action))))


def add_track(armature, action, name):
    if not armature.animation_data:
        armature.animation_data_create()
    track = armature.animation_data.nla_tracks.new()
    track.name = name
    start = int(round(action.frame_range[0]))
    strip = track.strips.new(name, start, action)
    strip.name = name
    strip.extrapolation = "NOTHING"
    strip.blend_type = "REPLACE"
    if hasattr(strip, "action_slot") and len(action.slots):
        strip.action_slot = action.slots[0]
    log("track", name, "start", start, "range", tuple(round(v, 2) for v in action.frame_range))
    return track


def apply_object_scale(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def scale_action_locations(action, factor):
    """Mixamo bakes location keys in centimetres while the armature object is
    scaled by 0.01. After applying that scale to the armature data, the pose
    location curves must be converted to metres too."""
    count = 0
    for fcurve in action_curves(action):
        if not fcurve.data_path.endswith(".location"):
            continue
        for key in fcurve.keyframe_points:
            key.co[1] *= factor
            key.handle_left[1] *= factor
            key.handle_right[1] *= factor
        fcurve.update()
        count += 1
    log("scaled location curves", action.name, count, "x", factor)


def find_rig_mesh(armature):
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if any(
            mod.type == "ARMATURE" and mod.object == armature
            for mod in obj.modifiers
        ):
            return obj
    raise RuntimeError("No mesh is bound to the imported Mixamo armature")


def main():
    started = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0

    idle_file = os.path.join(HERE, CLIPS[0][0])
    log("importing skin", idle_file)
    bpy.ops.import_scene.fbx(filepath=idle_file, use_anim=True)

    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError(f"Expected one armature in Idle, found {len(armatures)}")
    armature = armatures[0]
    rig_mesh = find_rig_mesh(armature)
    log("armature", armature.name, "bones", len(armature.data.bones), "mesh", rig_mesh.name)
    if len(armature.data.bones) < EXPECTED_BONES:
        raise RuntimeError("The Idle rig does not look like the expected Mixamo skeleton")

    idle_action = find_active_action(armature)
    if idle_action is None:
        raise RuntimeError("The Idle FBX did not contain an animation action")
    idle_action.name = "Idle"
    idle_action.use_fake_user = True
    log("idle", action_summary(idle_action))

    # Use the already-shipped, web-optimized texture set. It is the same
    # character and UV layout as the Mixamo skin.
    before_static = set(bpy.data.objects)
    log("importing texture material", STATIC_GLB)
    bpy.ops.import_scene.gltf(filepath=STATIC_GLB)
    static_meshes = [
        obj
        for obj in bpy.data.objects
        if obj not in before_static and obj.type == "MESH"
    ]
    if not static_meshes:
        raise RuntimeError("Could not import the existing mascot material")
    static_mesh = static_meshes[0]
    if not static_mesh.data.materials:
        raise RuntimeError("The existing mascot material is missing")
    material = static_mesh.data.materials[0]
    log("material", material.name, "images", [img.name for img in bpy.data.images if img.size[0]])
    rig_mesh.data.materials.clear()
    rig_mesh.data.materials.append(material)
    for obj in [obj for obj in bpy.data.objects if obj not in before_static]:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Remove the FBX light / helper empties; keep only the rig and skin.
    for obj in list(bpy.data.objects):
        if obj not in {armature, rig_mesh}:
            bpy.data.objects.remove(obj, do_unlink=True)

    # The FBX armature is in centimetres with a 0.01 object scale, while the
    # mesh scale is baked differently. Normalize both to metres before export so
    # the glTF root has no residual scale and the skin and skeleton line up.
    apply_object_scale(armature)
    apply_object_scale(rig_mesh)
    # The FBX importer's 90-degree armature rotation only exists to present the
    # Y-up Mixamo character in Blender's Z-up viewport. glTF is Y-up, so the
    # exported root must be upright rather than lying on its back.
    armature.rotation_mode = "QUATERNION"
    armature.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    scale_action_locations(idle_action, 0.01)
    log(
        "normalized scale",
        "armature", tuple(round(v, 4) for v in armature.scale),
        "mesh", tuple(round(v, 4) for v in rig_mesh.scale),
        "dims", tuple(round(v, 3) for v in rig_mesh.dimensions),
    )

    log(
        "mesh before decimate",
        "verts", len(rig_mesh.data.vertices),
        "polys", len(rig_mesh.data.polygons),
        "groups", len(rig_mesh.vertex_groups),
    )
    bpy.context.view_layer.objects.active = rig_mesh
    rig_mesh.select_set(True)
    decimate = rig_mesh.modifiers.new("Mascot Decimate", "DECIMATE")
    decimate.decimate_type = "COLLAPSE"
    decimate.ratio = DECIMATE_RATIO
    decimate.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=decimate.name)
    log(
        "mesh after decimate",
        "verts", len(rig_mesh.data.vertices),
        "polys", len(rig_mesh.data.polygons),
        "groups", len(rig_mesh.vertex_groups),
        "mods", [mod.type for mod in rig_mesh.modifiers],
    )

    # The Idle action arrives assigned to the armature. Move it onto an NLA
    # track, then extract each animation-only FBX onto its own track.
    armature.animation_data_create()
    armature.animation_data.action = idle_action
    if idle_action.slots:
        armature.animation_data.action_slot = idle_action.slots[0]
    for track in list(armature.animation_data.nla_tracks):
        armature.animation_data.nla_tracks.remove(track)
    add_track(armature, idle_action, "Idle")
    armature.animation_data.action = None

    target_bones = set(armature.data.bones.keys())
    for filename, clip_name in CLIPS[1:]:
        path = os.path.join(HERE, filename)
        log("importing animation", clip_name, path)
        before_objects = set(bpy.data.objects)
        before_actions = set(bpy.data.actions)
        bpy.ops.import_scene.fbx(filepath=path, use_anim=True)

        new_armatures = [
            obj
            for obj in bpy.data.objects
            if obj not in before_objects and obj.type == "ARMATURE"
        ]
        if not new_armatures:
            raise RuntimeError(f"No armature found in {filename}")
        source_armature = new_armatures[0]

        new_actions = [
            action for action in bpy.data.actions if action not in before_actions
        ]
        action = (
            source_armature.animation_data.action
            if source_armature.animation_data
            and source_armature.animation_data.action
            else None
        )
        if action is None and new_actions:
            action = max(new_actions, key=lambda item: len(list(action_curves(item))))
        if action is None:
            raise RuntimeError(f"No animation action found in {filename}")

        action.name = clip_name
        action.use_fake_user = True
        scale_action_locations(action, 0.01)
        summary = action_summary(action)
        missing = set(summary["bones"]) - target_bones
        log(
            "action",
            clip_name,
            "range", summary["range"],
            "curves", summary["curves"],
            "missing_bones", sorted(missing),
        )
        if missing:
            raise RuntimeError(f"{clip_name} targets bones missing from the skin: {sorted(missing)}")

        add_track(armature, action, clip_name)

        for obj in [obj for obj in bpy.data.objects if obj not in before_objects]:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

    armature.animation_data.action = None
    for track in armature.animation_data.nla_tracks:
        track.mute = False

    log("tracks", [track.name for track in armature.animation_data.nla_tracks])
    log("actions", [action.name for action in bpy.data.actions])

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    rig_mesh.select_set(True)
    bpy.context.view_layer.objects.active = armature

    log("exporting", OUTPUT)
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT,
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_yup=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_merge_animation="NLA_TRACK",
        export_nla_strips=True,
        export_frame_range=False,
        export_force_sampling=True,
        export_sampling_interpolation_fallback="LINEAR",
        export_anim_slide_to_zero=True,
        export_rest_position_armature=True,
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_armature=True,
        export_anim_single_armature=True,
        export_skins=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_extras=False,
    )
    log("done in", round(time.time() - started, 1), "s", "bytes", os.path.getsize(OUTPUT))


if __name__ == "__main__":
    main()
