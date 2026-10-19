"""Build a separate photo-reference face candidate, retaining the approved rig.
Texture and 2D landmarks are supplied in blender/reference-face-settings.json.
Does not replace the active athlete.
"""
import bpy, os, json, math, sys
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
settings=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'blender/reference-face-settings.json'
with open(os.path.join(ROOT,settings)) as f: cfg=json.load(f)
OUT=os.path.join(ROOT,cfg.get('out_dir','artifacts/reference-face'))
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-before-face.blend'))
body=bpy.data.objects['Castell_Body']
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)
def g(x,c,w): return math.exp(-.5*((x-c)/w)**2)
# Start from the unwarped anatomical mesh, not from previous smile edits.
for v in body.data.vertices:
    x,y,z=v.co
    if z<1.38 or z>1.66: continue
    t=smooth(1.38,1.445,z)
    dz=(1.635-z)*.09*t if z<1.635 else 0
    dx=x*.015*g(z,1.51,.075)*t
    dy=0
    if y<-.025:
        front=g(y,-.105,.055)
        # Preserve a relaxed mouth matching the photo, reduce bridge projection.
        dy=(.004*g(x,0,.019)*g(z,1.54,.029)-.001*g(abs(x),.052,.024)*g(z,1.515,.025))*front
    v.co=Vector((x+dx,y+dy,z+dz))
body.data.update()
image=bpy.data.images.load(os.path.join(ROOT,cfg['texture']),check_existing=True)
image.pack()
skin=bpy.data.materials['Castell_Skin']
skin.use_nodes=True
skin.diffuse_color=tuple(cfg['skin_linear'])+(1,)
nodes=skin.node_tree.nodes
links=skin.node_tree.links
bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=skin.diffuse_color
bsdf.inputs['Roughness'].default_value=.65
face=bpy.data.materials.new('Castell_Face_Reference')
face.use_nodes=True
face.diffuse_color=skin.diffuse_color
nodes=face.node_tree.nodes
links=face.node_tree.links
bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value=.68
texture=nodes.new('ShaderNodeTexImage')
texture.image=image
texture.extension='EXTEND'
uv_node=nodes.new('ShaderNodeUVMap')
uv_node.uv_map='FaceReferenceUV'
links.new(uv_node.outputs['UV'],texture.inputs['Vector'])
attribute=nodes.new('ShaderNodeVertexColor')
attribute.layer_name='FaceReferenceBlend'
mix=nodes.new('ShaderNodeMixRGB')
mix.blend_type='MIX'
mix.inputs[1].default_value=skin.diffuse_color
links.new(attribute.outputs['Color'],mix.inputs[0])
links.new(texture.outputs['Color'],mix.inputs[2])
links.new(mix.outputs[0],bsdf.inputs['Base Color'])
# Bake blending into a base-color image for glTF (which cannot export MixRGB).
# The UV texture itself will be baked by Blender, without lights or image edits.
body.data.materials.append(face)
face_index=len(body.data.materials)-1
uv=body.data.uv_layers.new(name='FaceReferenceUV')
mask=body.data.color_attributes.new(name='FaceReferenceBlend',type='FLOAT_COLOR',domain='CORNER')
rows=cfg['rows']
def pixel_y(z):
    for (za,pa),(zb,pb) in zip(rows,rows[1:]):
        if za<=z<=zb: return pa+(pb-pa)*(z-za)/(zb-za)
    return rows[0][1] if z<rows[0][0] else rows[-1][1]
def face_width(z):
    widths=[(1.425,.010),(1.459,.030),(1.48,.050),(1.50,.064),(1.525,.075),(1.56,.080),(1.59,.073),(1.625,.060),(1.65,.05)]
    for (za,wa),(zb,wb) in zip(widths,widths[1:]):
        if za<=z<=zb:return wa+(wb-wa)*(z-za)/(zb-za)
    return .01
