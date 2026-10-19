import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','realistic-athlete')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
scene=bpy.context.scene
for name,power,size in [('Studio Key',95,1.5),('Studio Fill',32,1.7),('Studio Rim',35,1.6)]:
    bpy.data.objects[name].data.energy=power;bpy.data.objects[name].data.size=size
bs=bpy.data.materials['Castell_Hair_HalfBun'].node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.62
scene.render.resolution_x=1000;scene.render.resolution_y=1150;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
cam=scene.camera;cam.data.ortho_scale=1.94;cam.location=(.2,-4,.96);cam.rotation_euler=(Vector((0,0,.84))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-realistic-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
