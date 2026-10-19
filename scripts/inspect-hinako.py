import bpy,os,json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'artifacts','hinako');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\torre\Downloads\realistic+girl\hinako\hinako blender 4.5 .blend')
bpy.context.view_layer.update()
report={'objects':[],'materials':[],'images':[]}
for o in bpy.context.scene.objects:
    points=[o.matrix_world@Vector(c) for c in o.bound_box]
    info={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'visible':o.visible_get(),'hide_render':o.hide_render,'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)],'matrix':[list(r) for r in o.matrix_world],'modifiers':[(m.name,m.type) for m in o.modifiers]}
    if o.type=='MESH':info.update(vertices=len(o.data.vertices),triangles=sum(len(p.vertices)-2 for p in o.data.polygons),materials=[m.name if m else None for m in o.data.materials],uvs=[u.name for u in o.data.uv_layers],shapes=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [])
    report['objects'].append(info)
for m in bpy.data.materials:
    report['materials'].append({'name':m.name,'nodes':[(n.name,n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes] if m.node_tree else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.node_tree else []})
for i in bpy.data.images:report['images'].append({'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)})
with open(os.path.join(OUT,'inspection.json'),'w',encoding='utf8') as f:json.dump(report,f,indent=2)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=650;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
meshes=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector([min(p[k] for p in points) for k in range(3)]);hi=Vector([max(p[k] for p in points) for k in range(3)])
center=(lo+hi)/2;height=(hi.z-lo.z)*1.1
cam=bpy.data.objects.new('Inspection camera',bpy.data.cameras.new('Inspection camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=height
cam.location=center+Vector((0,-4*height,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'source.png');bpy.ops.render.render(write_still=True)
print('HINAKO_INSPECTED',flush=True)
