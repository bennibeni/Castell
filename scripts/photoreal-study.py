"""Reference-led facial surface/detail pass, preserving the Castell body rig."""
import bpy,os,math,random,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','photoreal-study');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
body=bpy.data.objects['Castell_Body'];mesh=body.data;scene=bpy.context.scene
random.seed(81)
def g(v,c,w):return math.exp(-.5*((v-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def nd(mat,t):return mat.node_tree.nodes.new(t)
def lk(mat,a,b):mat.node_tree.links.new(a,b)
def bsdf(mat):return next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def parent(obj):
    bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=bpy.data.objects['Castell_Torso'];obj.matrix_world=world
skin=bpy.data.materials['Castell_Skin'];eyes=bpy.data.materials['Castell_Eyes'];p=bsdf(skin)
eyeidx=list(mesh.materials).index(eyes)
# Tiny changes that respect the base anatomy, rather than a radical synthetic face warp.
for v in mesh.vertices:
    x,y,z=v.co
    if not 1.425<z<1.61 or y>-.065:continue
    a=abs(x)
    v.co.y-=.0011*g(a,.049,.017)*g(z,1.515,.017)
    v.co.z+=.00065*g(a,.008,.005)*g(z,1.481,.004)
mesh.update()
# Anatomical corner points directly from the open eyelid boundary.
edges={}
for poly in mesh.polygons:
    if poly.material_index==eyeidx:continue
    for edge in poly.edge_keys:edges[edge]=edges.get(edge,0)+1
boundary={i for edge,count in edges.items() if count==1 for i in edge}
socket=[mesh.vertices[i].co.copy() for i in boundary if 1.53<mesh.vertices[i].co.z<1.57 and mesh.vertices[i].co.y<-.06]
if len(socket)<40:raise RuntimeError('Eye socket boundary not found')
# Give the face more than half of the atlas pixels; retain the original UV layer for source maps.
old=mesh.uv_layers['CastellFaceAtlas'];uv=mesh.uv_layers.new(name='PhotorealAtlas')
for poly in mesh.polygons:
    c=poly.center
    facial=poly.material_index!=eyeidx and 1.420<c.z<1.635 and c.y<-.052 and abs(c.x)<.079
    for li in poly.loop_indices:
        v=mesh.vertices[mesh.loops[li].vertex_index].co
        if facial:uv.data[li].uv=(.03+(v.x+.085)/.17*.94,.51+(v.z-1.410)/.235*.48)
        else:
            src=old.data[li].uv;uv.data[li].uv=(src.x,src.y*.48)
mesh.uv_layers.active_index=mesh.uv_layers.find('PhotorealAtlas');uv.active_render=True
# Delicate local albedo: lip vermilion, cheek/ear warmth and small, sparse freckles.
attr=mesh.color_attributes.new(name='PhotorealTint',type='FLOAT_COLOR',domain='CORNER')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co;a=abs(x);front=1-smooth(-.060,-.030,y)
    lip=(g(z,1.480+.001*g(a,.008,.004),.0028)*.65+g(z,1.473,.0032)*.70)*(1-smooth(.020,.028,a))*front
    cheek=.07*g(a,.050,.024)*g(z,1.512,.018)*front
    # RGB encodes tint amount, facial detail mask, and lip mask.
    face=smooth(1.42,1.46,z)*(1-smooth(1.61,1.65,z))*front
    attr.data[loop.index].color=(min(.85,lip),face,cheek,1)
base=p.inputs['Base Color'].links[0].from_socket
vc=nd(skin,'ShaderNodeVertexColor');vc.layer_name=attr.name
sep=nd(skin,'ShaderNodeSeparateColor');lk(skin,vc.outputs[0],sep.inputs[0])
lipmix=nd(skin,'ShaderNodeMixRGB');lipmix.inputs[2].default_value=(.46,.205,.19,1)
lk(skin,base,lipmix.inputs[1]);lk(skin,sep.outputs[0],lipmix.inputs[0])
cheekmix=nd(skin,'ShaderNodeMixRGB');cheekmix.inputs[2].default_value=(.61,.32,.27,1)
lk(skin,lipmix.outputs[0],cheekmix.inputs[1]);lk(skin,sep.outputs[2],cheekmix.inputs[0])
coords=nd(skin,'ShaderNodeTexCoord')
freckles=nd(skin,'ShaderNodeTexNoise');freckles.inputs['Scale'].default_value=1150;freckles.inputs['Detail'].default_value=1
lk(skin,coords.outputs['Object'],freckles.inputs['Vector'])
framp=nd(skin,'ShaderNodeValToRGB');framp.color_ramp.elements[0].position=.76;framp.color_ramp.elements[0].color=(0,0,0,1);framp.color_ramp.elements[1].position=.83;framp.color_ramp.elements[1].color=(.24,.24,.24,1)
lk(skin,freckles.outputs['Fac'],framp.inputs[0])
mult=nd(skin,'ShaderNodeMath');mult.operation='MULTIPLY';lk(skin,framp.outputs[0],mult.inputs[0]);lk(skin,sep.outputs[1],mult.inputs[1])
fmix=nd(skin,'ShaderNodeMixRGB');fmix.inputs[2].default_value=(.24,.12,.065,1)
lk(skin,cheekmix.outputs[0],fmix.inputs[1]);lk(skin,mult.outputs[0],fmix.inputs[0]);lk(skin,fmix.outputs[0],p.inputs['Base Color'])
# Individual pore depressions, resolved in the new face atlas.
vor=nd(skin,'ShaderNodeTexVoronoi');vor.distance='EUCLIDEAN';vor.inputs['Scale'].default_value=2100
lk(skin,coords.outputs['Object'],vor.inputs['Vector'])
pramp=nd(skin,'ShaderNodeValToRGB');pramp.color_ramp.elements[0].position=.09;pramp.color_ramp.elements[0].color=(0,0,0,1);pramp.color_ramp.elements[1].position=.24;pramp.color_ramp.elements[1].color=(.5,.5,.5,1)
lk(skin,vor.outputs['Distance'],pramp.inputs[0])
oldnormal=p.inputs['Normal'].links[0].from_socket
bump=nd(skin,'ShaderNodeBump');bump.inputs['Distance'].default_value=.00016;bump.inputs['Strength'].default_value=.22
lk(skin,pramp.outputs[0],bump.inputs['Height']);lk(skin,oldnormal,bump.inputs['Normal']);lk(skin,bump.outputs[0],p.inputs['Normal'])
# Fine vertical lip creases in the height field, localized to the lip mask.
wave=nd(skin,'ShaderNodeTexWave');wave.bands_direction='X';wave.inputs['Scale'].default_value=850;wave.inputs['Distortion'].default_value=3;wave.inputs['Detail Scale'].default_value=6
lk(skin,coords.outputs['Object'],wave.inputs['Vector'])
lipheight=nd(skin,'ShaderNodeMath');lipheight.operation='MULTIPLY';lk(skin,wave.outputs['Fac'],lipheight.inputs[0]);lk(skin,sep.outputs[0],lipheight.inputs[1])
lipbump=nd(skin,'ShaderNodeBump');lipbump.inputs['Distance'].default_value=.00010;lipbump.inputs['Strength'].default_value=.22
lk(skin,lipheight.outputs[0],lipbump.inputs['Height']);lk(skin,bump.outputs[0],lipbump.inputs['Normal']);lk(skin,lipbump.outputs[0],p.inputs['Normal'])
p.inputs['Subsurface Weight'].default_value=.055
# New hair strands originate on the real lid rim. Remove the former regular lash rows.
oldhair=bpy.data.objects.get('Castell_Facial_Hair')
if oldhair:bpy.data.objects.remove(oldhair,do_unlink=True)
bvh=BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],[list(f.vertices) for f in mesh.polygons])
def surf(x,z):
    hit=bvh.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)))
    return hit[0].y if hit[0] is not None else -.10
