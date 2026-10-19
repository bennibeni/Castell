"""New adult character sculpt from the original adult base, not donor facial geometry."""
import bpy,bmesh,os,math,shutil
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','original-adult-head');os.makedirs(OUT,exist_ok=True)
target=os.path.join(ROOT,'public','models','catalog','head-adult-smile.glb')
backup=os.path.join(OUT,'previous-head-adult-smile.glb')
if not os.path.exists(backup):shutil.copy2(target,backup)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-viso-reference.blend'))
scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();parts=[]
for obj in list(scene.objects):
    if obj.type!='MESH':continue
    data=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps);data.transform(obj.matrix_world)
    if obj.name=='Castell_Body':
        bm=bmesh.new();bm.from_mesh(data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,1.415),plane_no=(0,0,1),clear_inner=True)
        bm.to_mesh(data);bm.free()
    part=bpy.data.objects.new('AdultOriginal_'+obj.name,data);scene.collection.objects.link(part);parts.append(part)
for obj in list(scene.objects):
    if obj not in parts and obj.type in {'MESH','ARMATURE','EMPTY'}:bpy.data.objects.remove(obj,do_unlink=True)
face=next(o for o in parts if o.name=='AdultOriginal_Castell_Body')
def g(v,c,w):return math.exp(-.5*((v-c)/w)**2)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for obj in parts:
    if 'Hair' in obj.name or 'hair' in obj.name and 'Facial' not in obj.name:continue
    for v in obj.data.vertices:
        x,y,z=v.co;a=abs(x);side=1 if x>=0 else -1
        if z<1.43 or z>1.62:continue
        front=1-smooth(-.055,-.012,y)
        # Mature, individual bone structure: wider mandibular angle, defined chin
        # and cheekbone; original adult identity and skull dimensions retained.
        dx=side*(.0018*g(a,.057,.018)*g(z,1.457,.020)+.0010*g(a,.055,.017)*g(z,1.523,.012))
        dy=-.0012*g(a,.047,.019)*g(z,1.523,.012)
        dy+=.0010*g(a,.043,.019)*g(z,1.492,.016)
        dy-=.0011*g(x,0,.010)*g(z,1.535,.018)
        dz=-.0015*g(x,0,.025)*g(z,1.437,.012)
        # Reduce the startled round opening. The same deformation follows the
        # eye surface, eyelids and lashes so their placement stays coherent.
        eye=g(a,.036,.016)*g(z,1.551,.013)
        dz-=.075*(z-1.551)*eye
        # Less pinched inner brow, slight natural closed-mouth smile.
        dz+=.0008*g(a,.020,.009)*g(z,1.575,.005)
        corner=g(a,.025,.009)*g(z,1.477,.008)
        dz+=.0008*corner
        v.co+=Vector((dx*front,dy*front,dz*front))
    obj.data.update()
    for poly in obj.data.polygons:poly.use_smooth=True
skin=bpy.data.materials['Castell_Skin'];nodes=skin.node_tree.nodes;links=skin.node_tree.links
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Roughness'].default_value=.49;bs.inputs['Subsurface Weight'].default_value=.08;bs.inputs['Subsurface Scale'].default_value=.0012
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=420;noise.inputs['Detail'].default_value=2
coords=nodes.new('ShaderNodeTexCoord');links.new(coords.outputs['Position'] if 'Position' in coords.outputs else coords.outputs['Object'],noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00012
links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
# Bake subtle normal detail to retain the material in the browser renderer.
normal=bpy.data.images.new('Original adult skin microdetail',width=2048,height=2048,alpha=False);normal.colorspace_settings.name='Non-Color'
for mat in face.data.materials:
    n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=normal;mat.node_tree.nodes.active=n
bpy.ops.object.select_all(action='DESELECT');face.select_set(True);bpy.context.view_layer.objects.active=face
scene.render.engine='CYCLES';scene.cycles.samples=1;bpy.ops.object.bake(type='NORMAL')
normal.filepath_raw=os.path.join(OUT,'skin-normal.png');normal.file_format='PNG';normal.save();normal.pack()
n=nodes.new('ShaderNodeTexImage');n.image=normal
uv=nodes.new('ShaderNodeUVMap');uv.uv_map=face.data.uv_layers.active.name;links.new(uv.outputs[0],n.inputs['Vector'])
nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;links.new(n.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
face['identity']='Original fictional adult character; sculpted from the adult reference mesh. No Hinako facial mesh.'
face['features']='Defined cheekbones, mature jaw and chin, relaxed lids, subtle smile, baked skin normal.'
for obj in parts:
    for mat in obj.data.materials:
        if not mat or not mat.node_tree:continue
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                im=node.image;w,h=im.size
                if max(w,h)>2048:
                    ratio=2048/max(w,h);im.scale(round(w*ratio),round(h*ratio));im.pack()
cam=scene.camera;cam.data.ortho_scale=.36;cam.location=(.20,-3,1.54);cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=850;scene.render.resolution_y=950
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-testa-adulta-originale.blend'))
scene.render.filepath=os.path.join(OUT,'viso.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'head-adult-original-new-raw.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('ORIGINAL_ADULT_HEAD_READY',flush=True)
