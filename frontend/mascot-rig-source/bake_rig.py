"""Bake the sculpture's texture onto the rig with the rig's own UV unwrap.

The rigged mesh is a different mesh from the sculpture, so reusing the
sculpture's UV layout (add_uvs.py) samples the wrong atlas islands and the
model looks random. Here the rig gets a fresh unwrap of its own and the
sculpture's surface colour is baked into it with a selected-to-active Cycles
bake, which keeps the original art and its detail.

Run:
  blender --background --factory-startup --python-exit-code 1 \
    --python frontend/mascot-rig-source/bake_rig.py

Writes mascot-rigged.baked.raw.glb and mascot-bake.png.
"""

import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import add_uvs as A  # noqa: E402  (reuses the alignment + export pipeline)

RIG_GLB = os.path.join(HERE, "mascot-rigged.raw.glb")
STATIC_GLB = os.path.join(A.FRONTEND, "public", "mascot", "mascot.glb")
BAKE_PNG = os.path.join(HERE, "mascot-bake.png")
OUTPUT = os.path.join(HERE, "mascot-rigged.baked.raw.glb")
SIZE = 2048

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
    log("rig mesh verts", len(rig_mesh.data.vertices), "bones", len(armature.data.bones))
    return rig_mesh, armature


def import_sculpture():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=STATIC_GLB)
    meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not meshes:
        raise RuntimeError("The static mascot mesh did not import")
    sculpture = max(meshes, key=lambda o: len(o.data.vertices))
    for extra in meshes:
        if extra is not sculpture:
            bpy.data.objects.remove(extra, do_unlink=True)
    if not sculpture.data.uv_layers:
        raise RuntimeError("The static mascot mesh has no UV map")
    log("sculpture verts", len(sculpture.data.vertices))
    return sculpture


def unwrap(rig_mesh):
    for layer in list(rig_mesh.data.uv_layers):
        rig_mesh.data.uv_layers.remove(layer)
    rig_mesh.data.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    rig_mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig_mesh
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = rig_mesh.data.uv_layers.active.data
    us = [d.uv[0] for d in uv]
    vs = [d.uv[1] for d in uv]
    log("unwrap range", round(min(us), 4), round(max(us), 4), round(min(vs), 4), round(max(vs), 4))


def bake_material(rig_mesh):
    """Replace the rig material with a bake target that writes to a new image."""
    image = bpy.data.images.new("MascotBake", SIZE, SIZE, alpha=False)
    material = bpy.data.materials.new("MascotBaked")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.select = True
    nodes.active = tex

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Metallic"].default_value = 0.08
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    rig_mesh.data.materials.clear()
    rig_mesh.data.materials.append(material)
    return image, tex


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
    log("sculpture placed on the rig")

    unwrap(rig_mesh)
    image, _tex = bake_material(rig_mesh)

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    bake = scene.render.bake
    bake.use_pass_direct = False
    bake.use_pass_indirect = False
    bake.use_pass_color = True
    bake.margin = 24
    bake.use_clear = True

    bpy.ops.object.select_all(action="DESELECT")
    sculpture.select_set(True)
    rig_mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig_mesh

    log("baking", SIZE, "px")
    bpy.ops.object.bake(
        type="DIFFUSE",
        pass_filter={"COLOR"},
        use_selected_to_active=True,
        cage_extrusion=0.012,
        max_ray_distance=0.06,
        margin=24,
        use_clear=True,
    )
    log("bake finished")

    image.filepath_raw = BAKE_PNG
    image.file_format = "PNG"
    image.save()
    log("wrote", BAKE_PNG, round(os.path.getsize(BAKE_PNG) / 1024), "KB")

    # Make the baked colour the visible base colour of the shipped material.
    material = rig_mesh.data.materials[0]
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    tex = next(n for n in nodes if n.type == "TEX_IMAGE")
    material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    bpy.data.objects.remove(sculpture, do_unlink=True)
    A.stage_actions(armature)

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
