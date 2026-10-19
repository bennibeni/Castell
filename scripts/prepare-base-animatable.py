"""Preserve the source anatomy and texture; prepare Castell controls and skinning."""
import bpy, os, math
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'blender')
PREVIEW=os.path.join(ROOT,'artifacts','base-animatable')
os.makedirs(PREVIEW,exist_ok=True)
# Explicit weighting steps keep definitions visible to static analysis.
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\torre\Downloads\assets\models\Untitled.blend')
body = bpy.data.objects['Female body reference']
for o in list(bpy.data.objects):
    if o != body:
        bpy.data.objects.remove(o, do_unlink=True)
body.name = 'Castell_Body'
# Keep anatomical topology, bring feet to the floor and height near the reference.
for v in body.data.vertices:
    v.co.z = (v.co.z - 0.022331154) * 0.974

specs = [
 ('Hips',None,(0,0,.9)), ('Thigh_L','Hips',(.09,0,-.02)),
 ('Thigh_R','Hips',(-.09,0,-.02)), ('Knee_L','Thigh_L',(0,0,-.43)),
 ('Knee_R','Thigh_R',(0,0,-.43)), ('Torso','Hips',(0,0,.02)),
 ('Arm_L','Torso',(.19,0,.47)), ('Arm_R','Torso',(-.19,0,.47)),
 ('Elbow_L','Arm_L',(0,0,-.29)), ('Elbow_R','Arm_R',(0,0,-.29)),
]
target = {}
for name,parent,loc in specs:
    target[name] = (target[parent] if parent else Vector()) + Vector(loc)
# Source landmarks in the asset's A pose. Facing -Y, Z up (Blender).
source = {'Hips':Vector((0,0,.9)), 'Torso':Vector((0,0,.92))}
for side,sign in [('L',1),('R',-1)]:
    source['Thigh_'+side] = Vector((sign*.105,0,.88))
    source['Knee_'+side] = Vector((sign*.125,-.012,.45))
    source['Arm_'+side] = Vector((sign*.17,0,1.37))
    source['Elbow_'+side] = Vector((sign*.315,-.04,1.10))

def direction(name):
    if name.startswith('Arm_'):
        return source[name.replace('Arm_','Elbow_')] - source[name]
    if name.startswith('Elbow_'):
        sign = 1 if name.endswith('_L') else -1
        return Vector((sign*.46,-.09,.82)) - source[name]
    if name.startswith('Thigh_'):
        return source[name.replace('Thigh_','Knee_')] - source[name]
    if name.startswith('Knee_'):
        sign = 1 if name.endswith('_L') else -1
        return Vector((sign*.14,0,.025)) - source[name]
    return Vector((0,0,.10 if name=='Hips' else .72))

# Bone heat weights on the original anatomical pose.
arm_data = bpy.data.armatures.new('Castell_Deformation')
arm = bpy.data.objects.new('Castell_Deformation', arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,parent,loc in specs:
    b = arm_data.edit_bones.new('Skin_'+name)
    b.head = source[name]
    b.tail = b.head + direction(name)
    if parent: b.parent = arm_data.edit_bones['Skin_'+parent]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
weights = []
index_names = {g.index:g.name.removeprefix('Skin_') for g in body.vertex_groups}
missing = []
for v in body.data.vertices:
    w = [(index_names[g.group],g.weight) for g in v.groups if g.weight>1e-7]
    if not w: missing.append(v.index)
    total = sum(value for _,value in w)
    weights.append([(name,value/total) for name,value in w] if total else [])
if missing: raise RuntimeError('Unweighted body vertices: '+str(len(missing)))
# Bake the A-pose into Castell's arms-down rest pose with the same skin weights.
transforms = {}
for name,_,_ in specs:
    d = direction(name)
    rotation = d.normalized().rotation_difference(Vector((0,0,-1))) if name not in ['Hips','Torso'] else Vector((0,0,1)).rotation_difference(Vector((0,0,1)))
    transforms[name] = Matrix.Translation(target[name]) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-source[name])
for v,w in zip(body.data.vertices,weights):
    co = v.co.copy()
    v.co = sum((transforms[name] @ co * value for name,value in w), Vector())
