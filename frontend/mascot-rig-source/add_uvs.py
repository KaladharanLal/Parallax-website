"""Give the rigged mascot mesh a UV map.

The Mixamo skin FBX (Breathing Idle.fbx) ships without any UV layer, so the
exported rig can never sample the character atlas. The unrigged sculpture
(mascot.glb) is the same character in the same pose and already carries a
working UV layout, so its UVs are projected onto the rig and baked into the
mesh.

Run:
  blender --background --factory-startup --python-exit-code 1 \
    --python frontend/mascot-rig-source/add_uvs.py

Writes mascot-rigged.uv.raw.glb (same space as mascot-rigged.raw.glb).
"""

import itertools
import os

import bpy
from mathutils import Matrix, Vector, interpolate, kdtree

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.dirname(HERE)
RIG_GLB = os.path.join(HERE, "mascot-rigged.raw.glb")
STATIC_GLB = os.path.join(FRONTEND, "public", "mascot", "mascot.glb")
OUTPUT = os.path.join(HERE, "mascot-rigged.uv.raw.glb")

CLIP_ORDER = ["Idle", "Walk", "Wave", "Point", "Jump"]


def log(*args):
    print("[uv]", *args, flush=True)


def raw_points(obj):
    matrix = obj.matrix_world
    return [matrix @ v.co for v in obj.data.vertices]


def bounds(points):
    mn = Vector(
        (min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))
    )
    mx = Vector(
        (max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))
    )
    return mn, mx


ROTATIONS = []
for perm in itertools.permutations(range(3)):
    for signs in itertools.product((1, -1), repeat=3):
        matrix = Matrix.Identity(3)
        for row in range(3):
            for col in range(3):
                matrix[row][col] = 0.0
        for axis in range(3):
            matrix[perm[axis]][axis] = signs[axis]
        if abs(matrix.determinant() - 1.0) < 1e-6:
            ROTATIONS.append((perm, signs, matrix))


