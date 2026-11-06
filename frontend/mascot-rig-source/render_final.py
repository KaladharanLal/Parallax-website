import bpy, os, math
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
F=os.path.join(os.path.dirname(HERE),'public','mascot','mascot-rigged.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=F)
mesh=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Mesh_0'))
for o in [o for o in bpy.data.objects if o.type=='MESH' and o is not mesh]:
    o.hide_render=True
# active Idle, frame 10
for arm in [o for o in bpy.data.objects if o.type=='ARMATURE']:
    if arm.animation_data and arm.animation_data.action:
        bpy.context.scene.frame_set(10)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='TEXTURE'
scene.display.shading.background_type='VIEWPORT'
scene.display.shading.background_color=(0.015,0.02,0.03)
scene.render.resolution_x=500
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.render.film_transparent=False
cam_data=bpy.data.cameras.new('Camera')
cam=bpy.data.objects.new('Camera',cam_data)
scene.collection.objects.link(cam)
cam.data.type='ORTHO'
cam.data.ortho_scale=2.2
scene.camera=cam
for label, y, rotz in [('front',-4,0),('back',4,math.pi)]:
    cam.location=(0,y,0.95)
    cam.rotation_euler=(math.pi/2,0,rotz)
    scene.render.filepath=os.path.join(HERE,label+'.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED',scene.render.filepath)
