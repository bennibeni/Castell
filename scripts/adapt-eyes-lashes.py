"""Borrow eye/lash detail while preserving the original adult facial geometry."""
import bpy,bmesh,os,shutil
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','reference-eyes-lashes');os.makedirs(OUT,exist_ok=True)
SOURCE=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend')
BACKUP=os.path.join(ROOT,'blender','Castell-atleta-viso-reference-prima-occhi.blend')
if not os.path.exists(BACKUP):shutil.copy2(SOURCE,BACKUP)
glb=os.path.join(ROOT,'blender','athlete-reference-detail.glb')
backupglb=os.path.join(ROOT,'blender','athlete-reference-detail-prima-occhi.glb')
if not os.path.exists(backupglb):shutil.copy2(glb,backupglb)
bpy.ops.wm.open_mainfile(filepath=BACKUP)
body=bpy.data.objects['Castell_Body'];mesh=body.data
eyeidx=next(i for i,m in enumerate(mesh.materials) if m.name=='Castell_Eyes')
eyeids={i for f in mesh.polygons if f.material_index==eyeidx for i in f.vertices}
skinids={i for f in mesh.polygons if f.material_index!=eyeidx for i in f.vertices}
originalskin=sorted(tuple(round(v,8) for v in mesh.vertices[i].co) for i in skinids)
targets={}
for side in [-1,1]:
    pts=[mesh.vertices[i].co.copy() for i in eyeids if mesh.vertices[i].co.x*side>0]
    targets[side]=([min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)])
edges={}
for f in mesh.polygons:
    if f.material_index==eyeidx:continue
    for edge in f.edge_keys:edges[edge]=edges.get(edge,0)+1
socketids={i for e,n in edges.items() if n==1 for i in e}
socket=[mesh.vertices[i].co.copy() for i in socketids if 1.53<mesh.vertices[i].co.z<1.57 and mesh.vertices[i].co.y<-.06]
socketset={i for i in socketids if 1.53<mesh.vertices[i].co.z<1.57 and mesh.vertices[i].co.y<-.06}
segments=[(mesh.vertices[a].co.copy(),mesh.vertices[b].co.copy()) for (a,b),count in edges.items() if count==1 and a in socketset and b in socketset]
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==eyeidx],context='FACES')
bm.to_mesh(mesh);bm.free();mesh.update()
# Keep the original eyebrow fibres, remove only the former lash rows.
old=bpy.data.objects.get('Castell_Facial_Hair')
if old:
    bm=bmesh.new();bm.from_mesh(old.data)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<1.566],context='VERTS')
    bm.to_mesh(old.data);bm.free();old.data.update()
names=['Castell_Hinako_Eyes','Castell_Hinako_Lashes']
with bpy.data.libraries.load(os.path.join(ROOT,'blender','Castell-testa-Hinako.blend'),link=False) as (src,dst):dst.objects=list(names)
eyes=bpy.data.objects['Castell_Hinako_Eyes'];lashes=bpy.data.objects['Castell_Hinako_Lashes']
sources={}
for side in [-1,1]:
    pts=[v.co.copy() for v in eyes.data.vertices if v.co.x*side>0]
    sources[side]=([min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)])
def fit(co,lash=False):
    side=1 if co.x>=0 else -1
    lo,hi=sources[side];a,b=targets[side]
    result=Vector([a[k]+(co[k]-lo[k])/(hi[k]-lo[k])*(b[k]-a[k]) for k in range(3)])
    if lash:result.y=co.y-lo[1]+a[1]
    return result
for v in eyes.data.vertices:v.co=fit(v.co)
eyes.data.update()
# Individual lash components: exclude donor brow fragments, then align their roots to the original lids.
bm=bmesh.new();bm.from_mesh(lashes.data)
seen=set();components=[]
for seed in bm.verts:
    if seed in seen:continue
    stack=[seed];seen.add(seed);group=[]
    while stack:
        v=stack.pop();group.append(v)
        for e in v.link_edges:
            other=e.other_vert(v)
            if other not in seen:seen.add(other);stack.append(other)
    components.append(group)
