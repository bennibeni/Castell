"""Volto ispirato al disegno, capelli, trucco e divisa da castellera sul manichino
'Female body reference'. Tutto non distruttivo: shape key, oggetti e modificatori nuovi.
Uso: python3 -I build_castellera.py -- input.blend output.blend
"""
import bpy, bmesh, sys, math, random
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC, load_ui=False)
random.seed(7)

body = bpy.data.objects['Female body reference']
me = body.data
EYE_MAT = 1

def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def fall(d, r0, r1):
    return 1.0 if d <= r0 else (0.0 if d >= r1 else smooth((r1 - d) / (r1 - r0)))

def trap(v, a, b, c, d):
    if v <= a or v >= d: return 0.0
    if v < b: return smooth((v - a) / (b - a))
    if v <= c: return 1.0
    return smooth((d - v) / (d - c))

# ── 1. shape key del viso ────────────────────────────────────────────────
eye_verts = set()
for p in me.polygons:
    if p.material_index == EYE_MAT: eye_verts.update(p.vertices)
EYE_C = {1: Vector((0.0351, -0.098, 1.6148)), -1: Vector((-0.0351, -0.098, 1.6148))}
EYE_S = 1.15

if not me.shape_keys: body.shape_key_add(name='Basis')
key = body.shape_key_add(name='Viso_disegno', from_mix=False)
for i, v in enumerate(me.vertices):
    p = v.co.copy()
    if p.z < 1.46: continue
    q = p.copy()
    sd = 1 if p.x >= 0 else -1
    c = EYE_C[sd]
    d = (p - c).length
    if i in eye_verts:
        pass
    else:
        # apertura delle palpebre più ampia (solo x e z: il bulbo non sporge)
        w = fall(d, 0.019, 0.036)
        rel = p - c
        q.x += rel.x * (EYE_S - 1) * w
        q.z += rel.z * (EYE_S - 1) * w * 1.15
        # taglio a mandorla: angolo esterno leggermente sollevato
        if abs(p.x) > abs(c.x):
            q.z += 0.12 * (abs(p.x) - abs(c.x)) * fall(d, 0.014, 0.03)
        # mandibola a V e mento più stretto
        wj = trap(p.z, 1.472, 1.50, 1.535, 1.588) * (1.0 if p.y < 0.02 else fall(p.y, 0.02, 0.06))
        q.x -= p.x * 0.16 * wj
        # naso più sottile, punta meno sporgente e un po' all'insù
        wn = trap(p.z, 1.553, 1.562, 1.585, 1.60) * fall(abs(p.x), 0.012, 0.03) * (1.0 if p.y < -0.10 else 0.0)
        q.x -= p.x * 0.22 * wn
        tip = Vector((0, -0.134, 1.5755))
        wt = fall((p - tip).length, 0.004, 0.014)
        q.y += 0.0022 * wt; q.z += 0.0012 * wt
        # labbra più piene, bocca un po' più stretta
        if p.y < -0.10:
            wu = fall(math.hypot(p.x / 0.024, (p.z - 1.548) / 0.008), 0.5, 1.0)
            wl = fall(math.hypot(p.x / 0.022, (p.z - 1.535) / 0.008), 0.5, 1.0)
            q.y -= 0.0022 * wu + 0.0028 * wl
            q.z += 0.0007 * wu - 0.0009 * wl
            q.x -= p.x * 0.05 * trap(p.z, 1.525, 1.533, 1.552, 1.56) * fall(abs(p.x), 0.02, 0.032)
        # zigomi pieni e morbidi
        ch = Vector((sd * 0.040, -0.104, 1.586))
        q.y -= 0.0025 * fall((p - ch).length, 0.012, 0.032)
    key.data[i].co = q
key.value = 1.0

# Coordinate deformate e BVH del corpo per tutti i passi successivi
def deformed():
    return [kd.co.copy() for kd in key.data]
DEF = deformed()
tris = []
for p in me.polygons:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
body_tris = [t for t, p in zip(tris, [None]*len(tris))]
face_mat = []
for p in me.polygons:
    for k in range(1, len(p.vertices) - 1): face_mat.append(p.material_index)
