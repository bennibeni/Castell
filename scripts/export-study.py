"""Export a saved Castell study without re-running its material bake or render."""
import bpy,os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args=sys.argv[sys.argv.index('--')+1:]
source,output=args
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,source))
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'} and not o.get('renderOnly'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,output),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
