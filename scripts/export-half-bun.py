import bpy,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-half-bun.blend'))
bpy.data.objects['Castell_Skin_Rig'].hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-half-bun-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
