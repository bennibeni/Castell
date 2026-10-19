"""Compare original/optimized textures on the clothed mannequin, identical lighting."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','head-texture-optimization')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'public','models','catalog','body-mannequin.glb'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.seed=0
world=bpy.data.worlds.new('Texture comparison studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.68,.72,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
for name,pos,power,size in [('Key',(-1,-2,2.5),95,1.4),('Fill',(1,-1,1.9),35,1.6),('Rim',(.5,1,2.4),40,1.4)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,1.57))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=power;light.data.size=size
cam=bpy.data.objects.new('Comparison camera',bpy.data.cameras.new('Comparison camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.34
scene.render.resolution_x=650;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
for version in ['original','optimized']:
    before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=os.path.join(OUT,version+'.glb'));added=set(scene.objects)-before
    factor=.9034934067618628*.9;offset=.1431342506173896*.9+1.58-1.553*.9
    for root in added:
        if root.parent in added:continue
        root.scale*=factor;root.location*=factor;root.location.z+=offset
    for view,pos in [('front',(.15,-3,1.575)),('three-quarter',(.95,-3,1.575))]:
        cam.location=pos;cam.rotation_euler=(Vector((0,0,1.575))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=os.path.join(OUT,version+'-'+view+'.png');bpy.ops.render.render(write_still=True)
    for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
print('TEXTURE_COMPARISON_READY',flush=True)
