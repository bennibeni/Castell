import bpy,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\torre\Downloads\realistic+girl\hinako\hinako blender 4.5 .blend')
material=bpy.data.materials['hair'];group=next(n for n in material.node_tree.nodes if n.type=='GROUP')
def describe(tree):
    return {'nodes':[{'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'inputs':[(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value) for s in n.inputs if hasattr(s,'default_value') and s.type not in {'SHADER'}]} for n in tree.nodes], 'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
out={'group':describe(group.node_tree),'inputs':[(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value) for s in group.inputs if hasattr(s,'default_value')]}
with open(os.path.join(ROOT,'artifacts','hinako','hair-shader.json'),'w',encoding='utf8') as f:json.dump(out,f,ensure_ascii=True,indent=2)
