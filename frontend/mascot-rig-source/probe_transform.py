import bpy
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "Sad Idle.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.fbx(filepath=FILE, use_anim=True)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = next(
    o
    for o in bpy.data.objects
    if o.type == "MESH"
    and any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers)
)


def report(label):
    bpy.context.view_layer.update()
    print(label)
    print("  arm scale", tuple(round(v, 6) for v in arm.scale), "loc", tuple(round(v, 4) for v in arm.location))
    print("  mesh scale", tuple(round(v, 6) for v in mesh.scale), "dims", tuple(round(v, 4) for v in mesh.dimensions))
    print("  mesh world translation", tuple(round(v, 4) for v in mesh.matrix_world.translation))
    for name in ("mixamorig:Hips", "mixamorig:Head"):
        bone = arm.data.bones.get(name)
        if bone:
            p = arm.matrix_world @ bone.head_local
            print("  bone", name, tuple(round(v, 4) for v in p))


report("BEFORE")

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
report("AFTER ARMATURE SCALE APPLY")

bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
report("AFTER MESH SCALE APPLY")

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active = arm
out = os.path.join(HERE, "probe-transform.glb")
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    use_selection=True,
    export_apply=False,
    export_animations=False,
    export_rest_position_armature=True,
    export_skins=True,
    export_materials="NONE",
)
print("EXPORTED", out)