BVH = BVHTree.FromPolygons(DEF, tris)
skin_tris = [t for t, m in zip(tris, face_mat) if m != EYE_MAT]
BVH_SKIN = BVHTree.FromPolygons(DEF, skin_tris)

# ── 2. pelle, trucco, occhi ──────────────────────────────────────────────
# maschere per vertice (interpolate dalla suddivisione)
masks = {n: [0.0] * len(me.vertices) for n in ('lips', 'blush', 'liner', 'shadow')}
for i, v in enumerate(me.vertices):
    p = v.co
    if p.z < 1.5 or p.z > 1.66 or i in eye_verts: continue
    if p.y < -0.105:
        up = fall(math.hypot(p.x / 0.0215, (p.z - 1.5450) / 0.0062), 0.55, 1.0) if p.z > 1.5395 else 0
        lo = fall(math.hypot(p.x / 0.0195, (p.z - 1.5360) / 0.0068), 0.55, 1.0) if p.z <= 1.5415 else 0
        masks['lips'][i] = max(up, lo)
    sd = 1 if p.x >= 0 else -1
    c = EYE_C[sd]
    masks['blush'][i] = fall((p - Vector((sd * 0.047, -0.098, 1.582))).length, 0.004, 0.026)
    d = (p - c).length
    if p.y < c.y - 0.004:
        rim = abs(d - 0.0200)
        if p.z > c.z - 0.002:
            masks['liner'][i] = fall(rim, 0.0015, 0.005) * fall(abs(p.x) - abs(c.x), 0.014, 0.026)
        if p.z > c.z + 0.004:
            masks['shadow'][i] = fall(d, 0.022, 0.034)
masks['scalp'] = [0.0] * len(me.vertices)
HC0 = Vector((0, -0.005, 1.625))
for i, v in enumerate(me.vertices):
    p = v.co
    if p.z < 1.5 or i in eye_verts: continue
    phi = abs(math.atan2(p.x, -(p.y - HC0.y)))
    if phi < 0.45: z = 1.688
    elif phi < 1.05: z = 1.692 - 0.04 * (phi - 0.45) / 0.6
    elif phi < 1.55: z = 1.652
    elif phi < 2.2: z = 1.652 - 0.11 * (phi - 1.55) / 0.65
    else: z = 1.535
    masks['scalp'][i] = smooth((p.z - z + 0.002) / 0.008)
for n, vals in masks.items():
    a = me.attributes.get(n) or me.attributes.new(n, 'FLOAT', 'POINT')
    a.data.foreach_set('value', vals)

def nodes_of(mat):
    return mat.node_tree.nodes, mat.node_tree.links

