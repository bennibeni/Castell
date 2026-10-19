"""Use the exact selected portrait; retain integrated body and restore gathered hair."""
import bpy,os,json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(ROOT,'artifacts','atleta-scelta');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
body=bpy.data.objects['Castell_Body'];torso=bpy.data.objects['Castell_Torso']
for obj in list(bpy.data.objects):
    if obj.name.startswith('Castell_Hair'):bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(os.path.join(ROOT,'blender','Castell-atleta-originale.blend'),link=False) as (src,dst):
    dst.meshes=['Castell_Hair_CombedLocks']
hair=bpy.data.objects.new('Castell_Hair_Gathered',dst.meshes[0]);bpy.context.scene.collection.objects.link(hair)
bpy.context.view_layer.update();m=hair.matrix_world.copy();hair.parent=torso;hair.matrix_world=m
image=bpy.data.images.load(os.path.join(ROOT,'blender','volto-scelto.png'));image.pack()
with open(os.path.join(ROOT,'blender','asia-face-settings.json')) as f:old=json.load(f)
rows=[[1.42,1190],[1.459,1065],[1.493,874],[1.52034,755],[1.55856,565],[1.57949,485],[1.62135,275],[1.65,160]]
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def interpolate(value,pairs):
    ordered=sorted(pairs)
    for (a,va),(b,vb) in zip(ordered,ordered[1:]):
        if a<=value<=b:return va+(vb-va)*(value-a)/(b-a)
    return ordered[0][1] if value<ordered[0][0] else ordered[-1][1]
# Rebind using the original projection coordinates, preserving sculpted landmarks.
source_uv=body.data.uv_layers['FaceReferenceUV']
uv=body.data.uv_layers.new(name='SelectedFaceUV')
for li,item in enumerate(source_uv.data):
    x=(item.uv.x*1254-old['center_x'])/old['pixels_per_meter']
    z=interpolate((1-item.uv.y)*1254,[(py,sz) for sz,py in old['rows']])
    uv.data[li].uv=((635+x*3750)/image.size[0],1-interpolate(z,rows)/image.size[1])
head_mask=body.data.color_attributes.new(name='SelectedHeadClear',type='FLOAT_COLOR',domain='CORNER')
for loop in body.data.loops:
    z=body.data.vertices[loop.vertex_index].co.z
    value=smooth(1.40,1.445,z)
    head_mask.data[loop.index].color=(value,value,value,1)
skin=body.data.materials[0];nodes=skin.node_tree.nodes;links=skin.node_tree.links;p=nodes.get('Principled BSDF')
source=p.inputs['Base Color'].links[0].from_socket
warm=nodes.new('ShaderNodeMixRGB');warm.blend_type='MULTIPLY';warm.inputs[0].default_value=1;warm.inputs[2].default_value=(.9722,.9038,.8,1);links.new(source,warm.inputs[1])
clear=nodes.new('ShaderNodeMixRGB');clear.inputs[2].default_value=(.70,.47,.32,1);links.new(warm.outputs[0],clear.inputs[1])
mask=nodes.new('ShaderNodeVertexColor');mask.layer_name=head_mask.name;links.new(mask.outputs['Color'],clear.inputs[0])
photo=nodes.new('ShaderNodeTexImage');photo.image=image;photo.extension='EXTEND'
uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='SelectedFaceUV';links.new(uvnode.outputs['UV'],photo.inputs['Vector'])
face_mask=nodes.new('ShaderNodeVertexColor');face_mask.layer_name='FaceReferenceBlend'
mix=nodes.new('ShaderNodeMixRGB');links.new(face_mask.outputs['Color'],mix.inputs[0]);links.new(clear.outputs[0],mix.inputs[1]);links.new(photo.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
atlas=bpy.data.images.new('Selected portrait skin atlas',width=2048,height=2048,alpha=False)
target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
body.data.uv_layers.active_index=body.data.uv_layers.find('CastellAtlas');body.data.uv_layers['CastellAtlas'].active_render=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=8
modifier=body.modifiers.get('Castell skin weights');modifier.show_render=False
bpy.ops.object.bake(type='DIFFUSE');modifier.show_render=True
atlas.filepath_raw=os.path.join(ROOT,'public','models','atleta-scelta-color.png');atlas.file_format='PNG';atlas.save();atlas.pack()
atlas_uv=nodes.new('ShaderNodeUVMap');atlas_uv.uv_map='CastellAtlas';links.new(atlas_uv.outputs['UV'],target.inputs['Vector']);links.new(target.outputs['Color'],p.inputs['Base Color'])
body['identity']='Fictional adult athlete using the exact previously generated portrait selected by the user.'
body['face_revision']='Selected portrait volto-scelto.png, not regenerated or retouched; gathered hair restored.'
scene.cycles.samples=20;scene.cycles.use_denoising=True
scene.render.resolution_x=750;scene.render.resolution_y=900;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.ortho_scale=.40;camera.location=(.6,-3,1.56);camera.rotation_euler=(Vector((0,0,1.56))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-scelta.blend'))
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=1.94;camera.location=(1.1,-3.8,1.15);camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=850;scene.render.resolution_y=1250;scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','atleta-scelta-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