body.modifiers.clear()
body.parent = None
body.matrix_world = Matrix.Identity(4)
bpy.data.objects.remove(arm, do_unlink=True)

root=bpy.data.objects.new('Castell_Athlete',None)
bpy.context.collection.objects.link(root)
root['castellNoUniform']=True
root['description']='Original source face and UV texture; editable Castell animation controls.'
for name,parent,loc in specs:
    obj=bpy.data.objects.new('Castell_'+name,None)
    bpy.context.collection.objects.link(obj)
    obj.parent=bpy.data.objects['Castell_'+parent] if parent else root
    obj.location=loc
    obj.empty_display_type='SPHERE';obj.empty_display_size=.035
arm_data=bpy.data.armatures.new('Castell_Skin_Rig')
arm=bpy.data.objects.new('Castell_Skin_Rig',arm_data)
bpy.context.collection.objects.link(arm)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode='EDIT')
for name,parent,_ in specs:
    b=arm_data.edit_bones.new('Skin_'+name);b.head=target[name];b.tail=b.head+Vector((0,.08,0))
    if parent:b.parent=arm_data.edit_bones['Skin_'+parent]
bpy.ops.object.mode_set(mode='OBJECT')
for name,_,_ in specs:
    c=arm.pose.bones['Skin_'+name].constraints.new('COPY_TRANSFORMS')
    c.target=bpy.data.objects['Castell_'+name];c.owner_space='WORLD';c.target_space='WORLD'
body.parent=root;arm.parent=root
mod=body.modifiers.new('Castell skin weights','ARMATURE');mod.object=arm
arm.show_in_front=True
for p in body.data.polygons:p.use_smooth=True
# Preserve the packed skin atlas and eye vertex colors through glTF-supported nodes.
for mat in body.data.materials:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    if mat.name.startswith('Body'):
        mat.name='Castell_Skin'
        tex=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image)
        for socket in ['Base Color','Normal']:
            for link in list(bs.inputs[socket].links):links.remove(link)
        links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value=.53
        bs.inputs['IOR'].default_value=1.4
        bs.inputs['Subsurface Weight'].default_value=.035
        mat.diffuse_color=(.64,.43,.31,1)
    else:
        mat.name='Castell_Eyes'
        col=next((n for n in nodes if n.type=='VERTEX_COLOR'),None)
        if col:
            for link in list(bs.inputs['Base Color'].links):links.remove(link)
            links.new(col.outputs['Color'],bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value=.23
        bs.inputs['IOR'].default_value=1.46
body.data.uv_layers.active_index=body.data.uv_layers.find('UVMap')
body.data.uv_layers['UVMap'].active_render=True
bpy.ops.file.pack_all()
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.75,.78,.82,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
for name,pos,power in [('Key',(-2,-3,4),180),('Fill',(2,-2,2),90)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(light)
    light.location=pos;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=power;light.data.size=3
cam=bpy.data.objects.new('Preview',bpy.data.cameras.new('Preview'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO'
scene.view_settings.view_transform='AgX';scene.render.resolution_percentage=100
def render(name,center,scale,rx=600,ry=850):
    center=Vector(center);cam.location=center+Vector((.3,-4,.08));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=rx;scene.render.resolution_y=ry;scene.render.filepath=os.path.join(PREVIEW,name+'.png');bpy.ops.render.render(write_still=True)
arm.hide_set(True)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=2.4;area.spaces.active.region_3d.view_location=Vector((0,0,.85))
cam.location=(.3,-4,.93);cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.95
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Castell-atleta-base-animabile.blend'))
arm.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'athlete-base-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
arm.hide_set(True)
render('figura-intera',(0,0,.84),1.92)
render('viso-materiali',(0,0,1.53),.38,650,700)
# Representative joint test; controls are available for keyframing in the saved file.
bpy.data.objects['Castell_Arm_L'].rotation_euler.y=-1.25
bpy.data.objects['Castell_Elbow_L'].rotation_euler.x=.8
bpy.data.objects['Castell_Thigh_R'].rotation_euler.x=-.4
bpy.data.objects['Castell_Knee_R'].rotation_euler.x=.7
bpy.context.view_layer.update()
render('prova-articolazioni',(0,0,.84),1.95)
print('ANIMATABLE_BASE_READY',len(body.data.vertices))
