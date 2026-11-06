import bpy, os
HERE=os.path.dirname(os.path.abspath(__file__)); F=os.path.join(HERE,'Breathing Idle.fbx')
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
bpy.ops.import_scene.fbx(filepath=F, use_anim=True)
print('FPS',bpy.context.scene.render.fps)
for o in bpy.data.objects:
    print('OBJ',o.type,repr(o.name),'parent',repr(o.parent.name if o.parent else None),'scale',tuple(round(v,6) for v in o.scale),'dims',tuple(round(v,4) for v in o.dimensions),'rot',tuple(round(v,4) for v in o.rotation_euler),'loc',tuple(round(v,4) for v in o.location))
    if o.type=='MESH':
        print(' MESH verts',len(o.data.vertices),'poly',len(o.data.polygons),'uv',[u.name for u in o.data.uv_layers],'mats',[m.name if m else None for m in o.data.materials])
for m in bpy.data.materials:
    print('MAT',repr(m.name),'nodes',[(n.type,n.name,repr(getattr(n,'image',None).name) if getattr(n,'image',None) else None) for n in m.node_tree.nodes] if m.use_nodes else None)
for img in bpy.data.images:
    print('IMG',repr(img.name),'size',tuple(img.size),'has_data',img.has_data,'packed',bool(img.packed_file),'path',repr(img.filepath))
for a in bpy.data.actions:
    print('ACTION',repr(a.name),'range',tuple(round(v,2) for v in a.frame_range),'layers',len(a.layers))
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path=='pose.bones["mixamorig:Hips"].location':
                        print(' HIPLOC',fc.array_index,[tuple(round(v,4) for v in k.co) for k in fc.keyframe_points[:3]])
for arm in [o for o in bpy.data.objects if o.type=='ARMATURE']:
    print('ARM',repr(arm.name),'scale',tuple(round(v,6) for v in arm.scale),'dims',tuple(round(v,4) for v in arm.dimensions),'bones',len(arm.data.bones))
    for n in ('mixamorig:Hips','mixamorig:Head','mixamorig:LeftFoot'):
        b=arm.data.bones.get(n)
        if b: print(' BONE',n,tuple(round(v,4) for v in (arm.matrix_world @ b.head_local)))
