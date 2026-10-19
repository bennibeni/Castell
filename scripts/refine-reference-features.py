"""Refine the adult original face with localized, exportable surface accents."""
import bpy, os, shutil, math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','reference-face-finish');os.makedirs(OUT,exist_ok=True)
SOURCE=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend')
BACKUP=SOURCE.replace('.blend','-prima-rifinitura.blend')
if not os.path.exists(BACKUP):shutil.copy2(SOURCE,BACKUP)
glb=os.path.join(ROOT,'blender','athlete-reference-detail.glb')
if not os.path.exists(glb.replace('.glb','-prima-rifinitura.glb')):shutil.copy2(glb,glb.replace('.glb','-prima-rifinitura.glb'))
bpy.ops.wm.open_mainfile(filepath=BACKUP)
body=bpy.data.objects['Castell_Body'];mesh=body.data
original=[tuple(v.co) for v in mesh.vertices]
def g(x,c,w):return math.exp(-.5*((x-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
attr=mesh.color_attributes.new(name='FaceFinish',type='FLOAT_COLOR',domain='CORNER')
for loop in mesh.loops:
    x,y,z=mesh.vertices[loop.vertex_index].co;a=abs(x)
    front=1-smooth(-.060,-.025,y)
    color=Vector((.66,.47,.37));weight=0
    # Small accents aligned to the ORIGINAL adult vermilion and eyelid landmarks.
    lipshape=(1-smooth(.020,.028,a))*front
    upper=g(z,1.478+.0015*g(a,.009,.005),.0018)*lipshape
    lower=g(z,1.472,.0024)*lipshape
    lip=min(1,upper+lower)
    if lip>.01:color=Vector((.43,.18,.17));weight=.46*lip
    seam=g(z,1.475,.00065)*lipshape
    if seam>.1:color=color.lerp(Vector((.23,.095,.085)),seam*.45);weight=max(weight,.40*seam)
    eyelid=.25*g(a,.036,.016)*g(z,1.5605,.0027)*front
    if eyelid>weight:color=Vector((.40,.28,.24));weight=eyelid
    under=.11*g(a,.037,.015)*g(z,1.542,.0025)*front
    if under>weight:color=Vector((.56,.36,.30));weight=under
    cheek=.16*g(a,.052,.020)*g(z,1.513,.015)*front
    if cheek>weight:color=Vector((.70,.39,.32));weight=cheek
    attr.data[loop.index].color=(*color,weight)
skin=bpy.data.materials['Castell_Skin'];nodes=skin.node_tree.nodes;links=skin.node_tree.links
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
base=bs.inputs['Base Color'].links[0].from_socket
vc=nodes.new('ShaderNodeVertexColor');vc.layer_name=attr.name
mix=nodes.new('ShaderNodeMixRGB');links.new(vc.outputs['Alpha'],mix.inputs[0]);links.new(base,mix.inputs[1]);links.new(vc.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.48
bs.inputs['Subsurface Weight'].default_value=.07
bs.inputs['Subsurface Scale'].default_value=.0012
# Bake the localized changes into a conventional color atlas for glTF.
atlas=bpy.data.images.new('Castell refined adult face colors',width=4096,height=4096,alpha=False)
restore=[]
for mat in mesh.materials:
    if not mat or not mat.use_nodes:continue
    ns=mat.node_tree.nodes;ls=mat.node_tree.links
    p=next((n for n in ns if n.type=='BSDF_PRINCIPLED'),None)
    out=next((n for n in ns if n.type=='OUTPUT_MATERIAL'),None)
    if not p or not out:continue
    emission=ns.new('ShaderNodeEmission')
    if p.inputs['Base Color'].is_linked:ls.new(p.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
    else:emission.inputs['Color'].default_value=p.inputs['Base Color'].default_value
    ls.new(emission.outputs[0],out.inputs['Surface'])
    target=ns.new('ShaderNodeTexImage');target.image=atlas;ns.active=target
    restore.append((mat,p,out,emission,target))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
scene=bpy.context.scene;scene.cycles.samples=1
rigmod=next((m for m in body.modifiers if m.type=='ARMATURE'),None)
if rigmod:rigmod.show_render=False
bpy.ops.object.bake(type='EMIT')
if rigmod:rigmod.show_render=True
atlas.filepath_raw=os.path.join(OUT,'face-color.png');atlas.file_format='PNG';atlas.save();atlas.pack()
for mat,p,out,emission,target in restore:
    ns=mat.node_tree.nodes;ls=mat.node_tree.links
    ls.new(p.outputs['BSDF'],out.inputs['Surface']);ns.remove(emission)
    uv=ns.new('ShaderNodeUVMap');uv.uv_map=mesh.uv_layers.active.name;ls.new(uv.outputs[0],target.inputs['Vector']);ls.new(target.outputs['Color'],p.inputs['Base Color'])
brows=bpy.data.materials.get('Castell_Brows_Lashes')
if brows:
    p=next(n for n in brows.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.018,.011,.008,1);p.inputs['Roughness'].default_value=.5
assert original==[tuple(v.co) for v in mesh.vertices]
body['face_finish']='Localized lip contour, warm cheek tint and eyelid shading on the original adult face; original geometry preserved.'
scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=850;scene.render.resolution_y=950
cam=scene.camera;cam.data.ortho_scale=.38;cam.location=(.20,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=SOURCE)
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-reference-face-finish-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('FACE_FINISH_READY',flush=True)