skin = bpy.data.materials['Body_bsd']
N, L = nodes_of(skin)
bsdf = N['Principled BSDF']; mix = N['Mix']
hsv = N.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = 0.86
hsv.inputs['Value'].default_value = 1.06; hsv.inputs['Hue'].default_value = 0.49
L.new(mix.outputs['Result'], hsv.inputs['Color'])
cur = hsv.outputs['Color']
def layer(attr, color, fac):
    global cur
    an = N.new('ShaderNodeAttribute'); an.attribute_name = attr
    mf = N.new('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = fac
    L.new(an.outputs['Fac'], mf.inputs[0])
    m = N.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY' if attr in ('liner', 'shadow') else 'MIX'
    m.inputs[7].default_value = color
    L.new(mf.outputs[0], m.inputs['Factor']); L.new(cur, m.inputs[6])
    cur = m.outputs[2]
layer('blush', (0.80, 0.42, 0.40, 1), 0.28)
layer('shadow', (0.86, 0.70, 0.66, 1), 0.35)
layer('lips', (0.42, 0.12, 0.11, 1), 0.85)
layer('liner', (0.10, 0.07, 0.06, 1), 1.0)
layer('scalp', (0.05, 0.03, 0.022, 1), 1.0)
L.new(cur, bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.46
bsdf.inputs['Subsurface Weight'].default_value = 0.35
bsdf.inputs['Subsurface Radius'].default_value = (0.0036, 0.0016, 0.0009)
bsdf.inputs['Subsurface Scale'].default_value = 1.0
# labbra un po' più lucide
lr = N.new('ShaderNodeAttribute'); lr.attribute_name = 'lips'
mr = N.new('ShaderNodeMapRange'); mr.inputs[3].default_value = 0.46; mr.inputs[4].default_value = 0.28
L.new(lr.outputs['Fac'], mr.inputs[0]); L.new(mr.outputs[0], bsdf.inputs['Roughness'])
nm = N['Normal Map']; nm.inputs['Strength'].default_value = 0.08

# occhi procedurali: iride castano scuro, pupilla, limbo, cornea lucida
eyes = bpy.data.materials['Eyes_bsd']
N, L = nodes_of(eyes)
for n in list(N):
    if n.type != 'OUTPUT_MATERIAL': N.remove(n)
out = N['Material Output']
tc = N.new('ShaderNodeTexCoord')
sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; L.new(sep.outputs[0], ab.inputs[0])
com = N.new('ShaderNodeCombineXYZ'); L.new(ab.outputs[0], com.inputs[0]); L.new(sep.outputs[1], com.inputs[1]); L.new(sep.outputs[2], com.inputs[2])
sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.0351, -0.098, 1.6148)
L.new(com.outputs[0], sub.inputs[0])
mul = N.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = (1, 0, 1)
L.new(sub.outputs[0], mul.inputs[0])
ln = N.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(mul.outputs[0], ln.inputs[0])
R = 0.0187
mrn = N.new('ShaderNodeMapRange'); mrn.inputs[2].default_value = R
L.new(ln.outputs['Value'], mrn.inputs[0])
# variazione radiale dell'iride
nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 4
L.new(tc.outputs['Object'], nz.inputs['Vector'])
ramp = N.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.01, 0.008, 0.007, 1)
cr.elements[1].position = 0.5; cr.elements[1].color = (0.03, 0.018, 0.012, 1)
for pos, col in ((0.21, (0.012, 0.009, 0.008, 1)), (0.23, (0.035, 0.018, 0.010, 1)),
                 (0.36, (0.022, 0.012, 0.007, 1)), (0.50, (0.02, 0.012, 0.009, 1)),
                 (0.55, (0.70, 0.66, 0.63, 1)), (1.0, (0.76, 0.72, 0.69, 1))):
    e = cr.elements.new(pos); e.color = col
mx = N.new('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.03; mx.inputs[2].default_value = -0.015
L.new(nz.outputs['Fac'], mx.inputs[0])
ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'
L.new(mrn.outputs[0], ad.inputs[0]); L.new(mx.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], ramp.inputs['Fac'])
eb = N.new('ShaderNodeBsdfPrincipled')
L.new(ramp.outputs['Color'], eb.inputs['Base Color'])
eb.inputs['Roughness'].default_value = 0.35
eb.inputs['Coat Weight'].default_value = 0.6; eb.inputs['Coat Roughness'].default_value = 0.06
L.new(eb.outputs[0], out.inputs['Surface'])

# suddivisione per il render (la shape key resta modificabile)
sub_mod = body.modifiers.new('Suddivisione', 'SUBSURF'); sub_mod.levels = 1; sub_mod.render_levels = 2
for p in me.polygons: p.use_smooth = True