for p in body.data.polygons:
    zs=[body.data.vertices[i].co.z for i in p.vertices]
    if max(zs)>1.42 and min(zs)<1.65:
        p.material_index=face_index
    for li in p.loop_indices:
        v=body.data.vertices[body.data.loops[li].vertex_index]
        x,y,z=v.co
        px=cfg['center_x']+x*cfg['pixels_per_meter']
        uv.data[li].uv=(px/image.size[0],1-pixel_y(z)/image.size[1])
        top_fade=cfg.get('texture_top_fade',[1.615,1.64])
        amount=smooth(1.425,1.455,z)*(1-smooth(top_fade[0],top_fade[1],z))
        limit=face_width(z)-cfg.get('texture_edge_inset',0)
        amount*=1-smooth(limit-cfg.get('texture_edge_blend',.012),limit,abs(x))
        amount*=1-smooth(-.060,-.022,y)
        if cfg.get('soften_nostril_texture',False):
            amount*=1-.88*g(abs(x),.014,.009)*g(z,1.515,.007)
        # Keep the visible face crisp; taper toward the ears and rear scalp.
        mask.data[li].color=(amount,amount,amount,1)

# Bake the face diffuse color into a conventional UV atlas, exportable to GLB.
# This is Blender material baking, not a painted approximation in the preview.
atlas_uv=body.data.uv_layers.new(name='CastellAtlas')
body.data.uv_layers.active_index=body.data.uv_layers.find('CastellAtlas')
body.data.uv_layers['CastellAtlas'].active_render=True
bpy.context.view_layer.objects.active=body
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.008)
bpy.ops.object.mode_set(mode='OBJECT')
atlas=bpy.data.images.new('Castell face and skin atlas',width=2048,height=2048,alpha=False)
for mat in set(body.data.materials):
    node=mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image=atlas
    mat.node_tree.nodes.active=node
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=1
scene.render.bake.use_pass_direct=False
scene.render.bake.use_pass_indirect=False
scene.render.bake.use_pass_color=True
scene.render.bake.margin=8
# Disable armature only while baking to work on the neutral anatomical surface.
modifier=body.modifiers.get('Castell skin weights')
modifier.show_render=False
bpy.ops.object.bake(type='DIFFUSE')
modifier.show_render=True
atlas.filepath_raw=os.path.join(ROOT,cfg.get('atlas','public/models/athlete-face-atlas.png'))
atlas.file_format='PNG'
atlas.save()
atlas.pack()
final=bpy.data.materials.new(cfg.get('material','Castell_Skin_Reference'))
final.use_nodes=True
final.diffuse_color=skin.diffuse_color
nodes=final.node_tree.nodes
bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value=.65
tex=nodes.new('ShaderNodeTexImage')
tex.image=atlas
uvnode=nodes.new('ShaderNodeUVMap')
uvnode.uv_map='CastellAtlas'
final.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector'])
final.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
body.data.materials.clear()
body.data.materials.append(final)
for p in body.data.polygons:p.material_index=0
body.data.uv_layers.active_index=body.data.uv_layers.find('CastellAtlas')
body.data.uv_layers['CastellAtlas'].active_render=True
body['face_revision']=cfg.get('revision','Reference-based face texture and anatomy; candidate for review.')
scene.render.engine='CYCLES'
scene.cycles.samples=cfg.get('render_samples',16)
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.8,.8,.8,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
for name,position,power,size in [('Face key',(-2,-3,4),85,4),('Face fill',(2,-2,2),45,3)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'))
    scene.collection.objects.link(light)
    light.location=position
    light.rotation_euler=(Vector((0,0,1.5))-light.location).to_track_quat('-Z','Y').to_euler()
    light.data.energy=power
    light.data.shape='DISK'
    light.data.size=size
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=-.25
scene.render.resolution_x=700
scene.render.resolution_y=800
scene.render.resolution_percentage=100
cam=scene.camera
cam.data.ortho_scale=.38
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
cam.location=(0,-3,1.55)
cam.rotation_euler=(Vector((0,0,1.55))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,cfg.get('output_blend','blender/Castell-atleta-reference-face.blend')))
for name,pos in [('front',(0,-3,1.55)),('three-quarter',(.9,-3,1.55))]:
    cam.location=pos
    cam.rotation_euler=(Vector((0,0,1.55))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=os.path.join(OUT,'face-'+name+'.png')
    bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,cfg.get('output_raw','blender/reference-face-raw.glb')),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
