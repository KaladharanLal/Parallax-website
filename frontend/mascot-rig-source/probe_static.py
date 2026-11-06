import bpy
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(ROOT, "public", "mascot", "mascot.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=FILE)
for obj in bpy.data.objects:
    print("OBJECT", obj.type, repr(obj.name), "dims=", tuple(round(v, 3) for v in obj.dimensions))
    if obj.type == "MESH":
        print("  mats", [m.name for m in obj.data.materials], "verts", len(obj.data.vertices), "uv", [u.name for u in obj.data.uv_layers])
for mat in bpy.data.materials:
    print("MATERIAL", repr(mat.name), "nodes", [(n.type, n.name) for n in mat.node_tree.nodes] if mat.use_nodes else None)
for image in bpy.data.images:
    print("IMAGE", repr(image.name), "size=", tuple(image.size), "has_data=", image.has_data, "packed=", bool(image.packed_file), "filepath=", repr(image.filepath), "source=", image.source)