# ── 3. utilità per le fibre (capelli, sopracciglia, ciglia) ─────────────
def make_curves(name, strands, radius_root, radius_tip, material):
    hc = bpy.data.hair_curves.new(name)
    hc.add_curves([len(s) for s in strands])
    pos = [c for s in strands for pt in s for c in pt]
    hc.attributes['position'].data.foreach_set('vector', pos)
    rad = []
    for s in strands:
        n = len(s)
        for k in range(n):
            t = k / max(1, n - 1)
            rad.append(radius_root + (radius_tip - radius_root) * (t ** 0.8))
    ra = hc.attributes.get('radius') or hc.attributes.new('radius', 'FLOAT', 'POINT')
    ra.data.foreach_set('value', rad)
    hc.materials.append(material)
    ob = bpy.data.objects.new(name, hc)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def hair_material(name, melanin, redness, rough):
    m = bpy.data.materials.new(name)
    N, L = nodes_of(m)
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL': N.remove(n)
    h = N.new('ShaderNodeBsdfHairPrincipled')
    h.parametrization = 'MELANIN'
    h.inputs['Melanin'].default_value = melanin
    h.inputs['Melanin Redness'].default_value = redness
    h.inputs['Roughness'].default_value = rough
    h.inputs['Radial Roughness'].default_value = 0.35
    h.inputs['Coat'].default_value = 0.1
    h.inputs['Random Roughness'].default_value = 0.15
    ri = N.new('ShaderNodeHairInfo')
    L.new(ri.outputs['Random'], h.inputs['Random Color']) if 'Random Color' in h.inputs else None
    h.inputs['Random Color'].default_value = 0.08
    L.new(h.outputs[0], N['Material Output'].inputs['Surface'])
    m.diffuse_color = (0.12, 0.07, 0.045, 1)
    return m

def nearest(p):
    loc, nrm, idx, dist = BVH_SKIN.find_nearest(p)
    return loc, nrm, dist

# ── 4. capelli lunghi scalati, riga in mezzo ────────────────────────────
HC = Vector((0, -0.005, 1.625))
def hairline(p):
    phi = abs(math.atan2(p.x, -(p.y - HC.y)))          # 0 davanti, pi dietro
    if phi < 0.45: z = 1.688 + 0.004 * (phi / 0.45)
    elif phi < 1.05: z = 1.692 - 0.04 * (phi - 0.45) / 0.6
    elif phi < 1.55: z = 1.652
    elif phi < 2.2: z = 1.652 - 0.11 * (phi - 1.55) / 0.65
    else: z = 1.535
    return z
def is_scalp(p):
    if p.z < hairline(p): return False
    if abs(p.x) > 0.068 and p.z < 1.66 and -0.04 < p.y < 0.035: return False  # orecchie
    return True

scalp = []
for t in skin_tris:
    a, b, c = (DEF[t[0]], DEF[t[1]], DEF[t[2]])
    if a.z < 1.5: continue
    cen = (a + b + c) / 3
    if is_scalp(cen):
        area = ((b - a).cross(c - a)).length / 2
        scalp.append((a, b, c, area))
tot = sum(s[3] for s in scalp)
acc = []; run = 0
for s in scalp:
    run += s[3]; acc.append(run)
import bisect
def sample_root():
    r = random.random() * tot
    a, b, c, _ = scalp[min(bisect.bisect(acc, r), len(scalp) - 1)]
    u, v = random.random(), random.random()
    if u + v > 1: u, v = 1 - u, 1 - v
    return a + (b - a) * u + (c - a) * v

def face_half_width(z):
    if z > 1.71 or z < 1.44: return 0.0
    pts = ((1.44, 0.0), (1.49, 0.045), (1.53, 0.064), (1.58, 0.070), (1.62, 0.074), (1.66, 0.070), (1.69, 0.060), (1.71, 0.0))
    for (z0, w0), (z1, w1) in zip(pts, pts[1:]):
        if z0 <= z <= z1: return w0 + (w1 - w0) * (z - z0) / (z1 - z0)
    return 0.0

