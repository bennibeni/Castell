"""Add the original hair to the prepared head; body assets remain untouched."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','hinako')
SOURCE=r'C:\Users\torre\Downloads\realistic+girl\hinako'
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'hinako blender 4.5 .blend'))
original=bpy.data.objects['hair'];deps=bpy.context.evaluated_depsgraph_get()
data=bpy.data.meshes.new_from_object(original.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps);data.transform(original.matrix_world)
hair=bpy.data.objects.new('Castell_Hinako_Hair',data)
for obj in list(bpy.data.objects):
    if obj!=hair:bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.scene.collection.objects.link(hair)
for v in data.vertices:v.co=Vector((v.co.x*.64,v.co.y*.64+.018,(v.co.z-2.817)*.64+1.553))
for p in data.polygons:p.use_smooth=True
image=bpy.data.images.load(os.path.join(SOURCE,'textures','HAIR_NODE.png'),check_existing=False);image.colorspace_settings.name='Non-Color';image.pack()
mat=bpy.data.materials.new('Castell_Hinako_Hair');mat.use_nodes=True
n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
output=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');l.new(p.outputs['BSDF'],output.inputs['Surface'])
tex=n.new('ShaderNodeTexImage');tex.image=image
sep=n.new('ShaderNodeSeparateColor');l.new(tex.outputs['Color'],sep.inputs[0])
mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.009,.007,.006,1);mix.inputs[2].default_value=(.058,.041,.030,1);l.new(sep.outputs['Blue'],mix.inputs[0])
emission=n.new('ShaderNodeEmission');l.new(mix.outputs[0],emission.inputs['Color']);l.new(emission.outputs[0],output.inputs['Surface'])
data.materials.clear();data.materials.append(mat)
atlas=bpy.data.images.new('Hinako hair natural color',width=1024,height=1024,alpha=False)
target=n.new('ShaderNodeTexImage');target.image=atlas;n.active=target
bpy.ops.object.select_all(action='DESELECT');hair.select_set(True);bpy.context.view_layer.objects.active=hair
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=8
scene.world=bpy.data.worlds.new('Hair bake neutral')
bpy.ops.object.bake(type='EMIT')
atlas.filepath_raw=os.path.join(OUT,'hinako-hair-color.png');atlas.file_format='PNG';atlas.save();atlas.pack()
l.new(target.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Alpha'],p.inputs['Alpha']);l.new(p.outputs['BSDF'],output.inputs['Surface'])
p.inputs['Roughness'].default_value=.46;p.inputs['Metallic'].default_value=0
mat.surface_render_method='DITHERED';mat.use_backface_culling=False
bpy.data.libraries.write(os.path.join(OUT,'hair-component.blend'),{hair},fake_user=True)
# Append the prepared hair to the head-only file, preserving its studio setup.
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-testa-Hinako.blend'))
with bpy.data.libraries.load(os.path.join(OUT,'hair-component.blend'),link=False) as (src,dst):dst.objects=['Castell_Hinako_Hair']
hair=bpy.data.objects['Castell_Hinako_Hair'];bpy.context.scene.collection.objects.link(hair);hair.parent=bpy.data.objects['Castell_Head_Assembly']
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.ortho_scale=.49
center=Vector((0,.025,1.525));camera.location=(.45,-3,1.55);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');hair.select_set(True);bpy.context.view_layer.objects.active=hair
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-testa-Hinako-capelli.blend'))
scene.render.filepath=os.path.join(OUT,'testa-capelli.png');bpy.ops.render.render(write_still=True)
camera.location=(1.6,-3,1.55);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'testa-capelli-tre-quarti.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','Castell-testa-Hinako-capelli.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('HINAKO_HEAD_HAIR_READY',flush=True)
