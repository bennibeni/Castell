"""Local facial sculpt; leaves body topology, weights and joint controls intact."""
import bpy, math, os, shutil
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path=os.path.join(root,'blender','Castell-atleta.blend')
backup=os.path.join(root,'blender','Castell-atleta-before-face.blend')
if not os.path.exists(backup): shutil.copy2(path,backup)
bpy.ops.wm.open_mainfile(filepath=backup)
body=bpy.data.objects['Castell_Body']
def g(value,center,width): return math.exp(-.5*((value-center)/width)**2)
changed=0
for v in body.data.vertices:
    x,y,z=v.co
    if z<1.405 or z>1.635 or y>-.025: continue
    a=abs(x)
    front=g(y,-.105,.055)
    # Softly flatten the bridge and brow; retain the existing nose topology.
    dy=.006*g(x,0,.020)*g(z,1.54,.027)
    dy+=.002*g(x,0,.024)*g(z,1.508,.018)
    dy+=.0035*g(a,.036,.023)*g(z,1.574,.010)
    # Fuller lateral midface and softer lower jaw contour.
    cheek=g(a,.056,.022)*g(z,1.516,.023)
    dx=(1 if x>=0 else -1)*(.0038*cheek-.003*g(a,.059,.022)*g(z,1.464,.018))
    dy-=.0045*cheek
    # Subtle almond-shaped aperture, with a small lift of the outer corners.
    eye=g(a,.036,.021)*g(z,1.551,.012)
    dz=-(z-1.551)*.22*eye
    dz+=.0022*g(a,.054,.011)*g(z,1.551,.009)
    dy-=.002*g(a,.022,.009)*g(z,1.552,.009)
    v.co=Vector((x+dx*front,y+dy*front,z+dz*front))
    changed+=1
body.data.update()
body['face_revision']='Soft East Asian facial study: localized eyelid, bridge, cheek and jaw edits.'
bpy.context.scene['face_previous_version']='Castell-atleta-before-face.blend'
bpy.ops.wm.save_as_mainfile(filepath=path)
scene=bpy.context.scene
camera=scene.camera
scene.render.resolution_x=700
scene.render.resolution_y=800
camera.data.ortho_scale=.38
for name,pos in [('front',(0,-3,1.55)),('three-quarter',(.9,-3,1.55))]:
    camera.location=pos
    camera.rotation_euler=(Vector((0,0,1.55))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=os.path.join(root,'artifacts','athlete','face-'+name+'.png')
    bpy.ops.render.render(write_still=True)
arm=bpy.data.objects['Castell_Skin_Rig']
arm.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}: obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'blender','athlete-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('FACE_REFINED',changed,'vertices; topology, weights and controls preserved')

