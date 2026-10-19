"""Hair-only edit of the user's specified athlete; preserve the original face/body/rig."""
import bpy,os,shutil
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','reference-athlete-hinako-hair');os.makedirs(OUT,exist_ok=True)
SOURCE=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend')
BACKUP=os.path.join(ROOT,'blender','Castell-atleta-viso-reference-prima-capelli.blend')
if not os.path.exists(BACKUP):shutil.copy2(SOURCE,BACKUP)
glb=os.path.join(ROOT,'blender','athlete-reference-detail.glb')
backupglb=os.path.join(ROOT,'blender','athlete-reference-detail-prima-capelli.glb')
if os.path.exists(glb) and not os.path.exists(backupglb):shutil.copy2(glb,backupglb)
bpy.ops.wm.open_mainfile(filepath=BACKUP)
body=bpy.data.objects['Castell_Body']
before=[v.co.copy() for v in body.data.vertices]
for obj in list(bpy.context.scene.objects):
    if obj.name in {'Castell_Torso_hair','Castell_Torso_bun','Castell_Hair_HalfBun','Castell_Hinako_Hair'}:
        bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(os.path.join(ROOT,'artifacts','hinako','hair-component.blend'),link=False) as (src,dst):dst.objects=['Castell_Hinako_Hair']
hair=bpy.data.objects['Castell_Hinako_Hair'];bpy.context.collection.objects.link(hair)
for v in hair.data.vertices:
    v.co.x*=.90;v.co.y=v.co.y*.90+.012;v.co.z=1.55+(v.co.z-1.553)*.93
    front=max(0,min(1,(.04-v.co.y)/.12))
    v.co.y-=.026*front
hair.data.update()
bpy.context.view_layer.update();world=hair.matrix_world.copy();hair.parent=bpy.data.objects['Castell_Torso'];hair.matrix_world=world
hair['description']='Hair only, adapted to the original Castell reference face; no Hinako head imported.'
assert len(before)==len(body.data.vertices)
assert all((a-v.co).length<1e-9 for a,v in zip(before,body.data.vertices))
assert not any(o.name in {'Castell_Hinako_Head','Castell_Hinako_Eyes','Castell_Hinako_Lashes'} for o in bpy.context.scene.objects)
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.47;cam.location=(.45,-3,1.54);cam.rotation_euler=(Vector((0,.01,1.53))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=750;scene.render.resolution_y=900;scene.render.resolution_percentage=100
bpy.ops.object.select_all(action='DESELECT');hair.select_set(True);bpy.context.view_layer.objects.active=hair
bpy.ops.wm.save_as_mainfile(filepath=SOURCE)
scene.render.filepath=os.path.join(OUT,'viso-capelli.png');bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=1.96;cam.location=(.15,-4,.95);cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=750;scene.render.resolution_y=1050;scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-reference-hinako-hair-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('HAIR_ONLY_READY: original body vertices unchanged; no new head imported',flush=True)