def mat(name,color,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=bsdf(m);b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;return m
hairmat=mat('Castell_Fine_Brows',(.022,.012,.008),.57)
lashmat=mat('Castell_Fine_Lashes',(.006,.004,.003),.34)
vertices=[];faces=[];materials=[]
def strand(points,r,material=0):
    start=len(vertices)
    for i,pt in enumerate(points):
        pt=Vector(pt);d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        axis=d.cross(Vector((0,1,0))).normalized();other=d.cross(axis).normalized();radius=r*(1-.97*i/(len(points)-1))
        for k in range(4):vertices.append(pt+radius*(math.cos(k*math.pi/2)*axis+math.sin(k*math.pi/2)*other))
    for i in range(len(points)-1):
        for k in range(4):faces.append((start+i*4+k,start+i*4+(k+1)%4,start+(i+1)*4+(k+1)%4,start+(i+1)*4+k));materials.append(material)
def interp(points,a):
    points=sorted(points,key=lambda p:abs(p.x))
    for p,q in zip(points,points[1:]):
        if abs(p.x)<=a<=abs(q.x):return p.lerp(q,(a-abs(p.x))/max(1e-9,abs(q.x)-abs(p.x)))
    return min(points,key=lambda p:abs(abs(p.x)-a)).copy()
for side in [-1,1]:
    for i in range(430):
        t=random.random();a=.017+.045*t;z=1.5725+.005*math.sin(t*math.pi)-.0025*t+random.uniform(-.0013,.0013)
        length=random.uniform(.002,.0045);rise=(.0025*(1-t)+.0003)*random.uniform(.6,1.3)
        pts=[]
        for k in range(6):
            f=k/5;x=side*(a+length*f);zz=z+rise*math.sin(f*math.pi*.65);pts.append((x,surf(x,zz)-.00018-.0001*math.sin(f*math.pi),zz))
        strand(pts,random.uniform(.000035,.000065))
    socket_side=[v for v in socket if v.x*side>0]
    for upper,count in [(True,78),(False,35)]:
        edge=[v for v in socket_side if (v.z>=1.550 if upper else v.z<=1.550)]
        for i in range(count):
            t=(i+.3+random.random()*.4)/count;a=.024+.023*t
            root=interp(edge,a);root.y-=.00024
            length=random.uniform(.0035,.0055)*(.7+.4*math.sin(t*math.pi))*(1 if upper else .55)
            pts=[]
            for k in range(7):
                f=k/6;pts.append(root+Vector((side*(t-.35)*length*.5*f,-length*.75*math.sin(f*math.pi*.65),(1 if upper else -1)*length*.65*f*f)))
            strand(pts,random.uniform(.000042,.000070),1)
data=bpy.data.meshes.new('Natural brow and eyelash fibres');data.from_pydata(vertices,[],faces);data.materials.append(hairmat);data.materials.append(lashmat)
obj=bpy.data.objects.new('Castell_Facial_Fibres',data);scene.collection.objects.link(obj);parent(obj)
for poly,idx in zip(data.polygons,materials):poly.material_index=idx;poly.use_smooth=True
# Small moist caruncles at the inner corners, without changing eye topology.
tear=mat('Castell_Tear_Duct',(.30,.12,.105),.22);bsdf(tear).inputs['Coat Weight'].default_value=.65
for side in [-1,1]:
    pt=min([p for p in socket if p.x*side>0],key=lambda p:abs(p.x))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=pt+Vector((0,-.0002,-.0002)))
    o=bpy.context.object;o.name='Castell_Tear_Duct_'+str(side);o.scale=(.00075,.00045,.00060);o.data.materials.append(tear);parent(o)
    for poly in o.data.polygons:poly.use_smooth=True
