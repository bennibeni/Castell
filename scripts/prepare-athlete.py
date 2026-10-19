"""Build an editable, unclothed Castell athlete. Originals are only read.
Run with Blender --background --factory-startup --disable-autoexec --python ...
"""
import bpy, math, os, json
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'blender')
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\torre\Downloads\Untitled.blend')
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
# Import original controls, hair and bun; no old body pieces or clothes.
with bpy.data.libraries.load(r'C:\Users\torre\Desktop\Untitled.blend', link=False) as (src,dst):
    dst.objects = [n for n in src.objects if n in ['Castell_Athlete'] + ['Castell_'+s[0] for s in specs] + ['Castell_Torso_hair','Castell_Torso_bun']]
for obj in dst.objects:
    if obj: bpy.context.collection.objects.link(obj)
root = bpy.data.objects['Castell_Athlete']
root['castellNoUniform'] = True
root['description'] = 'Unclothed body reference, weights and hair; Castell controls preserved.'
# Editable skin bones follow the original named controls with world transforms.
# All rest bones share axes: the export tool maps skinning to those controls.
arm_data = bpy.data.armatures.new('Castell_Skin_Rig')
arm = bpy.data.objects.new('Castell_Skin_Rig', arm_data)
bpy.context.collection.objects.link(arm)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for name,parent,_ in specs:
    b = arm_data.edit_bones.new('Skin_'+name)
    b.head = target[name]
    b.tail = b.head + Vector((0,.08,0))
    if parent: b.parent = arm_data.edit_bones['Skin_'+parent]
bpy.ops.object.mode_set(mode='OBJECT')
for name,_,_ in specs:
    c = arm.pose.bones['Skin_'+name].constraints.new('COPY_TRANSFORMS')
    c.target = bpy.data.objects['Castell_'+name]
    c.owner_space = 'WORLD'
    c.target_space = 'WORLD'
body.parent = root
arm.parent = root
modifier = body.modifiers.new('Castell skin weights','ARMATURE')
modifier.object = arm
arm.show_in_front = True
for p in body.data.polygons: p.use_smooth = True
# A simple exportable skin material (no external texture dependency).
skin = bpy.data.materials.get('Castell_Skin') or bpy.data.materials.new('Castell_Skin')
skin.use_nodes = True
skin.diffuse_color = (.48,.29,.19,1)
bsdf = skin.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = skin.diffuse_color
bsdf.inputs['Roughness'].default_value = .65
for i in range(len(body.data.materials)):
    body.data.materials[i] = skin
# Keep original hair; resize around the new head rather than retaining its old width.
for name in ['Castell_Torso_hair','Castell_Torso_bun']:
    obj = bpy.data.objects[name]
    if name.endswith('_hair'):
        obj.scale = (.76,.90,1.0)
        obj.location.z += .015
    else:
        obj.location.z += .015

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 650
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
cam_data = bpy.data.cameras.new('Preview camera')
cam = bpy.data.objects.new('Preview camera',cam_data)
scene.collection.objects.link(cam)
cam.location = (2,-4,1.7)
cam.rotation_euler = (Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 1.95
scene.camera = cam
arm.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_distance = 2.5
            area.spaces.active.region_3d.view_location = Vector((0,0,.85))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Castell-atleta.blend'))
scene.render.filepath = os.path.join(ROOT,'artifacts','athlete','rest.png')
bpy.ops.render.render(write_still=True)
# Export every required mesh and node, without camera/light/animations.
arm.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}: obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'athlete-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('CASTELL_BODY_READY',len(body.data.vertices),'vertices; normalized weights on every vertex')
