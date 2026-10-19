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
