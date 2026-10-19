"""Nonsexual, opaque two-piece sports swimwear variant; neutral full-body preview."""
import bpy,bmesh,os,sys
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOWRISE='--low-rise' in sys.argv
OUT=os.path.join(ROOT,'artifacts','hinako-yellow-bikini-low-rise' if LOWRISE else 'hinako-yellow-swimwear');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-Hinako-costume.blend'))
suit=bpy.data.objects['Castell_Sports_Overall'];body=bpy.data.objects['Castell_Body']
bm=bmesh.new();bm.from_mesh(suit.data)
# Straight cut planes preserve full chest and pelvic coverage, with an exposed midriff.
waist=.955 if LOWRISE else 1.025
for z in [waist,1.142]:
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,z),plane_no=(0,0,1))
def neckline(x):return 1.305+.075*min(abs(x)/.105,1)**4
def legline(x,y):return (.780 if y<-.025 else .765)+.055*min(abs(x)/.155,1)**1.5
remove=[]
for face in bm.faces:
    c=face.calc_center_median()
    if waist<c.z<1.142 or (LOWRISE and (c.z<legline(c.x,c.y) or c.z>neckline(c.x))):remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES')
boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
hems={v:(waist if abs(v.co.z-waist)<.0001 else 1.142) for v in boundary if abs(v.co.z-waist)<.0001 or abs(v.co.z-1.142)<.0001}
legs={v for v in boundary if LOWRISE and v.co.z<.9}
neck={v for v in boundary if LOWRISE and v.co.z>1.285 and abs(v.co.x)<.115}
for _ in range(7 if LOWRISE else 3):
    new={}
    for v in boundary:
        neighbors=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(neighbors)==2:new[v]=v.co*.6+(neighbors[0].co+neighbors[1].co)*.2
    for v,co in new.items():v.co=co
tree=BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
for v in boundary:
    pt,n,idx,d=tree.find_nearest(v.co)
    if pt is not None:v.co=pt+n*.006
    if v in hems:v.co.z=hems[v]
    elif v in legs:v.co.z=legline(v.co.x,v.co.y)
    elif v in neck:v.co.z=neckline(v.co.x)
bm.to_mesh(suit.data);bm.free();suit.data.update();suit.name='Castell_Sports_Bikini'
mat=bpy.data.materials.new('Castell_Yellow_Swimwear');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.95,.60,.018,1);p.inputs['Roughness'].default_value=.64;p.inputs['Metallic'].default_value=0
trim=bpy.data.materials.new('Castell_Yellow_Swimwear_Trim');trim.use_nodes=True
tp=trim.node_tree.nodes.get('Principled BSDF');tp.inputs['Base Color'].default_value=(.28,.15,.012,1);tp.inputs['Roughness'].default_value=.72
suit.data.materials.clear();suit.data.materials.append(mat);suit.data.materials.append(trim)
for face in suit.data.polygons:
    z=face.center.z
    face.material_index=0
    face.use_smooth=True
bpy.data.objects['Castell_Athlete']['description']='Neutral athlete in opaque yellow two-piece sports swimwear, with full chest and pelvic coverage.'
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
bpy.ops.object.select_all(action='DESELECT');suit.select_set(True);bpy.context.view_layer.objects.active=suit
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-Hinako-bikini-giallo-vita-bassa.blend' if LOWRISE else 'Castell-atleta-Hinako-bikini-sportivo-giallo.blend'))
scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-hinako-yellow-bikini-low-rise-raw.glb' if LOWRISE else 'athlete-hinako-yellow-swimwear-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('YELLOW_SPORT_SWIMWEAR_READY',flush=True)
