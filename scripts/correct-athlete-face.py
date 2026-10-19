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
    if z<1.38 or z>1.66: continue
    a=abs(x)
    front=g(y,-.105,.055)
    # Shorten the whole lower head with a smooth transition into the neck.
    t=max(0,min(1,(z-1.38)/.065))
    blend=t*t*(3-2*t)
    dz=(1.635-z)*.16*blend if z<1.635 else 0
    dx=x*.045*g(z,1.51,.075)*blend
    dy=0
    if y<-.025:
        cheek=g(a,.050,.024)*g(z,1.517,.024)
        dy-=.0025*cheek*front
        # One continuous curve across the mouth, rather than two local dents.
        # Move the entire lip thickness together to preserve its natural contour.
        lateral=g(a,0,.042)
        mouth=g(z,1.479,.020)
        curve=min((a/.030)**2,1.5)
        dz+=.0090*curve*lateral*mouth*front
        dx+=(1 if x>=0 else -1)*.0015*min(a/.030,1)*lateral*mouth*front
        dz+=.0030*cheek*front
    v.co=Vector((x+dx,y+dy,z+dz))
    changed+=1
body.data.update()
skin=bpy.data.materials['Castell_Skin']
skin.diffuse_color=(.82,.62,.46,1)
skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=skin.diffuse_color
body['face_revision']='Shorter, rounder adult face; gentle continuous smile; light warm beige skin.'
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