STEP = 0.0055
def grow(root):
    loc, nrm, _ = nearest(root)
    sd = 1 if root.x >= 0 else -1
    back = smooth((root.y - 0.0) / 0.06)
    lateral = Vector((sd * (1 - back) + sd * 0.25 * back, 0.55 * back - 0.25 * (1 - back), -0.25 - 0.9 * back))
    d = (lateral - nrm * lateral.dot(nrm)).normalized()
    front = root.y < -0.03
    length = random.uniform(0.40, 0.52) if front else random.uniform(0.50, 0.62)
    layer_off = 0.0022 + 0.011 * random.random() ** 1.6
    margin = random.uniform(0.0, 0.012) if random.random() < 0.25 else random.uniform(0.012, 0.02)
    clump = Vector((round(root.x / 0.012), round(root.y / 0.012), round(root.z / 0.012))) * 1.7
    p = loc + nrm * 0.0012
    pts = [tuple(p)]
    travelled = 0.0
    while travelled < length:
        g = smooth(travelled / 0.07) * 0.22 + 0.04
        wav = noise.noise_vector(clump + p * 18) * 0.10 + noise.noise_vector(p * 90 + Vector((root.x * 300, 0, 0))) * 0.03
        d = (d + Vector((0, 0, -g)) + wav).normalized()
        p = p + d * STEP
        travelled += STEP
        # collisione con testa e corpo (i vestiti sporgono di circa 1 cm sotto il collo)
        off = layer_off + (0.011 if p.z < 1.47 else 0.0)
        for _ in range(2):
            loc, nrm, dist = nearest(p)
            rel = p - loc
            inside = rel.dot(nrm) < 0
            if inside or dist < off:
                p = loc + nrm * off
        # vicino al cuoio capelluto la ciocca resta aderente alla testa
        if travelled < 0.09 and p.z > 1.6:
            loc, nrm, dist = nearest(p)
            if dist > off + 0.002: p = loc + nrm * (off + 0.002)
        # il viso resta libero: le ciocche frontali lo incorniciano
        if p.y < -0.035:
            hw = face_half_width(p.z) + margin - 0.006
            if hw > 0 and abs(p.x) < hw:
                p.x = sd * hw
                d.x = abs(d.x) * sd * 0.5 + d.x * 0.5
        pts.append(tuple(p))
        if len(pts) > 2:
            d = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
    # leggero smussamento
    P = [Vector(q) for q in pts]
    for _ in range(2):
        P = [P[0]] + [(P[k - 1] + P[k] * 2 + P[k + 1]) / 4 for k in range(1, len(P) - 1)] + [P[-1]]
    return [tuple(q) for q in P]

hair_mat = hair_material('Capelli_castani', 0.90, 0.32, 0.30)
strands = [grow(sample_root()) for _ in range(20000)]
hair = make_curves('Capelli', strands, 0.00021, 0.00004, hair_mat)

# ── 5. sopracciglia e ciglia ─────────────────────────────────────────────
def ray_front(x, z):
    hit = BVH_SKIN.ray_cast(Vector((x, -0.4, z)), Vector((0, 1, 0)))
    return hit[0], hit[1]

brows = []
for sd in (1, -1):
    for _ in range(340):
        t = random.random() ** 0.8
        x = 0.016 + 0.052 * t
        zc = 1.6335 + 0.0055 * math.sin(math.pi * min(1, t / 0.8)) * (1 - 0.3 * t) - 0.004 * max(0, t - 0.8) / 0.2
        thick = 0.0032 * (1 - 0.55 * t)
        z = zc + random.uniform(-0.5, 0.5) * thick
        loc, nrm = ray_front(sd * x, z)
        if loc is None: continue
        dirv = Vector((sd * (0.7 + 0.6 * t), 0, 0.75 - 0.6 * t)) + Vector((0, 0, random.uniform(-0.15, 0.15)))
        dirv = (dirv - nrm * dirv.dot(nrm)).normalized()
        ln = random.uniform(0.004, 0.0065) * (0.7 + 0.3 * min(1, t / 0.15))
        s = []
        for k in range(5):
            q = loc + nrm * (0.0002 + 0.0004 * (k / 4) ** 2) + dirv * ln * k / 4
            s.append(tuple(q))
        brows.append(s)
brow_mat = hair_material('Sopracciglia', 0.9, 0.25, 0.4)
make_curves('Sopracciglia', brows, 0.000045, 0.000015, brow_mat)

