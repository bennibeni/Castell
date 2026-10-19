"""Capelli lunghi castani con riga in mezzo sulla base animabile Castell.
Il viso e il corpo non vengono modificati: si aggiunge solo l'oggetto Capelli
(figlio di Castell_Torso, quindi segue le pose) e una tinta scura del cuoio capelluto.
Uso: python3 -I capelli_base.py -- input.blend output.blend
"""
import bpy, sys, math, random, bisect
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
N_STRANDS = int(argv[2]) if len(argv) > 2 else 30000
bpy.ops.wm.open_mainfile(filepath=SRC, load_ui=False)
random.seed(11)

body = bpy.data.objects['Castell_Body']
dg = bpy.context.evaluated_depsgraph_get()
em = body.evaluated_get(dg).to_mesh()
MW = body.matrix_world
W = [MW @ v.co for v in em.vertices]
eye = set(v for p in em.polygons if p.material_index == 1 for v in p.vertices)
tris, skin_tris = [], []
for p in em.polygons:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1):
        tris.append((vs[0], vs[k], vs[k + 1]))
        if p.material_index != 1: skin_tris.append((vs[0], vs[k], vs[k + 1]))
BVH = BVHTree.FromPolygons(W, skin_tris)

# riferimenti della testa (misurati sulla base: stessa mesh del manichino, spostata)
eyes = [W[i] for i in eye]
EYE_Z = sum(p.z for p in eyes) / len(eyes)
TOP = max(p.z for p in W)
S = (TOP - EYE_Z) / 0.1106          # scala rispetto alle misure del manichino originale
def Z(z_orig):                       # quota del manichino originale -> quota della base
    return EYE_Z + (z_orig - 1.6148) * S
HC = Vector((0, -0.005 * S, Z(1.625)))
print('occhi', round(EYE_Z, 4), 'cima', round(TOP, 4), 'scala', round(S, 4))

def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def hairline_z(p):
    phi = abs(math.atan2(p.x, -(p.y - HC.y)))       # 0 davanti, pi dietro
    if phi < 0.45: z = 1.689
    elif phi < 1.05: z = 1.689 - 0.037 * (phi - 0.45) / 0.6
    elif phi < 1.55: z = 1.652
    elif phi < 2.2: z = 1.652 - 0.112 * (phi - 1.55) / 0.65
    else: z = 1.54
    return Z(z)

def is_scalp(p):
    if p.z < hairline_z(p): return False
    if abs(p.x) > 0.068 * S and p.z < Z(1.662) and -0.04 < p.y < 0.035: return False   # orecchie
    return True

# ── radici: campionamento per area, più fitte vicino alla riga e all'attaccatura ──
scalp = []
for t in skin_tris:
    a, b, c = W[t[0]], W[t[1]], W[t[2]]
    if a.z < Z(1.5): continue
    cen = (a + b + c) / 3
    if is_scalp(cen):
        area = ((b - a).cross(c - a)).length / 2
        edge = smooth(1 - (cen.z - hairline_z(cen)) / 0.02)       # vicino all'attaccatura
        part = smooth(1 - abs(cen.x) / 0.015) * (cen.y < 0.03)    # lungo la riga
        scalp.append((a, b, c, area * (1 + 0.8 * edge + 0.6 * part)))
acc, run = [], 0.0
for s in scalp:
    run += s[3]; acc.append(run)
def sample_root():
    a, b, c, _ = scalp[min(bisect.bisect(acc, random.random() * run), len(scalp) - 1)]
    u, v = random.random(), random.random()
    if u + v > 1: u, v = 1 - u, 1 - v
    return a + (b - a) * u + (c - a) * v

def face_half_width(z):
    pts = ((1.44, 0.0), (1.49, 0.047), (1.53, 0.066), (1.58, 0.071), (1.62, 0.075), (1.66, 0.072), (1.69, 0.062), (1.71, 0.0))
    zo = 1.6148 + (z - EYE_Z) / S
    for (z0, w0), (z1, w1) in zip(pts, pts[1:]):
        if z0 <= zo <= z1: return (w0 + (w1 - w0) * (zo - z0) / (z1 - z0)) * S
    return 0.0

STEP = 0.005
def grow(root):
    loc, nrm, _, _ = BVH.find_nearest(root)
    sd = 1 if root.x >= 0 else -1
    if abs(root.x) < 0.002: sd = random.choice((1, -1))
    back = smooth(root.y / 0.06)
    # davanti: la ciocca parte verso l'alto/indietro dalla riga (volume) e poi scende di lato
    want = Vector((sd * (1 - 0.75 * back), 0.45 * (1 - back) + 0.5 * back, -0.35 * (1 - back) - 1.0 * back))
    d = (want - nrm * want.dot(nrm)).normalized()
    front = root.y < -0.02 * S
    if front and abs(root.x) > 0.03:
        length = random.uniform(0.24, 0.34)          # ciocche che incorniciano il viso
    else:
        length = random.uniform(0.36, 0.47)
    lift = 0.0025 + 0.013 * random.random() ** 1.4
    lift *= 1.0 + 0.6 * smooth(1 - abs(root.x) / 0.03) * (root.y < 0.02)   # volume vicino alla riga
    margin = random.uniform(0.003, 0.016)
    clump = Vector((round(root.x / 0.014), round(root.y / 0.014), round(root.z / 0.014))) * 1.9
    p = loc + nrm * 0.0008
    pts = [p.copy()]
    travelled = 0.0
    while travelled < length:
        g = 0.05 + 0.25 * smooth(travelled / 0.06)
        wav = noise.noise_vector(clump + p * 7) * 0.06 + noise.noise_vector(p * 80 + Vector((root.x * 400, root.y * 400, 0))) * 0.006
        d = (d + Vector((0, 0, -g)) + wav).normalized()
        p = p + d * STEP
        travelled += STEP
        # sulla calotta il volume cresce gradualmente dalla radice
        off = lift * smooth(travelled / 0.035) + 0.0008
        for _ in range(2):
            loc, nrm, _, dist = BVH.find_nearest(p)
            if (p - loc).dot(nrm) < 0 or dist < off:
                p = loc + nrm * off
        if travelled < 0.10 and p.z > Z(1.60):
            loc, nrm, _, dist = BVH.find_nearest(p)
            if dist > off + 0.0015: p = loc + nrm * (off + 0.0015)
        # il viso resta libero
        if p.y < -0.03:
            hw = face_half_width(p.z) + margin - 0.004
            if hw > 0 and abs(p.x) < hw:
                p.x = sd * hw
        pts.append(p.copy())
        if len(pts) > 2: d = (pts[-1] - pts[-2]).normalized()
    for _ in range(2):
        pts = [pts[0]] + [(pts[k - 1] + pts[k] * 2 + pts[k + 1]) / 4 for k in range(1, len(pts) - 1)] + [pts[-1]]
    return pts

