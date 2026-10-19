"""A separate reference-inspired sculpt; geometry and exportable surface detail."""
import bpy,os,math,random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','reference-detail');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-base-animabile.blend'))
body=bpy.data.objects['Castell_Body'];mesh=body.data
def g(x,c,w):return math.exp(-.5*((x-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
# Small, symmetric anatomical edits, including eyeballs in the same mesh.
for v in mesh.vertices:
    x,y,z=v.co;a=abs(x)
    if z<1.405:continue
    front=1-smooth(-.045,.015,y)
    # Softer lower jaw, delicate nose tip/bridge and fuller lip profile.
    dx=-x*.075*g(z,1.445,.027)
    dx+=x*.022*g(z,1.515,.025)
    dy=front*(.0035*g(x,0,.018)*g(z,1.535,.024)-.0017*g(x,0,.023)*g(z,1.480,.009))
    dz=.003*g(z,1.433,.026)
    # Slight outward tilt of the eye corners; no drastic eye scaling.
    dz+=front*.0015*g(a,.052,.009)*g(z,1.551,.009)
    v.co=(x+dx,y+dy,z+dz)
mesh.update()
# Tinted skin retains the packed source atlas through an explicit original UV map.
skin=bpy.data.materials['Castell_Skin'];ns=skin.node_tree.nodes;ls=skin.node_tree.links
bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
tex=next(n for n in ns if n.type=='TEX_IMAGE' and n.image)
uv=ns.new('ShaderNodeUVMap');uv.uv_map='UVMap';ls.new(uv.outputs[0],tex.inputs['Vector'])
attr=mesh.color_attributes.new(name='FacialTint',type='FLOAT_COLOR',domain='CORNER')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co;a=abs(x);front=1-smooth(-.060,-.025,y)
    color=Vector((.66,.47,.37))
    # Diffuse lip tint fits the existing vermilion; not a projected photograph.
    lip=(g(z,1.478+.002*g(a,.009,.006),.0027)*.78+g(z,1.472,.0030)*.65)
    lip*=1-smooth(.020,.029,a);lip=min(.82,lip)*front
    color=color.lerp(Vector((.43,.17,.16)),lip)
    cheek=.14*g(a,.052,.023)*g(z,1.510,.019)*front
    color=color.lerp(Vector((.68,.32,.29)),cheek)
    lid=.20*g(a,.036,.017)*g(z,1.561,.0035)*front
    color=color.lerp(Vector((.34,.22,.20)),lid)
    attr.data[loop.index].color=(*color,1)
vc=ns.new('ShaderNodeVertexColor');vc.layer_name=attr.name
mix=ns.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.87
ls.new(tex.outputs['Color'],mix.inputs[1]);ls.new(vc.outputs['Color'],mix.inputs[2]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.48
# Brow strands and eyelashes are real geometry attached to the torso control.
bvh=BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
def surface(x,z):
    hit=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
    return hit[0].y if hit[0] is not None else -.10
hairmat=bpy.data.materials.new('Castell_Brows_Lashes');hairmat.diffuse_color=(.028,.018,.014,1);hairmat.use_nodes=True
hb=hairmat.node_tree.nodes.get('Principled BSDF');hb.inputs['Base Color'].default_value=hairmat.diffuse_color;hb.inputs['Roughness'].default_value=.62
verts=[];faces=[]
def strand(points,radius):
    start=len(verts)
    for i,p in enumerate(points):
        p=Vector(p);r=radius*(1-.85*i/(len(points)-1))
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        axis=tangent.normalized().cross(Vector((0,1,0))).normalized();other=tangent.normalized().cross(axis).normalized()
        for k in range(4):verts.append(tuple(p+r*(math.cos(k*math.pi/2)*axis+math.sin(k*math.pi/2)*other)))
    for i in range(len(points)-1):
        for k in range(4):faces.append((start+i*4+k,start+i*4+(k+1)%4,start+(i+1)*4+(k+1)%4,start+(i+1)*4+k))
random.seed(25)
for side in [-1,1]:
    for i in range(600):
        t=random.random();a=.017+.046*t
        z=1.573+.005*math.sin(t*math.pi)-.003*t+random.uniform(-.0018,.0018)
        points=[]
        for j in range(4):
            u=j/3;x=side*(a+.0035*u);zz=z+.0022*math.sin(u*math.pi*.7)
            points.append((x,surface(x,zz)-.00035,zz))
        strand(points,.00014*(.6+.4*math.sin(t*math.pi)))
    for i in range(30):
        t=.04+.92*i/29;a=.020+.032*t
        z=1.5505+.0053*math.sin(t*math.pi)+.0015*t
        x=side*a;y=surface(x,z)-.0013;length=.004+.003*t
        strand([(x,y,z),(x+side*.0005,y-length*.5,z+.0005),(x+side*.001,y-length*.85,z+.002),(x+side*.0015,y-length,z+.0035)],.00018)
geo=bpy.data.meshes.new('Eyebrow and eyelash strands');geo.from_pydata(verts,[],faces);geo.materials.append(hairmat)
obj=bpy.data.objects.new('Castell_Facial_Hair',geo);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=bpy.data.objects['Castell_Torso'];obj.matrix_world=world
for p in geo.polygons:p.use_smooth=True
# Bake the procedural tint to a conventional atlas supported by browser renderers.
eyes=bpy.data.materials['Castell_Eyes']
eyeattr=mesh.color_attributes.new(name='BrownIris',type='FLOAT_COLOR',domain='CORNER')
eyeidx=list(mesh.materials).index(eyes)
for p in mesh.polygons:
    if p.material_index!=eyeidx:continue
    for li in p.loop_indices:
        x,y,z=mesh.vertices[mesh.loops[li].vertex_index].co
        dx=abs(x)-.036;dz=z-1.550;r=math.sqrt(dx*dx+dz*dz)
        if r<.0028:c=(.004,.003,.002,1)
        elif r<.0072:
            f=.75+.25*math.sin(math.atan2(dz,dx)*37)
            c=(.095*f,.043*f,.019*f,1)
        elif r<.008:c=(.019,.012,.009,1)
        else:c=(.78,.77,.73,1)
        eyeattr.data[li].color=c
en=eyes.node_tree.nodes;el=eyes.node_tree.links;eb=next(n for n in en if n.type=='BSDF_PRINCIPLED')
ev=en.new('ShaderNodeVertexColor');ev.layer_name='BrownIris';el.new(ev.outputs['Color'],eb.inputs['Base Color'])
for mat in [eyes]:
    for n in mat.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:
            u=mat.node_tree.nodes.new('ShaderNodeUVMap');u.uv_map='UVMap';mat.node_tree.links.new(u.outputs[0],n.inputs['Vector'])
atlasuv=mesh.uv_layers.new(name='CastellFaceAtlas');mesh.uv_layers.active_index=mesh.uv_layers.find(atlasuv.name);atlasuv.active_render=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
atlas=bpy.data.images.new('Castell reference-inspired facial colors',width=4096,height=4096,alpha=False)
for mat in mesh.materials:
    n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=atlas;mat.node_tree.nodes.active=n
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=8
mod=body.modifiers.get('Castell skin weights');mod.show_render=False
bpy.ops.object.bake(type='DIFFUSE');mod.show_render=True
atlas.filepath_raw=os.path.join(OUT,'face-skin-atlas.png');atlas.file_format='PNG';atlas.save();atlas.pack()
for mat in mesh.materials:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');n=nodes.new('ShaderNodeTexImage');n.image=atlas
    u=nodes.new('ShaderNodeUVMap');u.uv_map='CastellFaceAtlas';links.new(u.outputs[0],n.inputs['Vector']);links.new(n.outputs['Color'],bs.inputs['Base Color'])
body['face_revision']='Reference-inspired local sculpt, lip/cheek tint, individually modeled eyebrow and eyelash strands; no portrait projection.'
scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=750;scene.render.resolution_y=850;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=.36
def render(name,pos,look):
    cam.location=pos;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)
cam.location=(0,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend'))
render('viso-frontale',(0,-3,1.54),(0,0,1.54))
render('viso-tre-quarti',(.85,-3,1.54),(0,0,1.54))
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-reference-detail-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('FACIAL_DETAIL_READY')
