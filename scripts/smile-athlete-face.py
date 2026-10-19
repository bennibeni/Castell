"""Local facial sculpt; leaves body topology, weights and joint controls intact."""
import bpy, math, os, shutil
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path=os.path.join(root,'blender','Castell-atleta.blend')
backup=os.path.join(root,'blender','Castell-atleta-before-smile.blend')
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
    # Youthful adult proportions: fuller upper cheeks and a softer jaw.
    cheek=g(a,.050,.024)*g(z,1.517,.024)
    dx=(1 if x>=0 else -1)*(.0015*cheek-.0025*g(a,.059,.023)*g(z,1.462,.022))
    dy=-.003*cheek
    dy-=.0025*g(a,.035,.020)*g(z,1.490,.018)
    dy+=.0015*g(a,.035,.025)*g(z,1.572,.014)
    dz=.0025*g(x,0,.035)*g(z,1.442,.012)
    # Closed-mouth smile, lifting both corners and the cheek pads smoothly.
    corner=g(a,.027,.011)*g(z,1.479,.012)
    dz+=.0075*corner
    dx+=(1 if x>=0 else -1)*.002*corner
    dy+=.0015*corner
    dz+=.003*g(a,.049,.022)*g(z,1.516,.020)
    # Subtle lower-lid lift to accompany the smile.
    dz+=.0013*g(a,.037,.022)*g(z,1.542,.007)
    v.co=Vector((x+dx*front,y+dy*front,z+dz*front))
    changed+=1
body.data.update()
body['face_revision']='Young adult East Asian facial study, soft closed-mouth smile.'
bpy.context.scene['face_previous_version']='Castell-atleta-before-smile.blend'
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


