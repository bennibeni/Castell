import bpy, os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'blender','Castell-atleta-viso-reference.blend'))
scene=bpy.context.scene
camera=scene.camera
camera.data.type='ORTHO';camera.data.ortho_scale=1.92
camera.location=(.15,-4,.94)
camera.rotation_euler=(Vector((0,0,.84))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.cycles.samples=32
scene.render.filepath=os.path.join(root,'artifacts','reference-detail','figura-intera.png')
bpy.ops.render.render(write_still=True)
