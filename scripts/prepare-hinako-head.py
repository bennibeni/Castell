"""Prepare only the supplied head, eyes and lashes, at Castell scale."""
import bpy,bmesh,os
from mathutils import Matrix,Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','hinako');os.makedirs(OUT,exist_ok=True)
SOURCE=r'C:\Users\torre\Downloads\realistic+girl\hinako'
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'hinako blender 4.5 .blend'))
scene=bpy.context.scene
deps=bpy.context.evaluated_depsgraph_get()
parts=[]
for name in ['BODY','eyes','lashes']:
    original=bpy.data.objects[name]
    data=bpy.data.meshes.new_from_object(original.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
    data.transform(original.matrix_world)
    if name=='BODY':
        bm=bmesh.new();bm.from_mesh(data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,2.59),plane_no=(0,0,1),clear_inner=True)
        bm.to_mesh(data);bm.free();data.update()
    obj=bpy.data.objects.new('Castell_Hinako_'+{'BODY':'Head','eyes':'Eyes','lashes':'Lashes'}[name],data)
    parts.append(obj)
# Remove source scene and rig widgets, retaining just the evaluated head parts.
for obj in list(bpy.data.objects):
    if obj not in parts:bpy.data.objects.remove(obj,do_unlink=True)
root=bpy.data.objects.new('Castell_Head_Assembly',None);scene.collection.objects.link(root)
root['description']='Head-only preparation from user supplied Hinako asset. No body or clothing changes.'
for obj in parts:
    scene.collection.objects.link(obj)
    for v in obj.data.vertices:v.co=Vector((v.co.x*.64,v.co.y*.64+.018,(v.co.z-2.817)*.64+1.553))
    obj.parent=root
    for p in obj.data.polygons:p.use_smooth=True
# Resolve external images and create portable, moderate-resolution copies, one at a time.
used=set()
for obj in parts:
    for mat in obj.data.materials:
        if mat and mat.node_tree:
            for n in mat.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image:used.add(n.image)
for image in used:
    print('TEXTURE_SOURCE',image.name,repr(image.filepath),image.source,flush=True)
    if image.source!='FILE' or not image.filepath:
        continue
    filename=image.filepath.replace('\\','/').rsplit('/',1)[-1]
    path=os.path.join(SOURCE,'textures',filename)
    if not os.path.isfile(path):raise RuntimeError('Missing head texture: '+filename)
    image.filepath=path;image.reload()
    limit=4096 if 'body_' in filename else 2048
    width,height=image.size
    if max(width,height)>limit:
        factor=limit/max(width,height);image.scale(round(width*factor),round(height*factor))
    image.filepath_raw=os.path.join(OUT,'head-'+filename.rsplit('.',1)[0]+'.png');image.file_format='PNG';image.save();image.pack()
    print('TEXTURE_READY',filename,list(image.size),flush=True)
for obj in parts:
    for mat in obj.data.materials:
        if not mat or not mat.node_tree:continue
        p=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not p:continue
        p.inputs['Metallic'].default_value=0
        if obj.name.endswith('Head'):
            mat.name='Castell_Hinako_Skin';p.inputs['Subsurface Weight'].default_value=.05;p.inputs['Subsurface Scale'].default_value=.0012
        elif obj.name.endswith('Eyes'):
            mat.name='Castell_Hinako_Eyes';p.inputs['Roughness'].default_value=.15;p.inputs['Coat Weight'].default_value=.8;p.inputs['Coat Roughness'].default_value=.04
        else:mat.name='Castell_Hinako_Lashes';mat.surface_render_method='DITHERED';mat.use_backface_culling=False
# Clear external UI scripts from the derivative file; source remains untouched.
for txt in list(bpy.data.texts):bpy.data.texts.remove(txt)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Head studio');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
for name,pos,power,size in [('Key',(-1,-2,2.5),95,1.4),('Fill',(1,-1,1.9),35,1.6),('Rim',(.5,1,2.4),40,1.4)]:
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,1.54))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=power;light.data.size=size
cam=bpy.data.objects.new('Head camera',bpy.data.cameras.new('Head camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.35
cam.location=(.45,-3,1.545);cam.rotation_euler=(Vector((0,0,1.545))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=750;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
bpy.ops.object.select_all(action='DESELECT');parts[0].select_set(True);bpy.context.view_layer.objects.active=parts[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Castell-testa-Hinako.blend'))
scene.render.filepath=os.path.join(OUT,'testa.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for obj in parts:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'blender','Castell-testa-Hinako.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
print('HINAKO_HEAD_READY',flush=True)
