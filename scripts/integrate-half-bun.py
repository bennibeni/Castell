import bpy,os
from mathutils import Vector,Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE=r'C:/Users/torre/Downloads/assets/models/assets/models/female-half-bun-_57ff81a2-2dd9-4c32-bd18-bb97e7100590/female-half-bun-haircut_2K_11b2f44d-5f7d-49e2-ad7d-1d4699a2d85e.blend'
OUT=os.path.join(ROOT,'artifacts','hair-integration');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend'))
with bpy.data.libraries.load(SOURCE,link=False) as (src,dst):
    dst.objects=['Female_Half_Bun_Haircut']
hair=bpy.data.objects['Female_Half_Bun_Haircut'];bpy.context.collection.objects.link(hair)
bpy.context.view_layer.update()
world=hair.matrix_world.copy();hair.parent=None
hair.data.transform(world);hair.matrix_world=Matrix.Identity(4)
for v in hair.data.vertices:
    v.co.x=v.co.x*1.08-.025
    v.co.y=v.co.y*.90-.015
    v.co.z=v.co.z+1.405
hair.name='Castell_Hair_HalfBun'
bpy.context.view_layer.update();world=hair.matrix_world.copy();hair.parent=bpy.data.objects['Castell_Torso'];hair.matrix_world=world
hair['source']='Female Half Bun Haircut, Ddr Rcs, BlenderKit'
hair['assetBaseId']='ffe910e5-54c6-44fc-af04-466a1e0e0139'
hair['license']='royalty_free'
# Convert the Hair Tool node group to a portable glTF PBR material.
original=hair.data.materials[0]
for group in bpy.data.node_groups:
    if group.name.startswith('HTool_UV'):
        print('UVGROUP',[(n.name,n.type,getattr(n,'attribute_name','')) for n in group.nodes],[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in group.links])
mat=bpy.data.materials.new('Castell_Hair_HalfBun');mat.use_nodes=True
n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.036,.021,.014,1);bs.inputs['Roughness'].default_value=.48
bs.inputs['Metallic'].default_value=0
uv=n.new('ShaderNodeUVMap');uv.uv_map='HairTool_UV'
for key,socket in [('hair_bake_opacity.png','Alpha'),('hair_bake_normal.png','Normal')]:
    image=bpy.data.images.get(key)
    if not image:raise RuntimeError('Missing packed hair texture '+key)
    image.colorspace_settings.name='Non-Color'
    t=n.new('ShaderNodeTexImage');t.image=image;l.new(uv.outputs['UV'],t.inputs['Vector'])
    if socket=='Normal':
        normal=n.new('ShaderNodeNormalMap');normal.uv_map='HairTool_UV';normal.inputs['Strength'].default_value=.55;l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs[0],bs.inputs['Normal'])
    else:l.new(t.outputs['Color'],bs.inputs['Alpha'])
mat.surface_render_method='DITHERED'
mat.use_backface_culling=False
hair.data.materials.clear();hair.data.materials.append(mat)
hair.data.uv_layers.active_index=hair.data.uv_layers.find('HairTool_UV');hair.data.uv_layers['HairTool_UV'].active_render=True
for p in hair.data.polygons:p.material_index=0;p.use_smooth=True
bpy.ops.file.pack_all()
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=700;scene.render.resolution_y=850;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.43
def render(name,pos,look):
    cam.location=pos;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)
cam.location=(.45,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-half-bun.blend'))
render('viso',(0,-3,1.54),(0,0,1.54))
render('tre-quarti',(.9,-3,1.54),(0,0,1.54))
cam.data.ortho_scale=1.94
render('figura-intera',(.15,-4,.94),(0,0,.84))
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-half-bun-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('HALF_BUN_READY')
