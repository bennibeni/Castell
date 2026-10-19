"""Export interchangeable bodies and static heads without changing source blends."""
import bpy,bmesh,os,subprocess,shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'public','models','catalog');os.makedirs(OUT,exist_ok=True)
def openblend(name):bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender',name))
def cut(mesh,keep_top):
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,1.415),plane_no=(0,0,1),clear_inner=keep_top,clear_outer=not keep_top)
    bm.to_mesh(mesh);bm.free();mesh.update()
def export(name,objects):
    images=set()
    for obj in objects:
        if obj.type!='MESH':continue
        for mat in obj.data.materials:
            if not mat or not mat.node_tree:continue
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:images.add(node.image)
    for image in images:
        w,h=image.size
        if max(w,h)>2048:
            ratio=2048/max(w,h);image.scale(round(w*ratio),round(h*ratio));image.pack()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.hide_set(False);obj.select_set(True)
    destination=os.path.join(ROOT,'blender','catalog') if name.endswith('-raw') else OUT
    os.makedirs(destination,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(destination,name+'.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
    print('CATALOG_READY',name,flush=True)
openblend('Castell-manichino-testa-nuova.blend')
for obj in list(bpy.context.scene.objects):
    if obj.name.startswith('Castell_Hinako_'):bpy.data.objects.remove(obj,do_unlink=True)
export('body-mannequin',[o for o in bpy.context.scene.objects if o.type in {'MESH','EMPTY','ARMATURE'}])
openblend('Castell-atleta-viso-reference.blend')
body=bpy.data.objects['Castell_Body'];cut(body.data,False)
for obj in list(bpy.context.scene.objects):
    if obj.type=='MESH' and obj!=body:bpy.data.objects.remove(obj,do_unlink=True)
export('body-adult-raw',[o for o in bpy.context.scene.objects if o.type in {'MESH','EMPTY','ARMATURE'}])
subprocess.run(['node',os.path.join(ROOT,'scripts','create-lightweight-head.mjs')],check=True,cwd=ROOT)
detail=os.path.join(ROOT,'artifacts','public-archive','models','catalog','head-hinako.glb')
optimization=os.path.join(ROOT,'artifacts','head-texture-optimization');os.makedirs(optimization,exist_ok=True)
original=os.path.join(optimization,'original.glb')
if os.path.exists(detail):shutil.copy2(detail,original)
elif not os.path.exists(original):raise FileNotFoundError('Detailed head missing: restore the local archived head-hinako.glb')
subprocess.run(['node',os.path.join(ROOT,'scripts','optimize-head-textures.mjs')],check=True,cwd=ROOT)
shutil.copy2(os.path.join(optimization,'optimized.glb'),os.path.join(OUT,'head-detailed-small-optimized.glb'))
print('CATALOG_COMPLETE',flush=True)
