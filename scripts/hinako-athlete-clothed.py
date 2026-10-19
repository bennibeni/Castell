"""Clothed full-body preview with the prepared Hinako head and original hair."""
import bpy,bmesh,os,math,sys
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWIMSUIT='--swimsuit' in sys.argv
OUT=os.path.join(ROOT,'artifacts','hinako-swimsuit' if SWIMSUIT else 'hinako-athlete');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
body=bpy.data.objects['Castell_Body']
for obj in list(bpy.context.scene.objects):
    if obj.type=='MESH' and obj!=body:bpy.data.objects.remove(obj,do_unlink=True)
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,1.414),plane_no=(0,0,1),clear_outer=True)
bm.to_mesh(body.data);bm.free();body.data.update()
def material(name,color,roughness):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;return m
suitmat=material('Castell_Uniform',(.016,.032,.064),.84)
trim=material('Castell_Sport_Trim',(.015,.30,.34) if SWIMSUIT else (.26,.37,.44),.72)
# An opaque sports overall, with a small amount of ease around the torso.
suit=body.copy();suit.data=body.data.copy();suit.name='Castell_Sports_Overall';bpy.context.collection.objects.link(suit)
bm=bmesh.new();bm.from_mesh(suit.data)
if SWIMSUIT:
    # Finer silhouette at the arm openings and short leg hems; deform weights interpolate.
    bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,.735),plane_no=(0,0,1),clear_inner=True)
remove=[]
for face in bm.faces:
    z=sum(v.co.z for v in face.verts)/len(face.verts)
    x=sum(v.co.x for v in face.verts)/len(face.verts)
    if SWIMSUIT:
        if z<.735 or z>1.394 or (abs(x)>.153 and z>1.08):remove.append(face)
    elif z<.11 or z>1.409:remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bm.to_mesh(suit.data);bm.free();suit.data.update()
for v in suit.data.vertices:
    v.co+=v.normal*.006
    # Less cling at chest/abdomen; the original anatomy is completely covered.
    if v.co.y<-.07 and abs(v.co.x)<.14 and 1.0<v.co.z<1.31:
        v.co.y-=.009*math.sin((v.co.z-1.0)/.31*math.pi)
suit.data.materials.clear();suit.data.materials.append(suitmat);suit.data.materials.append(trim)
for p in suit.data.polygons:
    if SWIMSUIT:
        threshold=.057+.024*math.sin((p.center.z-.9)*7)
        p.material_index=1 if abs(p.center.x)>threshold and p.center.z>.81 else 0
    else:p.material_index=1 if abs(p.center.x)>.15 and 1.05<p.center.z<1.10 else 0
    p.use_smooth=True
# Append only the new head assembly; the source full character is not imported.
source=os.path.join(ROOT,'blender','Castell-testa-Hinako-capelli.blend')
names=['Castell_Hinako_Head','Castell_Hinako_Eyes','Castell_Hinako_Lashes','Castell_Hinako_Hair']
with bpy.data.libraries.load(source,link=False) as (src,dst):dst.objects=list(names)
for name in names:
    obj=bpy.data.objects[name];bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=bpy.data.objects['Castell_Torso'];obj.matrix_world=world
# High sports collar covers the neck junction.
head=bpy.data.objects['Castell_Hinako_Head'];head.data.materials.append(suitmat);idx=len(head.data.materials)-1
if not SWIMSUIT:
    for p in head.data.polygons:
        if p.center.z<1.437:p.material_index=idx
# Remove dependent, unlinked assembly empties from the imported library.
root=bpy.data.objects['Castell_Athlete'];root['description']='Clothed athlete preview with Hinako head. Opaque sports overall; no intimate anatomical additions.'
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=850;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=1.96
look=Vector((0,0,.85));cam.location=(.20,-4,1.0);cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-Hinako-costume.blend' if SWIMSUIT else 'Castell-atleta-Hinako-vestita.blend'))
scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-hinako-swimsuit-raw.glb' if SWIMSUIT else 'athlete-hinako-clothed-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('CLOTHED_HINAKO_READY',flush=True)
