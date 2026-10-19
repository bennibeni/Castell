"""Small symmetrical smile and relaxed lids; preserve topology and rig."""
import bpy, math, os, shutil
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','reference-soft-smile');os.makedirs(OUT,exist_ok=True)
SOURCE=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend')
BACKUP=SOURCE.replace('.blend','-prima-sorriso-delicato.blend')
if not os.path.exists(BACKUP):shutil.copy2(SOURCE,BACKUP)
glb=os.path.join(ROOT,'blender','athlete-reference-detail.glb')
backupglb=glb.replace('.glb','-prima-sorriso-delicato.glb')
if not os.path.exists(backupglb):shutil.copy2(glb,backupglb)
bpy.ops.wm.open_mainfile(filepath=BACKUP)
def g(v,c,w):return math.exp(-.5*((v-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def delta(co,accessory=False):
    x,y,z=co;a=abs(x)
    if z<1.44 or z>1.60 or y>-.025:return Vector((0,0,0))
    front=1-smooth(-.06,-.025,y)
    corner=g(a,.025,.008)*g(z,1.475,.008)
    # Less than 3mm at the commissures; the centre of the closed mouth stays still.
    dz=.0027*corner
    dx=(1 if x>=0 else -1)*.00045*corner
    dy=.00035*corner
    cheek=g(a,.048,.019)*g(z,1.518,.012)
    dz+=.0007*cheek;dy-=.0004*cheek
    # Relax the upper lid, with a slight cheek-driven lower-lid lift.
    eye=g(a,.036,.015)
    dz+=eye*(.00065*g(z,1.542,.0035)-.00085*g(z,1.558,.0035))
    # A softer brow line; no eye-size or skull-proportion changes.
    dz+=.0006*g(a,.022,.009)*g(z,1.575,.005)
    return Vector((dx*front,dy*front,dz*front))
for name in ['Castell_Body','Castell_Adapted_Lashes','Castell_Facial_Hair']:
    obj=bpy.data.objects.get(name)
    if not obj:continue
    for v in obj.data.vertices:v.co+=delta(v.co,name!='Castell_Body')
    obj.data.update()
body=bpy.data.objects['Castell_Body'];body['expression']='Relaxed eyelids and slight symmetric closed-mouth smile; original adult face and skin weights preserved.'
scene=bpy.context.scene;scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=850;scene.render.resolution_y=950
cam=scene.camera;cam.data.ortho_scale=.38;cam.location=(.20,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=SOURCE)
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-reference-soft-smile-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('SOFT_SMILE_READY',flush=True)
