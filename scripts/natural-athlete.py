"""Natural gathered hair and subtle exportable skin detail on the reference candidate."""
import bpy, os, math, random, json, sys
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg={}
if '--' in sys.argv:
    with open(os.path.join(ROOT,sys.argv[sys.argv.index('--')+1])) as f:cfg=json.load(f)
OUT=os.path.join(ROOT,cfg.get('out_dir','artifacts/reference-face'))
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,cfg.get('source_blend','blender/Castell-atleta-reference-face.blend')))
random.seed(37)
torso=bpy.data.objects['Castell_Torso']
for name in ['Castell_Torso_hair','Castell_Torso_bun']:
    if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def parent_world(obj):
    bpy.context.view_layer.update()
    m=obj.matrix_world.copy()
    obj.parent=torso
    obj.matrix_world=m
def material(name,color,roughness):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Roughness'].default_value=roughness
    return m
hairmats=[material('Castell_Hair_Natural_'+str(i),c,.39+i*.025) for i,c in enumerate([
    (.012,.007,.005),(.020,.012,.008),(.030,.018,.012),(.042,.026,.017)])]
center=Vector((0,.008,1.568))
radii=Vector((.098,.110,.124))
def surface(d,offset: float = 0.0):
    return center+Vector((d.x*radii.x,d.y*radii.y,d.z*radii.z))+d*offset
def boundary(phi):
    front=max(0,-math.sin(phi))
    back=max(0,math.sin(phi))
    return 1.67-.76*front+.22*back
verts=[]; faces=[]
N=80; M=28
for j in range(M+1):
    for i in range(N):
        phi=2*math.pi*i/N
        theta=.015+(boundary(phi)-.015)*j/M
        d=Vector((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)))
        verts.append(surface(d))
for j in range(M):
    for i in range(N):
        a=j*N+i; b=j*N+(i+1)%N
        faces.append((a,b,b+N,a+N))
data=bpy.data.meshes.new('Natural scalp surface')
data.from_pydata(verts,[],faces);data.update()
cap=bpy.data.objects.new('Castell_Hair_Scalp',data)
bpy.context.collection.objects.link(cap)
data.materials.append(hairmats[0])
for p in data.polygons:p.use_smooth=True
parent_world(cap)

def tubes(name,paths,radius,sides=4):
    vertices=[];polygons=[];indices=[]
    for path_index,path in enumerate(paths):
        base=len(vertices)
        for j,point in enumerate(path):
            t=j/(len(path)-1)
            tangent=(path[min(j+1,len(path)-1)]-path[max(0,j-1)]).normalized()
            axis=tangent.cross(Vector((0,0,1)))
            if axis.length<.001:axis=tangent.cross(Vector((1,0,0)))
            axis.normalize();second=tangent.cross(axis).normalized()
            r=radius*(.32+.68*math.sin(math.pi*(.10+.8*t)))
            for k in range(sides):
                a=2*math.pi*k/sides
                vertices.append(point+r*(math.cos(a)*axis+math.sin(a)*second))
        for j in range(len(path)-1):
            for k in range(sides):
                a=base+j*sides+k;b=base+j*sides+(k+1)%sides
                polygons.append((a,b,b+sides,a+sides));indices.append(path_index%len(hairmats))
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],polygons);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    for m in hairmats:data.materials.append(m)
    for p,i in zip(data.polygons,indices):p.use_smooth=True;p.material_index=i
    parent_world(obj)
    return obj

# Swept fine locks sit on the cap, travelling from the hairline toward the tie.
paths=[]
end=Vector((0,.88,.475)).normalized()
lock_count=cfg.get('lock_count',490)
for i in range(lock_count):
    phi=2*math.pi*(i+random.random()*.6)/lock_count
    theta=boundary(phi)-random.uniform(.0,.045)
    start=Vector((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)))
    angle=start.angle(end)
    path=[]
    for j in range(19):
        t=j/18
        if angle>.001:
            d=(start*math.sin((1-t)*angle)+end*math.sin(t*angle))/math.sin(angle)
        else:d=start.copy()
        d.normalize()
        path.append(surface(d,.0009+random.uniform(0,.0004)))
    paths.append(path)
tubes('Castell_Hair_CombedLocks',paths,.00038)
# A compact, softly curved ponytail stays behind the neck during the simulation.
tail=[]
for i in range(95):
    phase=2*math.pi*i/95
    radial=math.sqrt(random.random())
    path=[]
    for j in range(22):
        t=j/21
        spread=.019*(1-t*.68)*radial
        x=math.cos(phase)*spread+.006*math.sin(t*4+phase)*t
        y=.109+.060*math.sin(t*math.pi*.72)+math.sin(phase)*spread
        z=1.624-.285*t
        path.append(Vector((x,y,z)))
    tail.append(path)
