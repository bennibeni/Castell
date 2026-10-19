"""Neutral anatomical details on the fictional, procedurally textured adult base."""
import bpy,os,math,random,bmesh,sys
from array import array
from mathutils import Vector,geometry
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKED='--marked' in sys.argv
VARIANT='anatomical-defined' if MARKED else 'anatomical-base'
BLEND_NAME='Castell-atleta-anatomia-definita.blend' if MARKED else 'Castell-atleta-base-anatomica.blend'
RAW_NAME='athlete-anatomical-defined-raw.glb' if MARKED else 'athlete-anatomical-raw.glb'
OUT=os.path.join(ROOT,'artifacts',VARIANT);os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
body=bpy.data.objects['Castell_Body'];mesh=body.data
random.seed(48)
# Local subdivisions retain deform weights and UVs and allow a real navel depression.
bm=bmesh.new();bm.from_mesh(mesh)
edges=[e for e in bm.edges if all(abs(v.co.x)<.026 and 1.015<v.co.z<1.075 and v.co.y<-.09 for v in e.verts)]
if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
bm.to_mesh(mesh);bm.free()
for v in mesh.vertices:
    x,y,z=v.co
    if y>-.075:continue
    navel=math.exp(-.5*((x/.0038)**2+((z-1.046)/.0058)**2))
    v.co.y+=(.0032 if MARKED else .0024)*navel
    mound=math.exp(-.5*((x/.029)**2+((z-.875)/.026)**2))
    v.co.y-=.0014*mound
