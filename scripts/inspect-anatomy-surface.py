import bpy,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','Castell-atleta-materiali-realistici.blend'))
body=bpy.data.objects['Castell_Body'];m=body.data
tree=BVHTree.FromPolygons([v.co.copy() for v in m.vertices],[list(p.vertices) for p in m.polygons])
for z in [1.30,1.27,1.24,1.21,1.18,1.15,1.10,1.06,1.02,.98,.94,.90,.86,.82,.78]:
    row=[]
    for x in [0,.025,.05,.075,.10,.125]:
        pt,n,idx,d=tree.ray_cast(Vector((x,-.6,z)),Vector((0,1,0)))
        row.append(round(pt.y,4) if pt else None)
    print('ROW',z,row,flush=True)
