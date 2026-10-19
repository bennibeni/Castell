"""Original segmented Castell mannequin with the prepared head; no anatomical additions."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','castell-mannequin-new-head');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
reference=os.path.join(ROOT,'blender','athlete-reference.glb')
if not os.path.exists(reference):reference=os.path.join(ROOT,'artifacts','public-archive','models','athlete-reference.glb')
bpy.ops.import_scene.gltf(filepath=reference)
for obj in list(bpy.context.scene.objects):
    if obj.name in {'Castell_Torso_head','Castell_Torso_hair','Castell_Torso_bun','Castell_Torso_neck'}:bpy.data.objects.remove(obj,do_unlink=True)
skin=bpy.data.materials['Castell_Skin'];skin.use_nodes=True
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
color=tuple(linear(v/255) for v in (219,163,138))+(1,)
skin.diffuse_color=color;p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.72
names=['Castell_Hinako_Head','Castell_Hinako_Eyes','Castell_Hinako_Lashes','Castell_Hinako_Hair']
with bpy.data.libraries.load(os.path.join(ROOT,'blender','Castell-testa-Hinako-capelli.blend'),link=False) as (src,dst):dst.objects=list(names)
torso=bpy.data.objects['Castell_Torso']
for name in names:
    obj=bpy.data.objects[name];bpy.context.collection.objects.link(obj)
    for v in obj.data.vertices:v.co=Vector((v.co.x*.9,v.co.y*.9,1.58+(v.co.z-1.553)*.9))
    bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=torso;obj.matrix_world=world
root=bpy.data.objects['Castell_Athlete'];root['description']='Original segmented Castell mannequin, new head and hair, warmer painted skin color. No anatomical intimate details or additional costume.'
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Mannequin studio');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.7,.73,.77,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
for name,pos,energy,size in [('Key',(-2,-3,3),150,3),('Fill',(2,-2,2),60,3),('Rim',(0,2,3),70,2)]:
    obj=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=energy;obj.data.size=size
cam=bpy.data.objects.new('Preview',bpy.data.cameras.new('Preview'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.02;cam.location=(.3,-4,1.02);cam.rotation_euler=(Vector((0,0,.88))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1150;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-manichino-testa-nuova.blend'))
scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-mannequin-new-head.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('MANNEQUIN_NEW_HEAD_READY',flush=True)
