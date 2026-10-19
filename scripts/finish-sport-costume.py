import bpy,bmesh,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','hinako-swimsuit')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-Hinako-costume.blend'))
suit=bpy.data.objects['Castell_Sports_Overall'];body=bpy.data.objects['Castell_Body']
arms={g.index for g in suit.vertex_groups if 'Arm_' in g.name or 'Elbow_' in g.name}
bm=bmesh.new();bm.from_mesh(suit.data);deform=bm.verts.layers.deform.active
remove=[]
for face in bm.faces:
    score=sum(sum(v[deform].get(i,0) for i in arms) for v in face.verts)/len(face.verts)
    if score>.28:remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES')
boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
for _ in range(9):
    new={}
    for v in boundary:
        neighbors=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(neighbors)==2:new[v]=v.co*.5+(neighbors[0].co+neighbors[1].co)*.25
    for v,co in new.items():v.co=co
tree=BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
for v in boundary:
    hit,normal,idx,dist=tree.find_nearest(v.co)
    if hit is not None:v.co=hit+normal*.006
bm.to_mesh(suit.data);bm.free();suit.data.update()
mat=bpy.data.materials.new('Castell_Uniform_Modern');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.72
coords=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coords.outputs['Object'],sep.inputs[0])
def mathnode(op,a,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for i,v in enumerate([a,b]):
        if v is not None:
            if isinstance(v,(float,int)):n.inputs[i].default_value=v
            else:links.new(v,n.inputs[i])
    return n.outputs[0]
threshold=mathnode('ADD',mathnode('MULTIPLY',mathnode('SINE',mathnode('MULTIPLY',mathnode('SUBTRACT',sep.outputs['Z'],.9),7)),.024),.057)
dist=mathnode('SUBTRACT',mathnode('ABSOLUTE',sep.outputs['X']),threshold)
edge=nodes.new('ShaderNodeMapRange');edge.interpolation_type='SMOOTHERSTEP';edge.inputs['From Min'].default_value=-.002;edge.inputs['From Max'].default_value=.002;links.new(dist,edge.inputs['Value'])
factor=mathnode('MULTIPLY',edge.outputs[0],mathnode('GREATER_THAN',sep.outputs['Z'],.81))
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.014,.027,.052,1);mix.inputs[2].default_value=(.01,.27,.30,1);links.new(factor,mix.inputs[0]);links.new(mix.outputs[0],p.inputs['Base Color'])
suit.data.materials.clear();suit.data.materials.append(mat)
for poly in suit.data.polygons:poly.material_index=0;poly.use_smooth=True
image=bpy.data.images.new('Castell modern sportsuit color',width=2048,height=2048,alpha=False)
target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
uvname='CastellFaceAtlas';suit.data.uv_layers.active_index=suit.data.uv_layers.find(uvname);suit.data.uv_layers[uvname].active_render=True
bpy.ops.object.select_all(action='DESELECT');suit.select_set(True);bpy.context.view_layer.objects.active=suit
scene=bpy.context.scene;scene.cycles.samples=1;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=8
bpy.ops.object.bake(type='DIFFUSE');image.filepath_raw=os.path.join(OUT,'costume-color.png');image.file_format='PNG';image.save();image.pack()
u=nodes.new('ShaderNodeUVMap');u.uv_map=uvname;links.new(u.outputs[0],target.inputs['Vector']);links.new(target.outputs['Color'],p.inputs['Base Color'])
old=bpy.data.materials.get('Castell_Uniform')
if old:old.name='Castell_Previous_Uniform'
mat.name='Castell_Uniform'
scene.cycles.samples=24;scene.cycles.use_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-Hinako-costume.blend'))
scene.render.filepath=os.path.join(OUT,'figura-intera.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False);bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','athlete-hinako-swimsuit-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('MODERN_SPORT_COSTUME_READY',flush=True)
