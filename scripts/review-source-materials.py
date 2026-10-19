import bpy,os
from mathutils import Vector
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'artifacts','source-model-review');os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
for obj in list(scene.objects):
    if obj.type=='LIGHT':bpy.data.objects.remove(obj,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.8,.8,.8,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
for name,pos,power in [('Key',(-2,-3,4),180),('Fill',(2,-2,2),90)]:
    obj=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=power;obj.data.size=3
camera=bpy.data.objects.new('Material review',bpy.data.cameras.new('Material review'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
scene.view_settings.view_transform='AgX';scene.render.resolution_percentage=100
for name,center,distance,rx,ry in [('materials-full',Vector((0,0,.87)),1.95,650,900),('materials-face',Vector((0,0,1.59)),.40,650,750)]:
    camera.location=center+Vector((.35,-4,.10));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=distance
    scene.render.resolution_x=rx;scene.render.resolution_y=ry;scene.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