guides_n = 700
guides = [grow(sample_root()) for _ in range(guides_n)]
kd = {1: KDTree(guides_n), -1: KDTree(guides_n)}
for i, g in enumerate(guides):
    kd[1 if g[min(len(g) - 1, 8)].x >= 0 else -1].insert(g[0], i)
kd[1].balance(); kd[-1].balance()

def follow(root):
    """Ciocca che segue una guida vicina dello stesso lato: ciocche raggruppate, senza attraversare il viso."""
    own = grow(root)
    side = 1 if own[min(len(own) - 1, 8)].x >= 0 else -1
    found = kd[side].find(root)
    if found[1] is None or found[2] > 0.012:
        return own
    g = guides[found[1]]
    shift = root - g[0]
    n = min(len(own), len(g))
    out = []
    for k, q in enumerate(own):
        if k < n:
            t = k / max(1, len(own) - 1)
            target = g[k] + shift * (1 - 0.5 * smooth(t))
            q = q.lerp(target, 0.15 + 0.4 * smooth(t))
        out.append(q)
    for k in range(1, len(out)):
        loc, nrm, _, dist = BVH.find_nearest(out[k])
        if (out[k] - loc).dot(nrm) < 0 or dist < 0.0012:
            out[k] = loc + nrm * 0.0012
    return out

strands = guides + [follow(sample_root()) for _ in range(N_STRANDS - guides_n)]

# ── oggetto curve, figlio di Castell_Torso ──
hc = bpy.data.hair_curves.new('Capelli')
hc.add_curves([len(s) for s in strands])
hc.attributes['position'].data.foreach_set('vector', [c for s in strands for q in s for c in q])
rad = []
for s in strands:
    n = len(s)
    for k in range(n):
        t = k / max(1, n - 1)
        rad.append(0.00018 * (1 - 0.75 * t ** 1.5))
(hc.attributes.get('radius') or hc.attributes.new('radius', 'FLOAT', 'POINT')).data.foreach_set('value', rad)

mat = bpy.data.materials.new('Capelli_castani')
N, L = mat.node_tree.nodes, mat.node_tree.links
for n in list(N):
    if n.type != 'OUTPUT_MATERIAL': N.remove(n)
h = N.new('ShaderNodeBsdfHairPrincipled'); h.parametrization = 'MELANIN'
h.inputs['Melanin'].default_value = 0.86
h.inputs['Melanin Redness'].default_value = 0.42
h.inputs['Roughness'].default_value = 0.36
h.inputs['Radial Roughness'].default_value = 0.55
h.inputs['Coat'].default_value = 0.05
h.inputs['Random Roughness'].default_value = 0.2
h.inputs['Random Color'].default_value = 0.12
L.new(h.outputs[0], N['Material Output'].inputs['Surface'])
mat.diffuse_color = (0.09, 0.055, 0.035, 1)
hc.materials.append(mat)
hair = bpy.data.objects.new('Capelli', hc)
for col in body.users_collection: col.objects.link(hair)
torso = bpy.data.objects['Castell_Torso']
hair.parent = torso
hair.matrix_parent_inverse = torso.matrix_world.inverted()

# ── cuoio capelluto scuro sotto i capelli (solo colore, nessuna modifica alla mesh) ──
me = body.data
vals = []
for v in me.vertices:
    p = MW @ v.co
    vals.append(smooth((p.z - hairline_z(p) - 0.006) / 0.012) if p.z > Z(1.5) else 0.0)
a = me.attributes.get('cuoio_capelluto') or me.attributes.new('cuoio_capelluto', 'FLOAT', 'POINT')
a.data.foreach_set('value', vals)
skin = body.material_slots[0].material
N, L = skin.node_tree.nodes, skin.node_tree.links
bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
link = bsdf.inputs['Base Color'].links[0] if bsdf.inputs['Base Color'].links else None
an = N.new('ShaderNodeAttribute'); an.attribute_name = 'cuoio_capelluto'
mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = 'Tinta_cuoio_capelluto'
mx.inputs[7].default_value = (0.055, 0.035, 0.025, 1)
if link:
    L.new(link.from_socket, mx.inputs[6])
else:
    mx.inputs[6].default_value = bsdf.inputs['Base Color'].default_value
L.new(an.outputs['Fac'], mx.inputs['Factor'])
L.new(mx.outputs[2], bsdf.inputs['Base Color'])

bpy.context.scene.render.engine = 'CYCLES'
bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
print('OK', len(strands), 'ciocche', sum(len(s) for s in strands), 'punti')