remove=[];kept=0
for group in components:
    if sum(v.co.z for v in group)/len(group)>1.569:
        remove.extend(group);continue
    for v in group:v.co=fit(v.co,lash=True)
    side=1 if sum(v.co.x for v in group)>0 else -1
    candidates=[(a,b) for a,b in segments if a.x*side>0 and b.x*side>0]
    if len(group)<180:
        pairs=[]
        for v in group:
            for a,b in candidates:
                d=b-a;t=max(0,min(1,(v.co-a).dot(d)/max(d.length_squared,1e-12)))
                pairs.append((v,a+d*t))
        root,pt=min(pairs,key=lambda pair:(pair[0].co-pair[1]).length_squared)
        delta=pt-root.co+Vector((0,-.00028,0))
        for v in group:v.co+=delta
    kept+=1
if remove:bmesh.ops.delete(bm,geom=remove,context='VERTS')
bm.to_mesh(lashes.data);bm.free();lashes.data.update()
print('LASH_COMPONENTS',len(components),'kept',kept,flush=True)
for obj,name in [(eyes,'Castell_Adapted_Eyes'),(lashes,'Castell_Adapted_Lashes')]:
    bpy.context.collection.objects.link(obj);obj.name=name
    bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=bpy.data.objects['Castell_Torso'];obj.matrix_world=world
    for f in obj.data.polygons:f.use_smooth=True
eyes['description']='Detailed iris/eye material fitted to the adult original eye dimensions; original eyelids unchanged.'
lashes['description']='Lashes fitted to the original adult eyelid rims; no donor face geometry imported.'
# Reduce the donor texture's exposed red border, preserving its iris detail.
eyemat=eyes.data.materials[0];nodes=eyemat.node_tree.nodes;links=eyemat.node_tree.links
ep=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');source=ep.inputs['Base Color'].links[0].from_socket
sep=nodes.new('ShaderNodeSeparateColor');links.new(source,sep.inputs[0])
red=nodes.new('ShaderNodeMath');red.operation='SUBTRACT';links.new(sep.outputs['Red'],red.inputs[0]);links.new(sep.outputs['Green'],red.inputs[1])
threshold=nodes.new('ShaderNodeMath');threshold.operation='SUBTRACT';threshold.inputs[1].default_value=.10;links.new(red.outputs[0],threshold.inputs[0])
amount=nodes.new('ShaderNodeMath');amount.operation='MULTIPLY';amount.use_clamp=True;amount.inputs[1].default_value=2.5;links.new(threshold.outputs[0],amount.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(.78,.74,.69,1);links.new(source,mix.inputs[1]);links.new(amount.outputs[0],mix.inputs[0])
output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
emission=nodes.new('ShaderNodeEmission');links.new(mix.outputs[0],emission.inputs['Color']);links.new(emission.outputs[0],output.inputs['Surface'])
atlas=bpy.data.images.new('Adapted detailed iris and sclera',width=2048,height=2048,alpha=False)
target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
bpy.ops.object.select_all(action='DESELECT');eyes.select_set(True);bpy.context.view_layer.objects.active=eyes
bpy.context.scene.cycles.samples=1;bpy.ops.object.bake(type='EMIT')
atlas.filepath_raw=os.path.join(OUT,'eyes-color.png');atlas.file_format='PNG';atlas.save();atlas.pack()
links.new(target.outputs['Color'],ep.inputs['Base Color']);links.new(ep.outputs['BSDF'],output.inputs['Surface'])
ep.inputs['Coat Weight'].default_value=1;ep.inputs['Coat Roughness'].default_value=.035
assert not any(o.name=='Castell_Hinako_Head' for o in bpy.context.scene.objects)
currentskin=sorted(tuple(round(v,8) for v in mesh.vertices[i].co) for i in {i for f in mesh.polygons if f.material_index!=eyeidx for i in f.vertices})
assert originalskin==currentskin,'Original skin geometry must not change'
scene=bpy.context.scene;scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=850;scene.render.resolution_y=950;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=.42;cam.location=(.35,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');eyes.select_set(True);bpy.context.view_layer.objects.active=eyes
bpy.ops.wm.save_as_mainfile(filepath=SOURCE)
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
cam.location=(1.1,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'tre-quarti.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-reference-eyes-lashes-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('ADAPTED_EYES_LASHES_READY: adult facial skin geometry unchanged',flush=True)
