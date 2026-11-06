import bpy, os
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
F=os.path.join(os.path.dirname(HERE),'public','mascot','mascot-rigged.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=F)
print('OBJECTS', [(o.name,o.type,tuple(round(v,3) for v in o.scale)) for o in bpy.data.objects])
for arm in [o for o in bpy.data.objects if o.type=='ARMATURE']:
    print('ACTIONS', [a.name for a in bpy.data.actions], 'active', arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None)
    for n in ('mixamorig:Hips','mixamorig:Head','mixamorig:LeftFoot','mixamorig:RightFoot'):
        b=arm.data.bones.get(n)
        if b:
            p=arm.matrix_world @ b.head_local
            print('BONE', n, 'worldZ', round(p.z,3), 'world', tuple(round(v,3) for v in p))
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    dg=bpy.context.evaluated_depsgraph_get(); e=o.evaluated_get(dg); m=e.to_mesh()
    pts=[o.matrix_world @ v.co for v in m.vertices]
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    print('MESH_BOUNDS', tuple(round(v,3) for v in mn), tuple(round(v,3) for v in mx))