lashes = []
for sd in (1, -1):
    c = EYE_C[sd]
    R = 0.0187
    eye_pts = [DEF[i] for i in eye_verts if (DEF[i].x > 0) == (sd > 0)]
    eye_bvh = BVHTree.FromPolygons(DEF, [t for t, m in zip(tris, face_mat) if m == EYE_MAT])
    near = []
    for i, v in enumerate(DEF):
        if i in eye_verts or (v - c).length > 0.03: continue
        loc, nrm, idx, dist = eye_bvh.find_nearest(v)
        if dist < 0.0018: near.append(v)
    upper = sorted([v for v in near if v.z > c.z - 0.001], key=lambda v: v.x)
    lower = sorted([v for v in near if v.z < c.z - 0.003], key=lambda v: v.x)
    print('margine palpebra', sd, len(upper), len(lower))
    def along(seq, n, up):
        out = []
        for _ in range(n):
            a = random.randrange(len(seq) - 1)
            q = seq[a].lerp(seq[a + 1], random.random())
            outer = max(0.0, (abs(q.x) - abs(c.x)) / 0.02)
            ln = (0.0062 + 0.0045 * outer) * random.uniform(0.75, 1.1) if up else (0.0025 + 0.001 * outer)
            base = Vector((sd * (0.15 + 0.6 * outer), -1.0, 0.2 if up else -0.5)).normalized()
            curl = Vector((0, 0.35, 1.3 if up else -0.4))
            s = []
            for k in range(6):
                t = k / 5
                pt = q + Vector((0, -0.0012, 0.0004 if up else -0.0002)) + base * ln * t + curl * ln * 0.45 * t * t
                s.append(tuple(pt))
            out.append(s)
        return out
    if len(upper) > 3: lashes += along(upper, 95, True)
    if len(lower) > 3: lashes += along(lower, 18, False)
lash_mat = hair_material('Ciglia', 1.0, 0.1, 0.3)
make_curves('Ciglia', lashes, 0.00006, 0.00001, lash_mat)

# ── 6. divisa da castellera ──────────────────────────────────────────────
SH = {1: Vector((0.165, -0.01, 1.395)), -1: Vector((-0.165, -0.01, 1.395))}
WR = {1: Vector((0.405, -0.13, 1.02)), -1: Vector((-0.405, -0.13, 1.02))}
def arm_t(p):
    sd = 1 if p.x >= 0 else -1
    a, b = SH[sd], WR[sd]
    return (p - a).dot(b - a) / (b - a).length_squared

def in_shirt(p, margin=0.0):
    if abs(p.x) > 0.19 + margin * 0 and p.z < 1.33:          # braccio
        return arm_t(p) < 0.72 - margin * 2
    if p.z < 0.97 + margin or p.z > 1.43 - margin: return False
    if p.y < -0.04 and abs(p.x) < 0.075 and p.z > 1.385 - margin: return False   # scollo
    if abs(p.x) > 0.13 and p.z > 1.33:
        return arm_t(p) < 0.72 - margin * 2 if abs(p.x) > 0.19 else True
    return True

def in_trousers(p, margin=0.0):
    return 0.13 + margin < p.z < 1.01 - margin and abs(p.x) < 0.2

def in_faixa(p, margin=0.0):
    return 0.92 + margin < p.z < 1.09 - margin and abs(p.x) < 0.2

def garment(name, pred, offset_fn, smooth_iter, mat):
    bm = bmesh.new()
    vmap = {}
    for poly in me.polygons:
        if poly.material_index == EYE_MAT: continue
        if all(pred(DEF[i]) for i in poly.vertices):
            vs = []
            for i in poly.vertices:
                if i not in vmap: vmap[i] = bm.verts.new(DEF[i])
                vs.append(vmap[i])
            try: bm.faces.new(vs)
            except ValueError: pass
    bm.normal_update()
    for v in bm.verts:
        v.co = v.co + v.normal * offset_fn(v.co)
    boundary = [v for v in bm.verts if v.is_boundary]
    for _ in range(smooth_iter):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.6,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
        for v in bm.verts:
            loc, nrm, dist = nearest(v.co)
            need = offset_fn(v.co) * 0.75
            if (v.co - loc).dot(nrm) < 0 or dist < need:
                v.co = loc + nrm * need
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    for p in m.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(ob)
    m.materials.append(mat)
    so = ob.modifiers.new('Spessore', 'SOLIDIFY'); so.thickness = 0.0022; so.offset = 1
    ss = ob.modifiers.new('Suddivisione', 'SUBSURF'); ss.levels = 1; ss.render_levels = 2
    return ob

