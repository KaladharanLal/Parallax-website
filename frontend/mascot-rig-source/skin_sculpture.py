"""Bind the textured sculpture to the Mixamo skeleton and merge the clips.

The two supplied assets are different meshes:

  mascot.glb         74,822 verts, UVs, full PBR material, no skeleton, no clips
  mascot-rigged.glb  87,656 verts, skeleton + 5 clips, no UV layer at all

Because the meshes differ, the sculpture's UVs and the rig's surfaces cannot be
swapped (that is what produced the random-looking texture), and the rig cannot
sample the sculpture atlas. The robust fix is therefore to keep the textured
mesh exactly as authored and give it the skeleton: transfer the rig's skin
weights onto the sculpture by closest surface, parent it to the armature, and
export one file with the sculpture's textures plus all five clips.

Run:
  blender --background --factory-startup --python-exit-code 1 \
    --python frontend/mascot-rig-source/skin_sculpture.py

Writes mascot-merged.raw.glb (finalize + optimize afterwards).
"""

import os
import sys

import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import add_uvs as A  # noqa: E402  (alignment probe + clip staging + export flags)

RIG_GLB = os.path.join(HERE, "mascot-rigged.raw.glb")
STATIC_GLB = os.path.join(A.FRONTEND, "public", "mascot", "mascot.glb")
OUTPUT = os.path.join(HERE, "mascot-merged.raw.glb")

log = A.log


def import_rig():
    bpy.ops.import_scene.gltf(filepath=RIG_GLB)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("The rig GLB has no mesh")
    rig_mesh = max(meshes, key=lambda o: len(o.data.vertices))
    for extra in meshes:
        if extra is not rig_mesh:
            log("dropping helper mesh", repr(extra.name))
            bpy.data.objects.remove(extra, do_unlink=True)
    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("The rig GLB has no armature")
    armature = max(armatures, key=lambda o: len(o.data.bones))
    for extra in armatures:
        if extra is not armature:
            bpy.data.objects.remove(extra, do_unlink=True)
    log("rig mesh", len(rig_mesh.data.vertices), "verts", len(armature.data.bones), "bones")
    return rig_mesh, armature


def import_sculpture():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=STATIC_GLB)
    meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not meshes:
        raise RuntimeError("The textured mascot mesh did not import")
    sculpture = max(meshes, key=lambda o: len(o.data.vertices))
    for extra in meshes:
        if extra is not sculpture:
            bpy.data.objects.remove(extra, do_unlink=True)
    if not sculpture.data.uv_layers:
        raise RuntimeError("The textured mascot mesh has no UV map")
    log(
        "sculpture",
        len(sculpture.data.vertices),
        "verts",
        len(sculpture.data.materials),
        "materials",
    )
    return sculpture


def weight_source(rig_mesh):
    """World-space triangles + per-vertex weights of the skin."""
    rig_mesh.data.calc_loop_triangles()
    world = [rig_mesh.matrix_world @ v.co for v in rig_mesh.data.vertices]
    tris = [tuple(t.vertices) for t in rig_mesh.data.loop_triangles]
    names = [g.name for g in rig_mesh.vertex_groups]
    weights = [
        {names[g.group]: g.weight for g in vertex.groups if g.weight > 0.0}
        for vertex in rig_mesh.data.vertices
    ]
    bvh = BVHTree.FromPolygons(world, tris, all_triangles=True)
    log("weight source", len(tris), "triangles", len(names), "groups")
    return bvh, world, tris, weights, names


def transfer_weights(sculpture, bvh, world, tris, weights, names):
    groups = {name: sculpture.vertex_groups.new(name=name) for name in names}
    misses = 0
    for vertex in sculpture.data.vertices:
        point = sculpture.matrix_world @ vertex.co
        _location, _normal, index, _distance = bvh.find_nearest(point)
        if index is None:
            misses += 1
            continue
        tri = tris[index]
        corner_weights = poly_3d_calc([world[i] for i in tri], _location)
        acc = {}
        for slot, vertex_index in enumerate(tri):
            share = corner_weights[slot]
            if share <= 1e-5:
                continue
            for name, weight in weights[vertex_index].items():
                acc[name] = acc.get(name, 0.0) + share * weight
        total = sum(acc.values())
        if total <= 1e-6:
            # Fall back to the nearest corner so no vertex is left unweighted.
            acc = dict(weights[tri[0]])
            total = sum(acc.values()) or 1.0
        for name, weight in acc.items():
            group = groups.get(name)
            if group is not None:
                group.add([vertex.index], weight / total, "REPLACE")
    log("weighted", len(sculpture.data.vertices) - misses, "vertices", "misses", misses)
    if misses > len(sculpture.data.vertices) * 0.01:
        raise RuntimeError("Too many vertices found no surface; refusing to bind")


def cleanup_weights(sculpture):
    bpy.ops.object.select_all(action="DESELECT")
    sculpture.select_set(True)
    bpy.context.view_layer.objects.active = sculpture
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    try:
        # Light smoothing removes the seams between neighbouring bone influences
        # without hollowing the deformation.
        bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.3, repeat=1)
        log("weights smoothed")
    except RuntimeError as error:
        log("smooth skipped:", error)
    try:
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
        log("weights limited to 4 influences and normalised")
    except RuntimeError as error:
        log("limit/normalise skipped:", error)
    bpy.ops.object.mode_set(mode="OBJECT")


def bind(sculpture, armature):
    world = sculpture.matrix_world.copy()
    sculpture.parent = armature
    sculpture.parent_type = "OBJECT"
    sculpture.matrix_parent_inverse = armature.matrix_world.inverted()
    sculpture.matrix_world = world
    modifier = sculpture.modifiers.new("Armature", "ARMATURE")
    modifier.object = armature
    modifier.use_vertex_groups = True
    log("bound sculpture to", armature.name)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1.0

    log("importing rig", RIG_GLB)
    rig_mesh, armature = import_rig()
    log("importing sculpture", STATIC_GLB)
    sculpture = import_sculpture()

    transform = A.fit_transform(A.raw_points(rig_mesh), A.raw_points(sculpture))
    sculpture.matrix_world = transform @ sculpture.matrix_world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    sculpture.select_set(True)
    bpy.context.view_layer.objects.active = sculpture
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    log("sculpture aligned to the skin")

    bvh, world, tris, weights, names = weight_source(rig_mesh)
    transfer_weights(sculpture, bvh, world, tris, weights, names)
    cleanup_weights(sculpture)
    bind(sculpture, armature)

    log("removing the untextured skin mesh", repr(rig_mesh.name))
    bpy.data.objects.remove(rig_mesh, do_unlink=True)

    A.stage_actions(armature)

    bpy.ops.object.select_all(action="DESELECT")
    sculpture.select_set(True)
    armature.select_set(True)
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
    log("wrote", round(os.path.getsize(OUTPUT) / 1024), "KB")


if __name__ == "__main__":
    main()
