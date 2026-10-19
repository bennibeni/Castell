"""Revision 3: actual facial sculpt, loose parted hair, integrated adult anatomy."""
import bpy, bmesh, os, math, random
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','asia-r3')
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia.blend'))
random.seed(137)
body=bpy.data.objects['Castell_Body'];torso=bpy.data.objects['Castell_Torso']
for obj in list(bpy.data.objects):
    if obj.type=='MESH' and (obj.name.startswith('Castell_Hair') or obj.name.startswith('Castell_Areola') or obj.name.startswith('Castell_Nipple')):
        bpy.data.objects.remove(obj,do_unlink=True)

def gauss(x,c,w):return math.exp(-.5*((x-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
# Shape the actual eye surrounds, lower face and nose, retaining all weights.
for v in body.data.vertices:
    x,y,z=v.co
    if z<1.41 or z>1.65:continue
    front=1-smooth(-.06,.0,y)
    sign=1 if x>=0 else -1
    eye=gauss(abs(x),.036,.022)*gauss(z,1.559,.016)*front
    v.co.x+=(x-sign*.036)*.13*eye
    v.co.z+=(z-1.559)*.10*eye
    nose=gauss(x,0,.024)*gauss(z,1.527,.025)*front
    v.co.x-=x*.10*nose
    v.co.y+=.003*nose
    jaw=gauss(z,1.467,.025)
    v.co.x-=x*.065*jaw
    v.co.z-=.0035*jaw*front
body.data.update()

# Subdivide only breast surfaces; interpolated UVs and deform groups are retained.
bm=bmesh.new();bm.from_mesh(body.data)
def chest(p):return p.y<-.025 and 1.185<p.z<1.295 and .025<abs(p.x)<.135
edges=[e for e in bm.edges if all(chest(v.co) for v in e.verts)]
if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=5,use_grid_fill=True)
bm.to_mesh(body.data);bm.free();body.data.update()
# Match landmarks to the actual surface at a lower, anatomically coherent height.
centers=[]
bpy.context.view_layer.update()
for sign in [-1,1]:
    hit,p,n,face=body.ray_cast(Vector((sign*.075,-.8,1.237)),Vector((0,1,0)))
    if not hit:raise RuntimeError('Anatomical surface not found')
    centers.append(p)
for v in body.data.vertices:
    if v.co.y>-.03:continue
    for c in centers:
        d=math.sqrt(((v.co.x-c.x)/.95)**2+((v.co.z-c.z)/.83)**2)
        if d<.023 and abs(v.co.y-c.y)<.035:
            amount=.00035*math.exp(-.5*(d/.010)**2)+.0015*math.exp(-.5*(d/.0026)**2)
            v.co+=v.normal*amount
body.data.update()
color=body.data.color_attributes.new(name='IntegratedAnatomyTint',type='FLOAT_COLOR',domain='CORNER')
for loop in body.data.loops:
    p=body.data.vertices[loop.vertex_index].co
    amount=0
    if p.y<-.03:
        for c in centers:
            d=math.sqrt(((p.x-c.x)/.0105)**2+((p.z-c.z)/.0090)**2)
            if abs(p.y-c.y)<.035:amount=max(amount,1-smooth(.55,1.18,d))
    color.data[loop.index].color=(1-.15*amount,1-.30*amount,1-.29*amount,1)
# Bake the integrated coloration to the existing UVs, without a pasted-on disc.
skin=body.data.materials[0];nodes=skin.node_tree.nodes;links=skin.node_tree.links
bsdf=nodes.get('Principled BSDF');source=bsdf.inputs['Base Color'].links[0].from_socket
attr=nodes.new('ShaderNodeVertexColor');attr.layer_name=color.name
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
links.new(source,mix.inputs[1]);links.new(attr.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
atlas=bpy.data.images.new('Asia R3 integrated skin',width=2048,height=2048,alpha=False)
tex=nodes.new('ShaderNodeTexImage');tex.image=atlas;nodes.active=tex
body.data.uv_layers.active_index=body.data.uv_layers.find('CastellAtlas')
body.data.uv_layers['CastellAtlas'].active_render=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
scene.render.bake.margin=8
arm=body.modifiers.get('Castell skin weights');arm.show_render=False
bpy.ops.object.bake(type='DIFFUSE');arm.show_render=True
atlas.filepath_raw=os.path.join(ROOT,'public','models','asia-r3-skin.png');atlas.file_format='PNG';atlas.save();atlas.pack()
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='CastellAtlas';links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])

def mat(name,color,roughness):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=roughness
    return m
palette=[(.014,.009,.007),(.026,.016,.011),(.038,.023,.015),(.052,.032,.021),(.069,.043,.027)]
vertices=[];polys=[];colors=[]
def add_tube(path,width,depth,shade,sides=6):
    base=len(vertices)
    for i,p in enumerate(path):
        t=i/(len(path)-1)
        tangent=(path[min(i+1,len(path)-1)]-path[max(0,i-1)]).normalized()
        axis=tangent.cross(Vector((0,1,0)))
        if axis.length<.01:axis=tangent.cross(Vector((1,0,0)))
        axis.normalize();other=tangent.cross(axis).normalized()
        taper=(.18+.82*math.sin(math.pi*(.05+.90*t)))*(1-.7*t**5)
        for k in range(sides):
            a=k*2*math.pi/sides
            vertices.append(p+taper*(axis*width*math.cos(a)+other*depth*math.sin(a)))
    for i in range(len(path)-1):
        for k in range(sides):
            a=base+i*sides+k;b=base+i*sides+(k+1)%sides
            polys.append((a,b,b+sides,a+sides));colors.append(palette[shade])
def spline(points,steps=5):
    result=[];pts=[points[0]]+points+[points[-1]]
    for k in range(1,len(pts)-2):
        p0,p1,p2,p3=pts[k-1:k+3]
        for j in range(steps):
            t=j/steps
            result.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return result+[points[-1]]
# Scalp underlay with an irregular V-shaped hairline instead of a circular rim.
N=72;M=22;base=len(vertices)
for j in range(M+1):
    for i in range(N):
        phi=2*math.pi*i/N;front=max(0,-math.sin(phi))
        limit=1.78-.88*front+.07*math.cos(phi)*front+.018*math.sin(13*phi)
        th=.008+(limit-.008)*j/M
        vertices.append(Vector((.094*math.sin(th)*math.cos(phi),.008+.110*math.sin(th)*math.sin(phi),1.565+.130*math.cos(th))))
for j in range(M):
    for i in range(N):
        a=base+j*N+i;b=base+j*N+(i+1)%N
        polys.append((a,b,b+N,a+N));colors.append(palette[0])
# Loose layered hair, swept out from an off-centre part and down past shoulders.
for side in [-1,1]:
    for i in range(85):
        u=i/84;back=random.uniform(-.02,.095);spread=random.uniform(-.008,.008)
        root=Vector((-.012+random.uniform(-.004,.004),back*.65,1.694-random.uniform(0,.004)))
        pts=[root,
            Vector((side*.057,back-.008,1.688+random.uniform(0,.010))),
            Vector((side*(.096+u*.006),back-.015,1.615)),
            Vector((side*(.106+u*.010),back-.010,1.49)),
            Vector((side*(.118+u*.018)+spread,back-.014,1.36)),
            Vector((side*(.135+u*.025)+spread,back-.027,1.20+random.uniform(-.07,.045)))]
        path=spline(pts,5)
        add_tube(path,random.uniform(.0027,.0045),random.uniform(.0010,.0017),i%5)
        # A finer strand follows each lock, breaking the smooth surface.
        offset=[p+Vector((random.uniform(-.0004,.0004),-.0015,0)) for p in path]
        add_tube(offset,.00018,.00018,(i+2)%5,3)
# Back layers fill the silhouette without a solid hanging cylinder.
for i in range(70):
    phi=random.uniform(.12,math.pi-.12)
    x=.091*math.cos(phi);y=.008+.107*math.sin(phi)
    pts=[Vector((x*.55,y*.6,1.68)),Vector((x,y,1.61)),Vector((x*1.13,y+.012,1.43)),Vector((x*1.5,y+.016,1.23)),Vector((x*1.55,y,1.13+random.uniform(-.05,.04)))]
    add_tube(spline(pts),random.uniform(.003,.005),.0018,i%5)
# Face-framing side-swept strands, corresponding to the supplied hairstyle.
for side in [-1,1]:
    for i in range(12):
        a=i/11
        pts=[Vector((-.012,-.045,1.69)),Vector((side*.044,-.085,1.665)),Vector((side*(.078+a*.009),-.100,1.60)),Vector((side*(.092+a*.008),-.095,1.50)),Vector((side*(.105+a*.012),-.105,1.36+random.uniform(-.025,.025)))]
        add_tube(spline(pts),.0013,.0007,i%5,5)
# Join all locks into one draw call while retaining variation between strands.
mesh=bpy.data.meshes.new('Asia loose parted hair');mesh.from_pydata(vertices,[],polys);mesh.update()
hair=bpy.data.objects.new('Castell_Hair_Loose',mesh);scene.collection.objects.link(hair)
tint=mesh.color_attributes.new(name='HairTint',type='FLOAT_COLOR',domain='CORNER')
for p,c in zip(mesh.polygons,colors):
    p.use_smooth=True
    for li in p.loop_indices:tint.data[li].color=(*c,1)
hm=mat('Castell_Loose_Hair',palette[2],.38)
ha=hm.node_tree.nodes.new('ShaderNodeVertexColor');ha.layer_name='HairTint'
hm.node_tree.links.new(ha.outputs['Color'],hm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mesh.materials.append(hm)
bpy.context.view_layer.update();matrix=hair.matrix_world.copy();hair.parent=torso;hair.matrix_world=matrix
body['surface_detail']='R3: locally subdivided anatomical surface with continuous relief and blended coloration; no separate breast-detail objects.'
body['face_revision']='R3: actual eye, nose and jaw sculpt plus the fictional generated reference texture.'
# Re-evaluate weights after local subdivision, then save the editable source.
for v in body.data.vertices:
    groups=[g for g in v.groups if g.weight>0]
    total=sum(g.weight for g in groups)
    if total:
        for g in groups:body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.ortho_scale=.56
camera.location=(.62,-3,1.535);camera.rotation_euler=(Vector((0,0,1.535))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-asia-r3.blend'))
scene.render.filepath=os.path.join(OUT,'head.png');bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=1.94;camera.location=(1.1,-3.8,1.15);camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=900;scene.render.resolution_y=1300
scene.render.filepath=os.path.join(OUT,'full-body.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Castell_Skin_Rig'].hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','asia-r3-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