tubes('Castell_Hair_Ponytail',tail,.0025,5)
# Sparse flyaways at the hairline make the silhouette less mechanically perfect.
fly=[]
for i in range(45):
    phi=random.uniform(-math.pi,0)
    theta=boundary(phi)
    path=[]
    for j in range(9):
        t=j/8
        a=theta-.10*t
        d=Vector((math.sin(a)*math.cos(phi+.04*t),math.sin(a)*math.sin(phi+.04*t),math.cos(a)))
        path.append(surface(d,.001+.002*math.sin(t*math.pi)))
    fly.append(path)
tubes('Castell_Hair_Flyaways',fly,.00019,3)

if cfg.get('merge_hair',False):
    hairs=[o for o in bpy.data.objects if o.name.startswith('Castell_Hair_') and o.type=='MESH']
    for obj in hairs:
        tint=obj.data.color_attributes.new(name='HairTint',type='FLOAT_COLOR',domain='CORNER')
        for p in obj.data.polygons:
            color=obj.data.materials[p.material_index].diffuse_color
            for li in p.loop_indices:tint.data[li].color=color
    bpy.ops.object.select_all(action='DESELECT')
    for obj in hairs:obj.select_set(True)
    bpy.context.view_layer.objects.active=hairs[0]
    bpy.ops.object.join()
    hair=bpy.context.object
    hair.name='Castell_Hair_Natural'
    mat=material('Castell_Hair_Combined',(.020,.012,.008),.45)
    attr=mat.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='HairTint'
    mat.node_tree.links.new(attr.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    hair.data.materials.clear();hair.data.materials.append(mat)
    for p in hair.data.polygons:p.material_index=0

body=bpy.data.objects['Castell_Body']
body.data.uv_layers.active_index=body.data.uv_layers.find('CastellAtlas')
body.data.uv_layers['CastellAtlas'].active_render=True
# A shallow navel indentation and softer surrounding abdominal transition.
for v in body.data.vertices:
    x,y,z=v.co
    if y<-.04 and abs(x)<.03 and abs(z-1.04)<.035:
        v.co.y+=.0035*math.exp(-.5*(x/.007)**2-.5*((z-1.04)/.009)**2)
body.data.update()
if cfg.get('eyelash_length',0)>0:
    # Fine upper lashes follow the neutral head surface and its torso controller.
    lash_paths=[]
    bpy.context.view_layer.update()
    for side in [-1,1]:
        for i in range(25):
            t=-.96+1.92*i/24
            x=side*(.036+t*.018)
            z=1.5585+.007*math.sqrt(max(0,1-t*t))
            hit,point,normal,face_index=body.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
            if not hit:continue
            root_point=point+Vector((0,-.00025,0))
            length=cfg['eyelash_length']*(.75+.25*(1-abs(t)))
            path=[]
            for j in range(8):
                u=j/7
                path.append(root_point+Vector((side*.0015*t*u,-length*u,length*.6*u*u)))
            lash_paths.append(path)
    lashes=tubes('Castell_Eyelashes',lash_paths,.00011,3)
    lashes.data.materials.clear()
    lashes.data.materials.append(material('Castell_Eyelash_Dark',(.009,.005,.003),.50))
    for p in lashes.data.polygons:p.material_index=0
skin=body.data.materials[0]
nodes=skin.node_tree.nodes;links=skin.node_tree.links
bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value=.57
bsdf.inputs['Subsurface Weight'].default_value=.025
bsdf.inputs['Subsurface Radius'].default_value=(1,.48,.30)
noise=nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value=1800
noise.inputs['Detail'].default_value=2
coordinate=nodes.new('ShaderNodeTexCoord')
links.new(coordinate.outputs['Object'],noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=.22
bump.inputs['Distance'].default_value=.00022
if cfg.get('face_pore_factor',1)<1:
    pore_strength=body.data.color_attributes.new(name='SkinPoreStrength',type='FLOAT_COLOR',domain='CORNER')
    for loop in body.data.loops:
        z=body.data.vertices[loop.vertex_index].co.z
        t=max(0,min(1,(z-1.40)/.055));t=t*t*(3-2*t)
        strength=.22*(1-t*(1-cfg['face_pore_factor']))
        pore_strength.data[loop.index].color=(strength,strength,strength,1)
    pore_node=nodes.new('ShaderNodeVertexColor');pore_node.layer_name='SkinPoreStrength'
    links.new(pore_node.outputs['Color'],bump.inputs['Strength'])
links.new(noise.outputs['Fac'],bump.inputs['Height'])
links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
# Bake pores as a tangent-space normal map, so they survive GLB export.
normal=bpy.data.images.new('Castell skin micro normal',width=2048,height=2048,alpha=False)
normal.colorspace_settings.name='Non-Color'
target=nodes.new('ShaderNodeTexImage');target.image=normal;nodes.active=target
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
bpy.context.view_layer.objects.active=body
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.margin=8
modifier=body.modifiers.get('Castell skin weights');modifier.show_render=False
bpy.ops.object.bake(type='NORMAL')
modifier.show_render=True
normal.filepath_raw=os.path.join(ROOT,cfg.get('normal_image','public/models/athlete-skin-normal.png'))
normal.file_format='PNG';normal.save();normal.pack()
normalmap=nodes.new('ShaderNodeNormalMap');normalmap.uv_map='CastellAtlas'
normalmap.inputs['Strength'].default_value=.65
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='CastellAtlas'
links.new(uv.outputs['UV'],target.inputs['Vector'])
links.new(target.outputs['Color'],normalmap.inputs['Color'])
links.new(normalmap.outputs['Normal'],bsdf.inputs['Normal'])
# Warm joint coloration and very small skin tone variation, baked into base color.
tone=body.data.color_attributes.new(name='NaturalSkinTone',type='FLOAT_COLOR',domain='CORNER')
for loop in body.data.loops:
    x,y,z=body.data.vertices[loop.vertex_index].co
    if z<1.40:
        joint=math.exp(-.5*((z-.45)/.045)**2)+math.exp(-.5*((z-1.10)/.035)**2)*min(abs(x)/.17,1)
        variation=.012*math.sin(x*131+z*72)*math.sin(z*109-y*143)
        c=(1+variation,1+variation-.035*joint,1+variation-.050*joint)
    else:c=(1,1,1)
    tone.data[loop.index].color=(*c,1)
attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='NaturalSkinTone'
old_color=bsdf.inputs['Base Color'].links[0].from_socket
multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
links.new(old_color,multiply.inputs[1]);links.new(attr.outputs['Color'],multiply.inputs[2])
links.new(multiply.outputs[0],bsdf.inputs['Base Color'])
color_atlas=bpy.data.images.new('Castell detailed skin atlas',width=2048,height=2048,alpha=False)
color_target=nodes.new('ShaderNodeTexImage');color_target.image=color_atlas;nodes.active=color_target
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
modifier.show_render=False
bpy.ops.object.bake(type='DIFFUSE')
modifier.show_render=True
color_atlas.filepath_raw=os.path.join(ROOT,cfg.get('skin_image','public/models/athlete-natural-skin.png'))
color_atlas.file_format='PNG';color_atlas.save();color_atlas.pack()
links.new(uv.outputs['UV'],color_target.inputs['Vector'])
links.new(color_target.outputs['Color'],bsdf.inputs['Base Color'])
body['surface_detail']='Baked pores, subtle warm joint tones, shallow navel, skin roughness and subsurface scattering; original anatomical hands, feet and body topology retained.'

if cfg.get('adult_anatomy',False):
    # Small neutral anatomical landmarks on the entirely fictional adult character.
    areola=material('Castell_Anatomy',(.46,.25,.21),.63)
    for sign in [-1,1]:
        vertices=[v for v in body.data.vertices if .045<sign*v.co.x<.12 and 1.17<v.co.z<1.31]
        tip=min(vertices,key=lambda v:v.co.y)
        center_point=tip.co.copy()
        outward=tip.normal.normalized()
        if outward.y>0:outward=-outward
        orient=Vector((0,0,1)).rotation_difference(outward)
        for label,scale,offset in [('Areola',(.011,.009,.0007),.0001),('Nipple',(.0023,.0023,.0017),.0018)]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=center_point+outward*offset)
            obj=bpy.context.object;obj.name='Castell_'+label+('_L' if sign>0 else '_R')
            obj.rotation_mode='QUATERNION';obj.rotation_quaternion=orient
            obj.scale=scale
            obj.data.materials.append(areola)
            for p in obj.data.polygons:p.use_smooth=True
            parent_world(obj)
    body['identity']=cfg.get('identity','Entirely fictional adult athlete, age 28-32; newly generated face with no photographic identity reference.')

# Studio lighting and full-length framing; no geometry is cropped.
scene.cycles.samples=cfg.get('render_samples',32)
scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=1300
scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.6
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.5
for name in ['Face key','Face fill']:
    light=bpy.data.objects.get(name)
    if light:
        light.data.energy=140 if name=='Face key' else 90
        light.data.size=3
camera=scene.camera
camera.data.ortho_scale=1.92
camera.location=(1.1,-3.8,1.15)
camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,cfg.get('output_blend','blender/Castell-atleta-natural.blend')))
scene.render.filepath=os.path.join(OUT,'full-body-natural.png')
bpy.ops.render.render(write_still=True)
# Also save a head detail, using the same actual materials and geometry.
camera.data.ortho_scale=.40
camera.location=(.6,-3,1.56)
camera.rotation_euler=(Vector((0,0,1.56))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=900
scene.render.filepath=os.path.join(OUT,'head-natural.png')
bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','EMPTY','ARMATURE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,cfg.get('output_raw','blender/natural-raw.glb')),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