def fit_transform(rig_points, static_points):
    """Find the rotation + uniform scale + translation that lands the static
    sculpture exactly on the rig, scored by mean nearest-vertex distance."""
    rig_min, rig_max = bounds(rig_points)
    static_min, static_max = bounds(static_points)
    rig_size = rig_max - rig_min
    static_size = static_max - static_min
    rig_center = (rig_min + rig_max) / 2
    static_center = (static_min + static_max) / 2

    rig_sample = rig_points[:: max(1, len(rig_points) // 3000)]
    static_sample = static_points[:: max(1, len(static_points) // 18000)]

    best = None
    for perm, signs, rotation in ROTATIONS:
        rotated = [rotation @ (p - static_center) for p in static_sample]
        rmin, rmax = bounds(rotated)
        rsize = rmax - rmin
        ratios = [
            rig_size[axis] / rsize[axis] for axis in range(3) if abs(rsize[axis]) > 1e-9
        ]
        if len(ratios) != 3:
            continue
        scale = sum(ratios) / 3

        placed = [p * scale + rig_center for p in rotated]
        tree = kdtree.KDTree(len(placed))
        for index, point in enumerate(placed):
            tree.insert(point, index)
        tree.balance()
        total = 0.0
        for point in rig_sample:
            _co, _index, distance = tree.find(point)
            total += distance
        mean = total / len(rig_sample)
        if best is None or mean < best[0]:
            best = (mean, perm, signs, rotation, scale)

    mean, perm, signs, rotation, scale = best
    transform = (
        Matrix.Translation(rig_center)
        @ Matrix.Scale(scale, 4)
        @ rotation.to_4x4()
        @ Matrix.Translation(-static_center)
    )
    log(
        "fit",
        "perm",
        perm,
        "signs",
        signs,
        "scale",
        round(scale, 6),
        "mean distance",
        round(mean, 7),
        f"({mean / max(rig_size) * 100:.2f}% of height)",
    )
    if mean / max(rig_size) > 0.02:
        raise RuntimeError("The sculpture does not line up with the rig; refusing to project")
    return transform


def project_uvs(rig_mesh, static_mesh):
    """Closest-surface UV projection, written per rig vertex."""
    me = static_mesh.data
    loop_uv = me.uv_layers.active.data
    to_static = static_mesh.matrix_world.inverted()
    to_world = rig_mesh.matrix_world

    vertex_uv = {}
    misses = 0
    for vertex in rig_mesh.data.vertices:
        local = to_static @ (to_world @ vertex.co)
        hit, location, _normal, face_index = static_mesh.closest_point_on_mesh(local)
        if not hit:
            misses += 1
            continue
        polygon = me.polygons[face_index]
        corners = [me.vertices[index].co for index in polygon.vertices]
        weights = interpolate.poly_3d_calc(corners, location)
        u = 0.0
        v = 0.0
        for offset, weight in enumerate(weights):
            uv = loop_uv[polygon.loop_start + offset].uv
            u += weight * uv[0]
            v += weight * uv[1]
        vertex_uv[vertex.index] = (u, v)

    log("projected vertices", len(vertex_uv), "misses", misses)
    uv_layer = rig_mesh.data.uv_layers.active
    written = 0
    for loop in rig_mesh.data.loops:
        uv = vertex_uv.get(loop.vertex_index)
        if uv is None:
            continue
        uv_layer.data[loop.index].uv = uv
        written += 1
    log("wrote uv loops", written)


def stage_actions(armature):
    """Recreate one NLA track per clip, in the original export order."""
    if armature.animation_data is None:
        armature.animation_data_create()
    for track in list(armature.animation_data.nla_tracks):
        armature.animation_data.nla_tracks.remove(track)
    armature.animation_data.action = None

    actions = {action.name: action for action in bpy.data.actions}
    ordered = [actions[name] for name in CLIP_ORDER if name in actions]
    ordered += [a for a in bpy.data.actions if a.name not in CLIP_ORDER]

    for action in ordered:
        action.use_fake_user = True
        track = armature.animation_data.nla_tracks.new()
        track.name = action.name
        start = int(round(action.frame_range[0]))
        strip = track.strips.new(action.name, start, action)
        strip.name = action.name
        strip.extrapolation = "NOTHING"
        strip.blend_type = "REPLACE"
        if hasattr(strip, "action_slot") and len(action.slots):
            strip.action_slot = action.slots[0]
        track.mute = False
        log("track", action.name, "range", tuple(round(v, 2) for v in action.frame_range))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0

    log("importing rig", RIG_GLB)
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
    if rig_mesh.data.uv_layers:
        raise RuntimeError("The rig already has a UV map")
    log("rig mesh verts", len(rig_mesh.data.vertices), "bones", len(armature.data.bones))

    log("importing sculpture", STATIC_GLB)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=STATIC_GLB)
    static_meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not static_meshes:
        raise RuntimeError("The static mascot mesh did not import")
    static_mesh = max(static_meshes, key=lambda o: len(o.data.vertices))
    for extra in static_meshes:
        if extra is not static_mesh:
            bpy.data.objects.remove(extra, do_unlink=True)
    if not static_mesh.data.uv_layers:
        raise RuntimeError("The static mascot mesh has no UV map")
    log("static mesh verts", len(static_mesh.data.vertices))

    transform = fit_transform(raw_points(rig_mesh), raw_points(static_mesh))
    static_mesh.matrix_world = transform @ static_mesh.matrix_world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    static_mesh.select_set(True)
    bpy.context.view_layer.objects.active = static_mesh
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    log("sculpture placed on the rig")

    rig_mesh.data.uv_layers.new(name="UVMap")
    log("projecting uvs")
    project_uvs(rig_mesh, static_mesh)

    uv_layer = rig_mesh.data.uv_layers.active
    us = [d.uv[0] for d in uv_layer.data]
    vs = [d.uv[1] for d in uv_layer.data]
    log(
        "uv range",
        round(min(us), 5),
        round(max(us), 5),
        round(min(vs), 5),
        round(max(vs), 5),
    )
    if max(us) - min(us) < 1e-4 or max(vs) - min(vs) < 1e-4:
        raise RuntimeError("UV projection produced a degenerate map")

    bpy.data.objects.remove(static_mesh, do_unlink=True)
    stage_actions(armature)

    bpy.ops.object.select_all(action="DESELECT")
    rig_mesh.select_set(True)
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
