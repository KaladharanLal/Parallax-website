import bpy
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "Sad Idle.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
print("EXPORT_OP", hasattr(bpy.ops.export_scene, "gltf"))
print("IMPORTING", FILE)
bpy.ops.import_scene.fbx(filepath=FILE, use_anim=True)

print("FPS", bpy.context.scene.render.fps)
for obj in bpy.data.objects:
    print(
        "OBJECT",
        obj.type,
        repr(obj.name),
        "parent=", repr(obj.parent.name if obj.parent else None),
        "dims=", tuple(round(v, 4) for v in obj.dimensions),
        "scale=", tuple(round(v, 4) for v in obj.scale),
        "mods=", [(m.type, getattr(m, "object", None).name if getattr(m, "object", None) else None) for m in obj.modifiers],
    )
    if obj.type == "MESH":
        print("  verts", len(obj.data.vertices), "polys", len(obj.data.polygons))
        print("  materials", [m.name if m else None for m in obj.data.materials])
        print("  uv_layers", [uv.name for uv in obj.data.uv_layers])
        print("  vertex_groups", len(obj.vertex_groups))
    if obj.type == "ARMATURE":
        print("  bones", len(obj.data.bones))
        print("  bone_names", [b.name for b in obj.data.bones][:12], "...")
        print("  anim_data", bool(obj.animation_data), "action", repr(obj.animation_data.action.name) if obj.animation_data and obj.animation_data.action else None)

print("ACTIONS")
for action in bpy.data.actions:
    print(
        "ACTION",
        repr(action.name),
        "range=", tuple(round(v, 2) for v in action.frame_range),
        "id_root=", getattr(action, "id_root", None),
        "users=", action.users,
        "fake=", action.use_fake_user,
        "layers=", len(action.layers),
        "slots=", len(action.slots),
    )
    for layer in action.layers:
        print("  LAYER", repr(layer.name), "strips=", len(layer.strips))
        for strip in layer.strips:
            print("    STRIP", strip.type, "attrs=", [a for a in dir(strip) if not a.startswith('_')])
            for attr in ("channelbags", "channelbag", "fcurves"):
                if hasattr(strip, attr):
                    value = getattr(strip, attr)
                    print("      ", attr, "=", value)
                    if attr == "channelbags":
                        for bag in value:
                            slot = bag.slot
                            print("        BAG slot=", getattr(slot, 'identifier', None), "target=", getattr(slot, 'target_id_type', None), "fcurves=", len(bag.fcurves))
                            print("        PATHS", sorted({fc.data_path for fc in bag.fcurves})[:8])

print("MATERIALS")
for mat in bpy.data.materials:
    print("MATERIAL", repr(mat.name), "use_nodes=", mat.use_nodes, "diffuse=", tuple(round(v, 3) for v in mat.diffuse_color))
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            print("  NODE", node.type, repr(node.name), "image=", repr(getattr(node, 'image', None).name) if getattr(node, 'image', None) else None)
            if node.type == 'BSDF_PRINCIPLED':
                for name in ('Base Color', 'Metallic', 'Roughness'):
                    socket = node.inputs.get(name)
                    if socket:
                        print("    INPUT", name, "default=", tuple(round(v, 3) for v in socket.default_value) if hasattr(socket.default_value, '__len__') else socket.default_value, "linked=", socket.is_linked)
        for link in mat.node_tree.links:
            print("  LINK", link.from_node.type, link.from_socket.name, '->', link.to_node.type, link.to_socket.name)

print("IMAGES")
for image in bpy.data.images:
    print("IMAGE", repr(image.name), "size=", tuple(image.size), "has_data=", image.has_data, "packed=", bool(image.packed_file), "source=", image.source, "filepath=", repr(image.filepath))
