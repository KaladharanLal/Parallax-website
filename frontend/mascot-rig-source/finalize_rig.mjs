import { NodeIO } from '@gltf-transform/core';
import { KHRTextureTransform, EXTTextureWebP } from '@gltf-transform/extensions';

const input = process.argv[2] || 'mascot-rig-source/mascot-rigged.raw.glb';
const output = process.argv[3] || 'mascot-rig-source/mascot-rigged.oriented.glb';

const io = new NodeIO().registerExtensions([KHRTextureTransform, EXTTextureWebP]);
const doc = await io.read(input);
const armature = doc
  .getRoot()
  .listNodes()
  .find((node) => node.getName() === 'Armature' && node.listChildren().length > 0);

if (!armature) throw new Error('Armature root not found');

// Blender exported the Mixamo rest data Z-up after clearing the FBX viewport
// rotation, with the character facing the other way. A +90-degree X rotation
// on the root gives glTF an upright Y-up result while keeping the mesh and all
// animation channels untouched.
armature.setRotation([Math.SQRT1_2, 0, 0, Math.SQRT1_2]);

await io.write(output, doc);
console.log(`WROTE ${output} from ${input}`);