# Bake the increased facial detail into portable, high-resolution maps.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=12
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
mod=body.modifiers.get('Castell skin weights');mod.show_render=False
maps={}
for name,kind in [('albedo','DIFFUSE'),('roughness','ROUGHNESS'),('normal','NORMAL')]:
    im=bpy.data.images.new('Photoreal study '+name,width=4096,height=4096,alpha=False)
    if name!='albedo':im.colorspace_settings.name='Non-Color'
    for material in mesh.materials:
        n=nd(material,'ShaderNodeTexImage');n.image=im;material.node_tree.nodes.active=n
    bpy.ops.object.bake(type=kind);im.filepath_raw=os.path.join(OUT,name+'.png');im.file_format='PNG';im.save();im.pack();maps[name]=im;print('BAKED',name,flush=True)
mod.show_render=True
for material in mesh.materials:
    b=bsdf(material);u=nd(material,'ShaderNodeUVMap');u.uv_map='PhotorealAtlas'
    for name,socketname in [('albedo','Base Color'),('roughness','Roughness'),('normal','Normal')]:
        n=nd(material,'ShaderNodeTexImage');n.image=maps[name];lk(material,u.outputs[0],n.inputs['Vector'])
        if name=='normal':
            nm=nd(material,'ShaderNodeNormalMap');nm.uv_map='PhotorealAtlas';lk(material,n.outputs[0],nm.inputs['Color']);lk(material,nm.outputs[0],b.inputs[socketname])
        else:lk(material,n.outputs[0],b.inputs[socketname])
body['surface_detail']='Higher facial texel density; pore depressions, lip microcreases, delicate freckles; anatomical eyelash placement.'
# Remove unused packed intermediate atlases from this new file only.
bpy.ops.file.pack_all()
scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.render.resolution_x=1100;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=.37;cam.location=(.30,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-studio-fotorealismo.blend'))
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=.22;cam.location=(.15,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'dettaglio.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-photoreal-study-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('PHOTOREAL_STUDY_READY',flush=True)
