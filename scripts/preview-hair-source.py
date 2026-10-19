import bpy,os,json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE=r'C:/Users/torre/Downloads/assets/models/assets/models/female-half-bun-_57ff81a2-2dd9-4c32-bd18-bb97e7100590/female-half-bun-haircut_2K_11b2f44d-5f7d-49e2-ad7d-1d4699a2d85e.blend'
bpy.ops.wm.open_mainfile(filepath=SOURCE)
out=os.path.join(ROOT,'artifacts','hair-integration');os.makedirs(out,exist_ok=True)
report={'objects':[],'materials':[],'images':[]}
for o in bpy.data.objects:
    coords=[o.matrix_world@Vector(c) for c in o.bound_box]
    report['objects'].append({'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)],'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'modifiers':[m.type for m in o.modifiers]})
for m in bpy.data.materials:
    report['materials'].append({'name':m.name,'nodes':[(n.name,n.type) for n in m.node_tree.nodes] if m.use_nodes else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.use_nodes else []})
for i in bpy.data.images:report['images'].append({'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)})
with open(os.path.join(out,'inspection.json'),'w') as f:json.dump(report,f,indent=2)

o=bpy.data.objects['Female_Half_Bun_Haircut']
print('UV_LAYERS',[u.name for u in o.data.uv_layers])
for group in bpy.data.node_groups:
    print('GROUP',group.name)
    if 'UV' in group.name:
        for n in group.nodes:print(n.name,n.type,[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Preview World');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.6
cam=bpy.data.objects.new('Preview',bpy.data.cameras.new('Preview'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.34
scene.render.resolution_x=500;scene.render.resolution_y=600;scene.render.resolution_percentage=100
for name,pos in [('front',(0,-1,.13)),('side',(-1,0,.13))]:
    cam.location=pos;cam.rotation_euler=(Vector((.02,0,.13))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(out,'source-'+name+'.png');bpy.ops.render.render(write_still=True)
