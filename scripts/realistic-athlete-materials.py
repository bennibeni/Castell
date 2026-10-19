"""Detailed Blender shading and baked PBR maps for the Castell browser model."""
import bpy,os,math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','realistic-athlete');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-half-bun.blend'))
body=bpy.data.objects['Castell_Body'];mesh=body.data
skin=bpy.data.materials['Castell_Skin'];eyes=bpy.data.materials['Castell_Eyes']
def gaussian(x,c,w):return math.exp(-.5*((x-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def node(mat,kind):return mat.node_tree.nodes.new(kind)
def link(mat,a,b):mat.node_tree.links.new(a,b)
def bsdf(mat):return next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
attr=mesh.color_attributes.new(name='SkinVariation',type='FLOAT_COLOR',domain='CORNER')
rough=mesh.color_attributes.new(name='SkinRoughness',type='FLOAT_COLOR',domain='CORNER')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co;a=abs(x);front=1-smooth(-.06,-.025,y)
    cheek=gaussian(a,.052,.022)*gaussian(z,1.512,.016)*front
    nose=gaussian(x,0,.017)*gaussian(z,1.518,.025)*front
    ear=gaussian(a,.084,.012)*gaussian(z,1.535,.030)
    color=Vector((1,1,1)).lerp(Vector((1.06,.86,.83)),min(.6,.30*cheek+.18*nose+.32*ear))
    attr.data[loop.index].color=(*color,1)
    zone=front*gaussian(x,0,.024)*(gaussian(z,1.595,.023)+gaussian(z,1.531,.024))
    r=.53-.14*min(1,zone)
    rough.data[loop.index].color=(r,r,r,1)
p=bsdf(skin);base=p.inputs['Base Color'].links[0].from_socket
variation=node(skin,'ShaderNodeVertexColor');variation.layer_name=attr.name
mix=node(skin,'ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
link(skin,base,mix.inputs[1]);link(skin,variation.outputs['Color'],mix.inputs[2])
coords=node(skin,'ShaderNodeTexCoord')
noise=node(skin,'ShaderNodeTexNoise');noise.inputs['Scale'].default_value=65;noise.inputs['Detail'].default_value=3
link(skin,coords.outputs['Object'],noise.inputs['Vector'])
ramp=node(skin,'ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.88,.85,.82,1);ramp.color_ramp.elements[1].color=(1.03,1.01,.99,1)
link(skin,noise.outputs['Fac'],ramp.inputs[0])
mottle=node(skin,'ShaderNodeMixRGB');mottle.blend_type='MULTIPLY';mottle.inputs[0].default_value=.32
link(skin,mix.outputs[0],mottle.inputs[1]);link(skin,ramp.outputs[0],mottle.inputs[2]);link(skin,mottle.outputs[0],p.inputs['Base Color'])
pores=node(skin,'ShaderNodeTexNoise');pores.inputs['Scale'].default_value=1900;pores.inputs['Detail'].default_value=2;pores.inputs['Roughness'].default_value=.7
link(skin,coords.outputs['Object'],pores.inputs['Vector'])
bump=node(skin,'ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.00009
link(skin,pores.outputs['Fac'],bump.inputs['Height']);link(skin,bump.outputs['Normal'],p.inputs['Normal'])
ra=node(skin,'ShaderNodeVertexColor');ra.layer_name=rough.name
link(skin,ra.outputs[0],p.inputs['Roughness'])
p.inputs['Subsurface Weight'].default_value=.075;p.inputs['Subsurface Radius'].default_value=(1,.32,.18);p.inputs['Subsurface Scale'].default_value=.0012
p.inputs['IOR'].default_value=1.4
# Iris fibres from radial procedural coordinates, with a separate black pupil and limbal ring.
eyeuv=mesh.uv_layers.new(name='EyeRadialUV')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co
    eyeuv.data[loop.index].uv=((abs(x)-.036)/.016+.5,(z-1.550)/.016+.5)
ep=bsdf(eyes);eu=node(eyes,'ShaderNodeUVMap');eu.uv_map='EyeRadialUV'
sep=node(eyes,'ShaderNodeSeparateXYZ');link(eyes,eu.outputs[0],sep.inputs[0])
def mathnode(op,a=None,b=None):
    n=node(eyes,'ShaderNodeMath');n.operation=op
    for i,v in enumerate([a,b]):
        if v is not None:
            if isinstance(v,(float,int)):n.inputs[i].default_value=v
            else:link(eyes,v,n.inputs[i])
    return n.outputs[0]
x=mathnode('SUBTRACT',sep.outputs['X'],.5);z=mathnode('SUBTRACT',sep.outputs['Y'],.5)
radius=mathnode('SQRT',mathnode('ADD',mathnode('MULTIPLY',x,x),mathnode('MULTIPLY',z,z)))
angle=mathnode('ARCTAN2',z,x)
comb=node(eyes,'ShaderNodeCombineXYZ');link(eyes,mathnode('MULTIPLY',angle,18),comb.inputs[0]);link(eyes,mathnode('MULTIPLY',radius,4),comb.inputs[1])
fibres=node(eyes,'ShaderNodeTexNoise');fibres.inputs['Scale'].default_value=4;fibres.inputs['Detail'].default_value=3;link(eyes,comb.outputs[0],fibres.inputs['Vector'])
iris=node(eyes,'ShaderNodeValToRGB');iris.color_ramp.elements[0].color=(.018,.008,.004,1);iris.color_ramp.elements[1].color=(.19,.09,.032,1);link(eyes,fibres.outputs['Fac'],iris.inputs[0])
ring=node(eyes,'ShaderNodeMixRGB');ring.inputs[2].default_value=(.012,.007,.004,1);link(eyes,iris.outputs[0],ring.inputs[1]);link(eyes,mathnode('GREATER_THAN',radius,.40),ring.inputs[0])
white=node(eyes,'ShaderNodeMixRGB');white.inputs[2].default_value=(.76,.75,.71,1);link(eyes,ring.outputs[0],white.inputs[1]);link(eyes,mathnode('GREATER_THAN',radius,.46),white.inputs[0])
pupil=node(eyes,'ShaderNodeMixRGB');pupil.inputs[2].default_value=(.002,.0015,.001,1);link(eyes,white.outputs[0],pupil.inputs[1]);link(eyes,mathnode('LESS_THAN',radius,.17),pupil.inputs[0]);link(eyes,pupil.outputs[0],ep.inputs['Base Color'])
ep.inputs['Roughness'].default_value=.24;ep.inputs['Coat Weight'].default_value=.8;ep.inputs['Coat Roughness'].default_value=.04;ep.inputs['IOR'].default_value=1.376
# Bake only the body/eyes; preserve existing hair textures and rig untouched.
mesh.uv_layers.active_index=mesh.uv_layers.find('CastellFaceAtlas');mesh.uv_layers['CastellFaceAtlas'].active_render=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=12
mod=body.modifiers.get('Castell skin weights');mod.show_render=False
maps={}
for name,kind in [('albedo','DIFFUSE'),('roughness','ROUGHNESS'),('normal','NORMAL')]:
    image=bpy.data.images.new('Castell realistic '+name,width=4096,height=4096,alpha=False)
    if name!='albedo':image.colorspace_settings.name='Non-Color'
    for mat in mesh.materials:
        n=node(mat,'ShaderNodeTexImage');n.image=image;mat.node_tree.nodes.active=n
    bpy.ops.object.bake(type=kind)
    image.filepath_raw=os.path.join(OUT,name+'.png');image.file_format='PNG';image.save();image.pack();maps[name]=image
    print('BAKED',name,flush=True)
mod.show_render=True
for mat in mesh.materials:
    p=bsdf(mat);uv=node(mat,'ShaderNodeUVMap');uv.uv_map='CastellFaceAtlas'
    for name,socket in [('albedo','Base Color'),('roughness','Roughness'),('normal','Normal')]:
        n=node(mat,'ShaderNodeTexImage');n.image=maps[name];link(mat,uv.outputs[0],n.inputs['Vector'])
        if name=='normal':
            nm=node(mat,'ShaderNodeNormalMap');nm.uv_map='CastellFaceAtlas';link(mat,n.outputs['Color'],nm.inputs['Color']);link(mat,nm.outputs[0],p.inputs[socket])
        else:link(mat,n.outputs['Color'],p.inputs[socket])
# Genuine transmissive eye shell for Blender close-ups; browser uses coat on the eye material.
eyeindex=list(mesh.materials).index(eyes)
indices=sorted({i for face in mesh.polygons if face.material_index==eyeindex for i in face.vertices});lookup={vi:i for i,vi in enumerate(indices)}
vertices=[mesh.vertices[i].co+mesh.vertices[i].normal*.00015 for i in indices]
faces=[[lookup[i] for i in face.vertices] for face in mesh.polygons if face.material_index==eyeindex]
data=bpy.data.meshes.new('Corneal wet shell');data.from_pydata(vertices,[],faces);data.update()
cornea=bpy.data.objects.new('Castell_Cornea_RenderOnly',data);scene.collection.objects.link(cornea)
mat=bpy.data.materials.new('Castell_Cornea_Glass');mat.use_nodes=True;cb=bsdf(mat)
cb.inputs['Base Color'].default_value=(1,1,1,1);cb.inputs['Transmission Weight'].default_value=1;cb.inputs['IOR'].default_value=1.376;cb.inputs['Roughness'].default_value=.025
data.materials.append(mat)
for f in data.polygons:f.use_smooth=True
bpy.context.view_layer.update();world=cornea.matrix_world.copy();cornea.parent=bpy.data.objects['Castell_Torso'];cornea.matrix_world=world
cornea['renderOnly']=True
# Studio key/fill/rim setup, moderate world illumination for readable highlights.
bsdf(bpy.data.materials['Castell_Hair_HalfBun']).inputs['Roughness'].default_value=.62
for o in list(scene.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.18
for name,position,power,size,color in [('Studio Key',(-1.3,-2.2,2.8),95,1.5,(1,.91,.83)),('Studio Fill',(1.5,-1.2,1.9),32,1.7,(.82,.9,1)),('Studio Rim',(.5,1.2,2.4),35,1.6,(1,.94,.88))]:
    o=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(o);o.location=position;o.rotation_euler=(Vector((0,0,1.45))-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size;o.data.color=color
scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=.40;cam.location=(.45,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=1.94;cam.location=(.2,-4,.96);cam.rotation_euler=(Vector((0,0,.84))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-realistic-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('REALISTIC_MATERIALS_READY',flush=True)
