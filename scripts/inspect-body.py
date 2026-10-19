import bpy, math, os
from mathutils import Vector

out = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'athlete')
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.world.color = (0.22, 0.22, 0.22)
camera_data = bpy.data.cameras.new('Inspection')
camera = bpy.data.objects.new('Inspection', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 1.95
for name, pos in [('front', (0,-4,0.88)), ('side', (4,0,0.88))]:
    camera.location = pos
    camera.rotation_euler = (Vector((0,0,0.88))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(out, 'source-'+name+'.png')
    bpy.ops.render.render(write_still=True)
