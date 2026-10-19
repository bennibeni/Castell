"""Render the procedural original head and the corresponding catalog mannequin."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-manichino-testa-nuova.blend'))
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH','EMPTY','ARMATURE'}:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'public','models','catalog','body-mannequin.glb'))
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'public','models','catalog','head-mannequin-original.glb'))
head=bpy.data.objects['Castell_Original_Head'];head.scale*=.9;head.location.z+=1.58-1.553*.9
scene=bpy.context.scene;scene.cycles.samples=24;scene.cycles.use_denoising=True
cam=scene.camera
def render(name,target,scale,width,height):
    cam.location=Vector(target)+Vector((.15,-4,0));cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100
    scene.render.filepath=os.path.join(ROOT,'public','previews',name+'.png');bpy.ops.render.render(write_still=True)
render('head-mannequin-original',(0,0,1.59),.39,450,550)
render('body-mannequin-original',(0,0,.88),1.95,450,650)
print('ORIGINAL_HEAD_PREVIEWS_READY',flush=True)
