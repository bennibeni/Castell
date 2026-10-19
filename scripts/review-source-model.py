import bpy, json, os
from mathutils import Vector
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'artifacts','source-model-review')
os.makedirs(out,exist_ok=True)
report={'objects':[],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images]}
for o in bpy.context.scene.objects:
    item={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'dimensions':list(o.dimensions),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    if o.type=='MESH':
        item.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),triangles=sum(max(0,len(p.vertices)-2) for p in o.data.polygons),uv_layers=[u.name for u in o.data.uv_layers],vertex_groups=[g.name for g in o.vertex_groups],shape_keys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],materials=[{'name':m.name,'nodes':[n.type for n in m.node_tree.nodes] if m and m.node_tree else [],'textures':[n.image.filepath for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m and m.node_tree else []} for m in o.data.materials])
    if o.type=='ARMATURE':item['bones']=[b.name for b in o.data.bones]
    report['objects'].append(item)
with open(os.path.join(out,'inspection.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print('SOURCE_REVIEW='+json.dumps(report))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if meshes:
    coords=[o.matrix_world@Vector(corner) for o in meshes for corner in o.bound_box]
    lo=Vector(tuple(min(v[k] for v in coords) for k in range(3)));hi=Vector(tuple(max(v[k] for v in coords) for k in range(3)))
    center=(lo+hi)*.5;height=max(hi.z-lo.z,hi.x-lo.x,1)*1.18
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));bpy.context.scene.collection.objects.link(camera)
    camera.data.type='ORTHO';camera.data.ortho_scale=height
    scene=bpy.context.scene;scene.camera=camera;scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=650;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    for name,offset in [('front',(0,-4,0)),('side',(4,0,0))]:
        camera.location=center+Vector(offset)*height
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
