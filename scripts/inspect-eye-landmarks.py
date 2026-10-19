import bpy,os,json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
o=bpy.data.objects['Castell_Body'];m=o.data
eyeidx=next(i for i,v in enumerate(m.materials) if v.name=='Castell_Eyes')
ids={i for p in m.polygons if p.material_index==eyeidx for i in p.vertices}
for sign in [-1,1]:
    vs=[m.vertices[i] for i in ids if m.vertices[i].co.x*sign>0]
    print('EYE',sign,'min',[min(v.co[j] for v in vs) for j in range(3)],'max',[max(v.co[j] for v in vs) for j in range(3)],flush=True)
    front=sorted(vs,key=lambda v:v.co.y)[:10]
    print('FRONT',[list(v.co) for v in front],flush=True)
# Boundary loops of eye sockets, excluding eyeball material.
edge_faces={}
for p in m.polygons:
    if p.material_index==eyeidx:continue
    for k in p.edge_keys:edge_faces[k]=edge_faces.get(k,0)+1
points=set(i for k,c in edge_faces.items() if c==1 for i in k)
pts=[list(m.vertices[i].co) for i in points if 1.53<m.vertices[i].co.z<1.57 and m.vertices[i].co.y<-.06]
with open(os.path.join(ROOT,'artifacts','photoreal-study','eye-boundary.json'),'w') as f:json.dump(pts,f)
print('BOUNDARY',pts,flush=True)
