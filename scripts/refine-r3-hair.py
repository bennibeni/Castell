"""Replace the draft locks with scalp-conforming textured hair sheets."""
import bpy,os,math,random
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','asia-r3');random.seed(121)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
scene=bpy.context.scene;torso=bpy.data.objects['Castell_Torso']
for obj in list(bpy.data.objects):
    if obj.type=='MESH' and obj.name.startswith('Castell_Hair'):bpy.data.objects.remove(obj,do_unlink=True)
image=bpy.data.images.load(os.path.join(ROOT,'blender','asia-hair-card.png'));image.pack()
mat=bpy.data.materials.new('Castell_Hair_FineStrands');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF')
p.inputs['Roughness'].default_value=.48
tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND'
links.new(tex.outputs['Color'],p.inputs['Base Color']);links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
mat.surface_render_method='DITHERED';mat.use_backface_culling=False
center=Vector((0,.008,1.565));r=Vector((.095,.110,.130))
def attach(obj):
    bpy.context.view_layer.update();m=obj.matrix_world.copy();obj.parent=torso;obj.matrix_world=m
def sphere(d):return center+Vector((d.x*r.x,d.y*r.y,d.z*r.z))*1.008
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def slerp(a,b,t):
    angle=a.angle(b)
    return ((a*math.sin((1-t)*angle)+b*math.sin(t*angle))/math.sin(angle)).normalized() if angle>.001 else a
def spline(pts,steps=5):
    result=[];ps=[pts[0]]+pts+[pts[-1]]
    for k in range(1,len(ps)-2):
        p0,p1,p2,p3=ps[k-1:k+3]
        for j in range(steps):
            t=j/steps
            result.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return result+[pts[-1]]
verts=[];faces=[];uvs=[]
def card(path,width,seed):
    base=len(verts);rng=random.Random(seed);offset=rng.uniform(.0,.16)
    for i,point in enumerate(path):
        t=i/(len(path)-1)
        tangent=(path[min(i+1,len(path)-1)]-path[max(0,i-1)]).normalized()
        radial=Vector((point.x/r.x,(point.y-.008)/r.y,max((point.z-1.565)/r.z,.0))).normalized()
        normal=(radial*smooth(1.52,1.64,point.z)+Vector((0,-1 if point.y<0 else 1,0))*(1-smooth(1.52,1.64,point.z))).normalized()
        axis=tangent.cross(normal)
        if axis.length<.01:axis=Vector((1,0,0))
        axis.normalize()
        w=width*(.65+.35*math.sin(math.pi*t))*(1-.40*t**8)
        for side in [-1,1]:
            pos=point+axis*w*.5*side
            if point.z>1.56:
                d=Vector((pos.x/r.x,(pos.y-.008)/r.y,(pos.z-1.565)/r.z)).normalized()
                pos=pos.lerp(sphere(d),smooth(1.56,1.62,point.z))
            verts.append(pos);uvs.append((offset+(.82 if side>0 else 0),1-t))
    for i in range(len(path)-1):
        a=base+i*2;faces.append((a,a+1,a+3,a+2))
for side in [-1,1]:
    for row in range(14):
        y=-.079+.164*row/13
        dx=-.012/r.x;dy=(y-.008)/r.y
        root=Vector((dx,dy,math.sqrt(max(.01,1-dx*dx-dy*dy)))).normalized()
        end=Vector((side*.92,dy*.85,-.08)).normalized()
        path=[sphere(slerp(root,end,i/13)) for i in range(14)]
        front=y<.01
        zstart=path[-1].z
        spread=(row%7)/6
        long=[path[-1],Vector((side*(.103+.008*spread),-.105 if front else .12,1.48)),Vector((side*(.105+.04*spread),-.18 if front else .145,1.34)),Vector((side*(.10+.08*spread),-.22 if front else .145,1.19)),Vector((side*(.10+.10*spread),-.22+spread*.025 if front else .13,1.12+random.uniform(-.07,.04)))]
        path+=spline(long,6)[1:]
        path=spline(path,2)
        if front:
            body=bpy.data.objects['Castell_Body']
            for point in path:
                if point.z<1.39:
                    hit,surface,normal,face=body.ray_cast(Vector((point.x,-.8,point.z)),Vector((0,1,0)))
                    if hit:point.y=min(point.y,surface.y-.010)
        card(path,.026+random.uniform(-.003,.003),row+(100 if side>0 else 0))
# Overlapping rear sheets cover the back of the head and upper back.
for i in range(14):
    phi=.15+(math.pi-.3)*i/13
    top=Vector((math.cos(phi)*.55,math.sin(phi)*.55,.835)).normalized()
    end=Vector((math.cos(phi)*.95,math.sin(phi)*.95,-.25)).normalized()
    path=[sphere(slerp(top,end,j/12)) for j in range(13)]
    x=path[-1].x
    path+=spline([path[-1],Vector((x*1.1,.14,1.43)),Vector((x*1.5,.16,1.26)),Vector((x*1.6,.15,1.08+random.uniform(-.035,.035)))],6)[1:]
    card(path,.029,i+300)
mesh=bpy.data.meshes.new('Parted layered hair sheets');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('Castell_Hair_Parted',mesh);scene.collection.objects.link(obj);mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='HairUV')
for p in mesh.polygons:
    p.use_smooth=True
    for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
attach(obj)
# Fine dark scalp beneath the transparent strands; it stops above the forehead.
vs=[];fs=[];N=64;M=20
for j in range(M+1):
    for i in range(N):
        phi=2*math.pi*i/N;front=max(0,-math.sin(phi))
        limit=1.75-.75*front+.025*math.cos(5*phi)
        th=.01+(limit-.01)*j/M
        vs.append(center+Vector((r.x*math.sin(th)*math.cos(phi),r.y*math.sin(th)*math.sin(phi),r.z*math.cos(th))))
for j in range(M):
    for i in range(N):
        a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
data=bpy.data.meshes.new('Scalp underlay');data.from_pydata(vs,[],fs);data.update()
cap=bpy.data.objects.new('Castell_Hair_Underlay',data);scene.collection.objects.link(cap)
base=bpy.data.materials.new('Castell_Hair_Shadow');base.use_nodes=True
base.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.012,.008,.006,1)
base.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
data.materials.append(base)
for p in data.polygons:p.use_smooth=True
attach(cap)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=32
camera=scene.camera;camera.data.ortho_scale=.56
camera.location=(.62,-3,1.535);camera.rotation_euler=(Vector((0,0,1.535))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=850;scene.render.resolution_y=1050
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
scene.render.filepath=os.path.join(OUT,'head-v3.png');bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=1.94;camera.location=(1.1,-3.8,1.15);camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=850;scene.render.resolution_y=1250
scene.render.filepath=os.path.join(OUT,'full-body-v3.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','asia-r3-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