mesh.update();mesh.calc_loop_triangles()
triangles=list(mesh.loop_triangles)
tree=BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],[list(t.vertices) for t in triangles],all_triangles=True)
uv=mesh.uv_layers['CastellFaceAtlas']
skin=bpy.data.materials['Castell_Skin'];bs=next(n for n in skin.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
image=bs.inputs['Base Color'].links[0].from_node.image
pixels=array('f',[0.0])*len(image.pixels)
image.pixels.foreach_get(pixels)
def surface(x,z):
    hit,normal,index,d=tree.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
    if hit is None:raise RuntimeError('Anatomical surface missing')
    tri=triangles[index];points=[mesh.vertices[i].co for i in tri.vertices]
    uvs=[Vector((*uv.data[li].uv,0)) for li in tri.loops]
    tex=geometry.barycentric_transform(hit,*points,*uvs)
    px=max(0,min(image.size[0]-1,int(tex.x*image.size[0])));py=max(0,min(image.size[1]-1,int(tex.y*image.size[1])))
    offset=(py*image.size[0]+px)*4
    # Loaded PNG pixels are encoded sRGB; float color attributes expect linear RGB.
    def linear(value):return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    color=Vector(tuple(linear(value) for value in pixels[offset:offset+3]))
    bary=geometry.barycentric_transform(hit,*points,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    weights={}
    for vi,amount in zip(tri.vertices,bary):
        for group in mesh.vertices[vi].groups:weights[group.group]=weights.get(group.group,0)+max(0,amount)*group.weight
    total=sum(weights.values());weights={k:w/total for k,w in weights.items()} if total else {}
    return hit,normal,color,weights
def material(name,roughness):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=roughness
    vc=n.new('ShaderNodeVertexColor');vc.layer_name='AnatomicalColor';m.node_tree.links.new(vc.outputs['Color'],p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value=.04
    return m
def skinned_object(name,verts,faces,colors,weights,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();data.materials.append(mat)
    attr=data.color_attributes.new(name='AnatomicalColor',type='FLOAT_COLOR',domain='CORNER')
    for loop in data.loops:attr.data[loop.index].color=(*colors[loop.vertex_index],1)
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.parent=bpy.data.objects['Castell_Athlete']
    for group in body.vertex_groups:obj.vertex_groups.new(name=group.name)
    for vi,values in enumerate(weights):
        for gi,w in values.items():
            if w>1e-6:obj.vertex_groups[gi].add([vi],w,'REPLACE')
    modifier=obj.modifiers.new('Follow body skinning','ARMATURE');modifier.object=bpy.data.objects['Castell_Skin_Rig']
    for p in data.polygons:p.use_smooth=True
    return obj
areolamat=material('Castell_Anatomical_Skin',.58)
for side in [-1,1]:
    cx=side*.073;cz=1.207
    verts=[];colors=[];weights=[];faces=[]
    # Skin-colored perimeter blends into the sampled body texture without an alpha decal.
    for ring in range(25):
        count=1 if ring==0 else 64;r=ring/24
        for k in range(count):
            a=2*math.pi*k/count
            scale=1.45 if MARKED else 1.0
            x=cx+.0115*scale*r*math.cos(a);z=cz+.0104*scale*r*math.sin(a)
            pt,n,color,w=surface(x,z)
            nipple=(.0025 if MARKED else .0018)*math.exp(-.5*(r/(.14 if MARKED else .17))**4)
            relief=.00013*math.exp(-.5*((r-.65)/.25)**2)
            pt+=n*(.00007+nipple+relief)
            fade=(1-r**8)*(.58 if MARKED else .36)
            tone=Vector((.31,.125,.105) if MARKED else (.39,.20,.16));grain=.025*math.sin(k*11.7+ring*5.3)
            color=color.lerp(tone,min(.68 if MARKED else .55,max(0,fade+grain*(1-r))))
            if r<.22:color=color.lerp(tone,.12)
            verts.append(pt);colors.append(color);weights.append(w)
    for k in range(64):faces.append((0,1+k,1+(k+1)%64))
    for ring in range(1,24):
        a=1+(ring-1)*64;b=a+64
        for k in range(64):faces.append((a+k,a+(k+1)%64,b+(k+1)%64,b+k))
    skinned_object('Castell_Anatomical_Areola_'+str(side),verts,faces,colors,weights,areolamat)
# A small inset crease follows the true navel indentation, with no floating dark disk.
verts=[];colors=[];weights=[];faces=[]
for ring in range(13):
    count=1 if ring==0 else 40;r=ring/12
    for k in range(count):
        a=2*math.pi*k/count;pt,n,color,w=surface(.0045*r*math.cos(a),1.046+.0065*r*math.sin(a))
        pt+=n*.00005
        color=color.lerp(Vector((.17,.085,.060)),(.52 if MARKED else .38)*(1-r)**1.4)
        verts.append(pt);colors.append(color);weights.append(w)
for k in range(40):faces.append((0,1+k,1+(k+1)%40))
for ring in range(1,12):
    a=1+(ring-1)*40;b=a+40
    for k in range(40):faces.append((a+k,a+(k+1)%40,b+(k+1)%40,b+k))
skinned_object('Castell_Anatomical_Navel',verts,faces,colors,weights,areolamat)
# Short, irregular pubic fibres on the mound, stopping above the inner-thigh opening.
verts=[];faces=[];colors=[];weights=[]
for i in range(950 if MARKED else 650):
    t=random.random();z=.843+.067*t;width=.009+.034*t
    x=random.uniform(-width,width)
    pt,n,color,w=surface(x,z);length=random.uniform(.004,.010);phase=random.uniform(0,math.tau)
    start=len(verts);shade=random.uniform(.7,1.3)
    for j in range(7):
        f=j/6;point=pt+n*(.00015+.0014*math.sin(f*math.pi*.7))+Vector((math.sin(phase+f*3)*length*.20*f,0,-length*f))
        radius=(.000055 if MARKED else .000045)*(1-.90*f)
        for k in range(3):
            a=k*math.tau/3;verts.append(point+Vector((math.cos(a)*radius,math.sin(a)*radius,0)));colors.append(Vector((.021,.011,.007))*shade);weights.append(w)
    for j in range(6):
        for k in range(3):faces.append((start+j*3+k,start+j*3+(k+1)%3,start+(j+1)*3+(k+1)%3,start+(j+1)*3+k))
skinned_object('Castell_Anatomical_PubicHair',verts,faces,colors,weights,material('Castell_Pubic_Fibres',.70))
body['description']='Fictional adult anatomical base; procedural face, no photographic portrait texture; modest nipples/areolae, navel and pubic mound/hair.'
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=1150;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=1.94;cam.location=(.18,-4,.94);cam.rotation_euler=(Vector((0,0,.84))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender',BLEND_NAME))
scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender',RAW_NAME),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('ANATOMICAL_BASE_READY',flush=True)
