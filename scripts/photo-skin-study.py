import bpy,os,math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','photoreal-study')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-studio-fotorealismo.blend'))
body=bpy.data.objects['Castell_Body'];mesh=body.data;skin=bpy.data.materials['Castell_Skin'];scene=bpy.context.scene
image=bpy.data.images.load(os.path.join(OUT,'references','asia','a3bd621ec5faddcb19f406bfb5b0faeb.jpg'));image.pack()
rows=[(1.420,478),(1.440,450),(1.459,418),(1.474,387),(1.480,375),(1.506,337),(1.551,246),(1.573,212),(1.600,165),(1.625,125)]
def interp(z):
    for (a,pa),(b,pb) in zip(rows,rows[1:]):
        if a<=z<=b:return pa+(pb-pa)*(z-a)/(b-a)
    return rows[0][1] if z<rows[0][0] else rows[-1][1]
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def g(x,c,w):return math.exp(-.5*((x-c)/w)**2)
uv=mesh.uv_layers.new(name='PortraitStudyUV');mask=mesh.color_attributes.new(name='PortraitSkinBlend',type='FLOAT_COLOR',domain='CORNER')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co;a=abs(x)
    uv.data[loop.index].uv=((245+x*1650)/image.size[0],1-interp(z)/image.size[1])
    amount=.58*smooth(1.430,1.455,z)*(1-smooth(1.600,1.622,z))*(1-smooth(.060,.078,a))*(1-smooth(-.070,-.035,y))
    # Preserve modeled eyes, independent brow fibres and nostril cavities.
    amount*=1-.99*g(a,.035,.021)*g(z,1.551,.009)
    amount*=1-.97*g(a,.037,.025)*g(z,1.575,.004)
    amount*=1-.95*g(a,.011,.009)*g(z,1.508,.006)
    mask.data[loop.index].color=(amount,amount,amount,1)
n=skin.node_tree.nodes;l=skin.node_tree.links;p=next(v for v in n if v.type=='BSDF_PRINCIPLED');base=p.inputs['Base Color'].links[0].from_socket
tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND'
u=n.new('ShaderNodeUVMap');u.uv_map='PortraitStudyUV';l.new(u.outputs[0],tex.inputs['Vector'])
vc=n.new('ShaderNodeVertexColor');vc.layer_name=mask.name
mix=n.new('ShaderNodeMixRGB');l.new(base,mix.inputs[1]);l.new(tex.outputs[0],mix.inputs[2]);l.new(vc.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color'])
mesh.uv_layers.active_index=mesh.uv_layers.find('PhotorealAtlas');mesh.uv_layers['PhotorealAtlas'].active_render=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
atlas=bpy.data.images.new('Photographic skin study albedo',width=4096,height=4096,alpha=False)
for material in mesh.materials:
    t=material.node_tree.nodes.new('ShaderNodeTexImage');t.image=atlas;material.node_tree.nodes.active=t
scene.cycles.samples=1;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
mod=body.modifiers.get('Castell skin weights');mod.show_render=False;bpy.ops.object.bake(type='DIFFUSE');mod.show_render=True
atlas.filepath_raw=os.path.join(OUT,'photo-skin-albedo.png');atlas.file_format='PNG';atlas.save();atlas.pack()
for material in mesh.materials:
    nodes=material.node_tree.nodes;links=material.node_tree.links;b=next(v for v in nodes if v.type=='BSDF_PRINCIPLED')
    t=nodes.new('ShaderNodeTexImage');t.image=atlas;u=nodes.new('ShaderNodeUVMap');u.uv_map='PhotorealAtlas';links.new(u.outputs[0],t.inputs['Vector']);links.new(t.outputs[0],b.inputs['Base Color'])
body['surface_detail']='Photographic skin study blended with procedural microdetail; separate experimental version.'
scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=950;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=.37;cam.location=(.30,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-studio-pelle-fotografica.blend'))
scene.render.filepath=os.path.join(OUT,'viso-pelle-fotografica.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-photo-skin-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('PHOTO_SKIN_READY',flush=True)