def fabric(name, color, rough=0.82, sheen=0.4, stripes=False):
    m = bpy.data.materials.new(name)
    N, L = nodes_of(m)
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Roughness'].default_value = 0.4
    tc = N.new('ShaderNodeTexCoord')
    if stripes:
        w = N.new('ShaderNodeTexWave'); w.bands_direction = 'Z'; w.inputs['Scale'].default_value = 60
        w.inputs['Distortion'].default_value = 2.0
        L.new(tc.outputs['Object'], w.inputs['Vector']); src = w.outputs['Fac']
    else:
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2500
        L.new(tc.outputs['Object'], nz.inputs['Vector']); src = nz.outputs['Fac']
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15 if not stripes else 0.35
    L.new(src, bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = color
    return m

uniform = fabric('Castell_Uniform', (0.012, 0.025, 0.08, 1), 0.8, 0.15)
white = fabric('Pantaloni_bianchi', (0.86, 0.85, 0.82, 1), 0.85, 0.3)
black = fabric('Faixa_nera', (0.006, 0.006, 0.007, 1), 0.75, 0.08, stripes=True)

def shirt_off(p):
    # più ampia sul petto e sotto le ascelle: il tessuto non segue l'anatomia
    return 0.007 + 0.006 * trap(p.z, 1.12, 1.2, 1.36, 1.42) * (1 if p.y < -0.02 else 0.4) + 0.004 * (abs(p.x) > 0.19)
def trousers_off(p):
    return 0.012 + 0.022 * trap(p.z, 0.12, 0.22, 0.55, 0.78) + 0.008 * trap(p.z, 0.7, 0.78, 0.9, 1.0)
garment('Camisa', in_shirt, shirt_off, 14, uniform)
garment('Pantalons', in_trousers, trousers_off, 12, white)
garment('Faixa', in_faixa, lambda p: 0.022 + 0.004 * trap(p.z, 0.92, 0.97, 1.05, 1.09), 6, black)

# la pelle coperta dai vestiti viene nascosta (modificatore Mask, reversibile)
vg = body.vertex_groups.new(name='Coperto_dai_vestiti')
covered = [i for i, p in enumerate(DEF) if i not in eye_verts and
           (in_shirt(p, 0.025) or in_trousers(p, 0.025))]
vg.add(covered, 1.0, 'REPLACE')
mk = body.modifiers.new('Nascondi_sotto_vestiti', 'MASK'); mk.vertex_group = vg.name; mk.invert_vertex_group = True
bpy.ops.object.select_all(action='DESELECT')
# ordine: maschera prima della suddivisione
body.modifiers.move(len(body.modifiers) - 1, 0)

# ── 7. luci, camera, salvataggio ─────────────────────────────────────────
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'LIGHT': bpy.data.objects.remove(o)
def area(name, loc, energy, size, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = color
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    d = Vector((0, 0, 1.3)) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
area('Luce_principale', (-1.4, -2.2, 2.2), 260, 1.6, (1.0, 0.96, 0.92))
area('Luce_riempimento', (1.8, -1.8, 1.4), 90, 2.0, (0.92, 0.95, 1.0))
area('Luce_controluce', (0.6, 1.8, 2.3), 160, 1.0)
w = sc.world or bpy.data.worlds.new('Mondo'); sc.world = w
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.42, 0.42, 0.44, 1); bg.inputs[1].default_value = 0.6
sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
cam_data = bpy.data.cameras.new('Camera'); cam = bpy.data.objects.new('Camera', cam_data)
sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -0.95, 1.6); cam_data.lens = 85
cam.rotation_euler = (Vector((0, 0, 1.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
for im in list(bpy.data.images):
    if im.name == '.upload_preview': bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
print('OK', len(strands), 'ciocche', len(brows), 'sopracciglia', len(lashes), 'ciglia')
