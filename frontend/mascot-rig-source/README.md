# Mixamo handoff

Drop the five downloaded FBX files here, keeping these exact names:

| File | Mixamo animation | Skin | Notes |
| --- | --- | --- | --- |
| `Idle.fbx` | Idle | **With Skin** | The only skinned file; it supplies the skeleton and mesh |
| `Walk.fbx` | Walking | Without Skin | Enable **In Place** |
| `Wave.fbx` | Waving | Without Skin | Used when the mascot is clicked |
| `Point.fbx` | Pointing | Without Skin | Used while guiding to a target |
| `Jump.fbx` | Jumping | Without Skin | Reserved for a future reaction beat |

Export settings for every file: **FBX Binary**, **30 fps**, **Keyframe Reduction: none**.

Once the files are here, they get merged into
`frontend/public/mascot/mascot-rigged.glb`; the loader prefers that file over
the unrigged fallback.

The Mixamo skin ships without a UV layer and a different mesh than the
sculpture, so textures cannot be moved onto it. `skin_sculpture.py` does the
reverse and the correct thing: it keeps the textured sculpture and transfers the
skin weights onto it by closest surface, then parents it to the armature and
exports the sculpture plus all five clips. `finalize_rig.mjs` adds the Y-up root
rotation and `gltf-transform optimize` compresses the result. See
`../src/components/mascot/README.md` for the exact commands, and keep
`--flatten`/`--join` off for the skinned mesh.

Raw FBX files are ignored by git (see `.gitignore`); only the optimized GLB ships.
