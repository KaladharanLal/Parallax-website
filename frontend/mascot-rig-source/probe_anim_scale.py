import bpy
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "Sad Idle.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.fbx(filepath=FILE, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = next(
    o
    for o in bpy.data.objects
    if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers)
)
action = arm.animation_data.action


def curves():
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def report(label):
    bpy.context.scene.frame_set(42)
    bpy.context.view_layer.update()
    print(label)
    for name in ("mixamorig:Hips", "mixamorig:Head", "mixamorig:LeftHand"):
        pb = arm.pose.bones.get(name)
        if pb:
            p = arm.matrix_world @ pb.head
            print("  pose", name, tuple(round(v, 5) for v in p))
    for fc in curves():
        if fc.data_path == 'pose.bones["mixamorig:Hips"].location':
            vals = [tuple(round(v, 5) for v in kp.co) for kp in fc.keyframe_points[:3]]
            print("  hips_loc", fc.array_index, vals)


report("BEFORE")
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for fc in curves():
    if fc.data_path.endswith(".location"):
        for kp in fc.keyframe_points:
            kp.co[1] *= 0.01
            kp.handle_left[1] *= 0.01
            kp.handle_right[1] *= 0.01
        fc.update()
report("AFTER ARMATURE + LOCATION SCALE")
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
report("AFTER MESH")
