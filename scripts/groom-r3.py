"""Fine independent fibres for the detailed Blender source; reduced mesh for GLB."""
import bpy,os,math,random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(ROOT,'artifacts','asia-r3')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
random.seed(831);scene=bpy.context.scene;body=bpy.data.objects['Castell_Body'];torso=bpy.data.objects['Castell_Torso']
body_bvh=BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
for obj in list(bpy.data.objects):
    if obj.name.startswith('Castell_Hair') and obj.name!='Castell_Hair_Underlay':bpy.data.objects.remove(obj,do_unlink=True)
data=bpy.data.curves.new('Individual groomed hair fibres','CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_resolution=0;data.bevel_depth=.00013
obj=bpy.data.objects.new('Castell_Hair_Fibres',data);scene.collection.objects.link(obj)
center=Vector((0,.008,1.565));r=Vector((.095,.110,.130))
def scalp(d):return center+Vector((d.x*r.x,d.y*r.y,d.z*r.z))*1.004
def slerp(a,b,t):
    angle=a.angle(b)
    return ((a*math.sin((1-t)*angle)+b*math.sin(t*angle))/math.sin(angle)).normalized() if angle>.001 else a
def spline(points,steps=4):
    ps=[points[0]]+points+[points[-1]];out=[]
    for k in range(1,len(ps)-2):
        p0,p1,p2,p3=ps[k-1:k+3]
        for j in range(steps):
            t=j/steps;out.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return out+[points[-1]]
for index in range(6400):
    side=-1 if index%2 else 1;u=random.random();front=random.random()<.40
    y=random.uniform(-.085,.005) if front else random.uniform(.0,.10)
    x=side*random.uniform(.005,.070)-.007
    dx=x/r.x;dy=(y-.008)/r.y
    if dx*dx+dy*dy>.96:
        factor=math.sqrt(.96/(dx*dx+dy*dy));dx*=factor;dy*=factor
    start=Vector((dx,dy,math.sqrt(max(.01,1-dx*dx-dy*dy)))).normalized()
    end=Vector((side*.95,dy*.75,-.04)).normalized() if front else Vector((dx*.6,.98,-.1)).normalized()
    path=[scalp(slerp(start,end,j/9)) for j in range(10)]
    if front:
        controls=[path[-1],Vector((side*(.100+.01*u),-.11,1.48)),Vector((side*(.105+.05*u),-.19,1.33)),Vector((side*(.10+.09*u),-.22,1.17)),Vector((side*(.10+.095*u),-.21,1.065+random.uniform(-.015,.11)))]
    else:
        controls=[path[-1],Vector((x*1.2,.133,1.45)),Vector((x*1.55,.15,1.26)),Vector((x*1.8,.14,1.07+random.uniform(-.02,.10)))]
    lower=spline(controls,5)
    phase=random.uniform(0,math.tau)
    for j,p in enumerate(lower):
        t=j/max(len(lower)-1,1)
        p.x+=.0025*math.sin(t*5+phase)*t;p.y+=.0015*math.cos(t*4+phase)*t
        if front and p.z<1.39:
            q,n,face,distance=body_bvh.ray_cast(Vector((p.x,-.8,p.z)),Vector((0,1,0)))
            if q is not None:p.y=min(p.y,q.y-.006-random.random()*.003)
    path+=lower[1:]
    fibre=data.splines.new('POLY');fibre.points.add(len(path)-1)
    width=random.uniform(.65,1.30)
    for j,(point,p) in enumerate(zip(fibre.points,path)):
        t=j/(len(path)-1);point.co=(*p,1);point.radius=width*(1-.90*t**6)
material=bpy.data.materials.new('Castell_Fibre_Chestnut');material.use_nodes=True
p=material.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.025,.014,.008,1);p.inputs['Roughness'].default_value=.42
data.materials.append(material)
bpy.context.view_layer.update();m=obj.matrix_world.copy();obj.parent=torso;obj.matrix_world=m
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
camera=scene.camera;camera.data.ortho_scale=.53;camera.location=(.62,-3,1.535);camera.rotation_euler=(Vector((0,0,1.535))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1000
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
scene.render.filepath=os.path.join(OUT,'head-final.png');bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=1.94;camera.location=(1.1,-3.8,1.15);camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=850;scene.render.resolution_y=1250
scene.render.filepath=os.path.join(OUT,'full-body-final.png');bpy.ops.render.render(write_still=True)
# Preserve the detailed source; export fewer fibres to avoid an enormous web mesh.
for index in reversed(range(len(data.splines))):
    if index%8:data.splines.remove(data.splines[index])
data.bevel_depth=.00028
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.object.convert(target='MESH')
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','asia-r3-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
