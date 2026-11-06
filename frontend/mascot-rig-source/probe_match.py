"""Measure how well the static sculpture lines up with the rigged skin.

Both assets are the same character, but Blender's glTF import can land each
one in a different orientation. This probe tries every orientation-preserving
axis rotation and reports the mean distance from rig vertices to the nearest
static vertex, so we can tell whether a UV projection is valid and which
transform to use.

Run:
  blender --background --factory-startup --python-exit-code 1 \
    --python frontend/mascot-rig-source/probe_match.py
"""

import itertools
import os

import bpy
from mathutils import Matrix, Vector, kdtree

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.dirname(HERE)
RIG_GLB = os.path.join(HERE, "mascot-rigged.raw.glb")
STATIC_GLB = os.path.join(FRONTEND, "public", "mascot", "mascot.glb")


def log(*args):
    print("[match]", *args, flush=True)


def raw_points(obj):
    matrix = obj.matrix_world
    return [matrix @ v.co for v in obj.data.vertices]


def bounds(points):
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return mn, mx


# All 24 orientation-preserving rotations of the cube.
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
log("rotations", len(ROTATIONS))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=RIG_GLB)
    rig_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    rig_mesh = max(rig_meshes, key=lambda o: len(o.data.vertices))
    rig_points = raw_points(rig_mesh)
    rig_min, rig_max = bounds(rig_points)
    log("rig verts", len(rig_points))
    log("rig bounds", tuple(round(v, 5) for v in rig_min), tuple(round(v, 5) for v in rig_max))
    log("rig size", tuple(round(v, 5) for v in (rig_max - rig_min)))
    log("rig matrix_world", [round(v, 5) for row in rig_mesh.matrix_world for v in row])

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=STATIC_GLB)
    static_meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    static_mesh = max(static_meshes, key=lambda o: len(o.data.vertices))
    static_points = raw_points(static_mesh)
    static_min, static_max = bounds(static_points)
    log("static verts", len(static_points), "uv layers", [l.name for l in static_mesh.data.uv_layers])
    log(
        "static bounds",
        tuple(round(v, 5) for v in static_min),
        tuple(round(v, 5) for v in static_max),
    )
    log("static size", tuple(round(v, 5) for v in (static_max - static_min)))
    log("static matrix_world", [round(v, 5) for row in static_mesh.matrix_world for v in row])

    # Sample for speed.
    rig_sample = rig_points[:: max(1, len(rig_points) // 4000)]
    static_sample = static_points[:: max(1, len(static_points) // 20000)]
    rig_center = (rig_min + rig_max) / 2
    static_center = (static_min + static_max) / 2
    rig_size = rig_max - rig_min
    static_size = static_max - static_min
    log("samples", len(rig_sample), len(static_sample))

    results = []
    for perm, signs, rotation in ROTATIONS:
        rotated = [rotation @ (p - static_center) for p in static_sample]
        rmn, rmx = bounds(rotated)
        rsize = rmx - rmn
        # uniform scale from the largest common extent
        ratios = []
        for axis in range(3):
            if abs(rsize[axis]) > 1e-9:
                ratios.append(rig_size[axis] / rsize[axis])
        if not ratios:
            continue
        scale = sum(ratios) / len(ratios)
        scaled = [p * scale + rig_center for p in rotated]

        tree = kdtree.KDTree(len(scaled))
        for index, point in enumerate(scaled):
            tree.insert(point, index)
        tree.balance()

        total = 0.0
        worst = 0.0
        for point in rig_sample:
            _co, _index, distance = tree.find(point)
            total += distance
            worst = max(worst, distance)
        mean = total / len(rig_sample)
        results.append((mean, perm, signs, scale, worst))

    results.sort()
    span = max(rig_size)
    for mean, perm, signs, scale, worst in results[:4]:
        log(
            "candidate perm",
            perm,
            "signs",
            signs,
            "mean",
            round(mean, 6),
            "worst",
            round(worst, 6),
            f"({mean / span * 100:.2f}% of height)",
            "scale",
            round(scale, 6),
        )


if __name__ == "__main__":
    main()
