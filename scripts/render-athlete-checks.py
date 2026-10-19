import bpy, os, json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=os.path.join(root,'artifacts','athlete')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=650
scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'))
scene.collection.objects.link(camera)
scene.camera=camera
camera.data.type='ORTHO'
camera.data.ortho_scale=2.05
camera.location=(2,-4,1.7)
camera.rotation_euler=(Vector((0,0,.85))-camera.location).to_track_quat('-Z','Y').to_euler()
for name in ['rest','support','squat','salute']:
    for obj in list(bpy.data.objects):
        if obj.type=='MESH': bpy.data.objects.remove(obj,do_unlink=True)
    with open(os.path.join(out,'pose-'+name+'.json')) as f: meshes=json.load(f)
    for item in meshes:
        data=bpy.data.meshes.new(item['name'])
        data.from_pydata(item['points'],[],item['faces'])
        data.update()
        obj=bpy.data.objects.new(item['name'],data)
        scene.collection.objects.link(obj)
        material=bpy.data.materials.new(item['name'])
        material.diffuse_color=(*item['color'],1)
        data.materials.append(material)
        for p in data.polygons:p.use_smooth=True
    scene.render.filepath=os.path.join(out,'verified-'+name+'.png')
    bpy.ops.render.render(write_still=True)
