"""Refresh the catalog thumbnail from a Blender render, without altering source files."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-base-animabile.blend'))
mat=bpy.data.materials['Castell_Skin'];nodes=mat.node_tree.nodes;links=mat.node_tree.links
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(1,.88,.91,1)
if bs.inputs['Base Color'].is_linked:links.new(bs.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
links.new(mix.outputs[0],bs.inputs['Base Color'])
scene=bpy.context.scene;cam=scene.camera;cam.location=(.15,-4,.88);cam.rotation_euler=(Vector((0,0,.86))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.95
scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=450;scene.render.resolution_y=650;scene.render.resolution_percentage=100
scene.render.filepath=os.path.join(ROOT,'public','previews','body-adult-rosy.png');bpy.ops.render.render(write_still=True)
print('ROSY_BODY_PREVIEW_READY',flush=True)
