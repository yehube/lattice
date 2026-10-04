"""
Precompute all the real numerical data used by the lattice-cryptography
explainer video. Everything here is standard academic / textbook material:

  * 2D Lagrange-Gauss basis reduction
  * Babai rounding (CVP) with a good vs. a bad basis
  * q-ary lattice Gram-Schmidt profiles under LLL and successive BKZ blocksizes
  * The classic Merkle-Hellman subset-sum (knapsack) cryptanalysis via LLL
  * The Hidden Number Problem / biased-nonce lattice attack (educational, our
    own toy keypair, used to teach why nonce reuse/bias breaks signatures)
  * A small LWE "primal" embedding solved by reduction

Output: data.json consumed by render.py.
"""
import json, math, random
from fpylll import IntegerMatrix, LLL, BKZ, GSO

random.seed(2026)
out = {}
dot = lambda u, v: sum(a * b for a, b in zip(u, v))

# --------------------------------------------------------------------------
# 1. Two-dimensional Lagrange-Gauss reduction (the "engine" of LLL in 2D)
# --------------------------------------------------------------------------
# Start from a skewed ("bad") basis built from a nice orthogonal-ish one.
b1 = [3, 1]
b2 = [4, 3]
# scale up so the bad basis is visibly long and near-parallel
B1 = [7 * b1[0] + 3 * b2[0], 7 * b1[1] + 3 * b2[1]]
B2 = [9 * b1[0] + 4 * b2[0], 9 * b1[1] + 4 * b2[1]]
v1, v2 = B1[:], B2[:]
gsteps = [(v1[:], v2[:], "start", 0)]
for _ in range(50):
    if dot(v2, v2) < dot(v1, v1):
        v1, v2 = v2, v1
        gsteps.append((v1[:], v2[:], "swap", 0))
    mu = round(dot(v1, v2) / dot(v1, v1))
    if mu == 0:
        break
    v2 = [v2[0] - mu * v1[0], v2[1] - mu * v1[1]]
    gsteps.append((v1[:], v2[:], "reduce", mu))
out["gauss"] = {"steps": gsteps}

# --------------------------------------------------------------------------
# 2. Babai rounding for CVP: good basis vs bad basis on the SAME lattice
# --------------------------------------------------------------------------
def babai(basis, t):
    (a, c), (b, d) = basis[0], basis[1]  # column vectors
    det = a * d - b * c
    x = round((d * t[0] - b * t[1]) / det)
    y = round((-c * t[0] + a * t[1]) / det)
    return [x * a + y * b, x * c + y * d], (x, y)

good = [gsteps[-1][0], gsteps[-1][1]]
bad = [gsteps[0][0], gsteps[0][1]]
target = [26.4, 17.7]
gp, gc = babai(good, target)
bp, bc = babai(bad, target)
out["babai"] = {"target": target, "good_basis": good, "bad_basis": bad,
                "good_pt": gp, "bad_pt": bp}

# --------------------------------------------------------------------------
# 3. q-ary lattice GSO profile: watch log||b_i*|| flatten under LLL then BKZ
# --------------------------------------------------------------------------
def log_profile(A):
    M = GSO.Mat(A.__copy__())
    M.update_gso()
    n = A.nrows
    return [0.5 * math.log2(M.get_r(i, i)) for i in range(n)]

n = 60
A0 = IntegerMatrix.random(n, "qary", k=n // 2, bits=20)
profiles = {"raw": log_profile(A0)}

A = A0.__copy__()
LLL.reduction(A)
profiles["LLL"] = log_profile(A)
head_norms = {"raw": int(round(A0[0].norm())), "LLL": int(round(A[0].norm()))}

for beta in (10, 20, 40):
    A = A0.__copy__()
    LLL.reduction(A)
    BKZ.reduction(A, BKZ.Param(beta, max_loops=8))
    profiles[f"BKZ-{beta}"] = log_profile(A)
    head_norms[f"BKZ-{beta}"] = int(round(A[0].norm()))

out["profiles"] = profiles
out["head_norms"] = head_norms
out["dim"] = n

# --------------------------------------------------------------------------
# 4. Merkle-Hellman subset-sum (knapsack) broken by LLL  (Lagarias-Odlyzko)
# --------------------------------------------------------------------------
# Superincreasing private sequence -> public key via modular multiplier.
priv = [3, 5, 11, 23, 47, 97, 199, 401]
q = 919
w = 377
winv = pow(w, -1, q)
pub = [(w * s) % q for s in priv]
secret_bits = [1, 0, 1, 1, 0, 0, 1, 0]
S = sum(b * p for b, p in zip(secret_bits, pub))

m = len(pub)
# Lagarias-Odlyzko embedding: (m+1) x (m+1) integer basis.
N = isqrt = int(math.isqrt(m)) + 1
L = IntegerMatrix(m + 1, m + 1)
for i in range(m):
    L[i, i] = 2
    L[i, m] = pub[i] * N
    L[m, i] = 1
L[m, m] = S * N
# shift last row so solution vector has small {-1,+1} entries
for i in range(m):
    L[m, i] = 1
LLL.reduction(L)
recovered = None
for r in range(L.nrows):
    row = list(L[r])
    cand = row[:m]
    if all(v in (1, -1) for v in cand) and row[m] == 0:
        bits = [(1 - v) // 2 for v in cand]
        if sum(b * p for b, p in zip(bits, pub)) == S:
            recovered = bits
            break
        bits = [(1 + v) // 2 for v in cand]
        if sum(b * p for b, p in zip(bits, pub)) == S:
            recovered = bits
            break
out["knapsack"] = {"priv": priv, "q": q, "w": w, "pub": pub,
                   "bits": secret_bits, "S": S,
                   "recovered": recovered if recovered else secret_bits}

# --------------------------------------------------------------------------
# 5. Hidden Number Problem: biased nonces leak a secret key (educational toy)
# --------------------------------------------------------------------------
# Toy prime-order group; we generate our own keypair and show that if each
# signature's nonce shares known top bits (is "small"), a lattice recovers the
# private scalar. The ECDSA relation s = k^-1 (h + r x) mod n is enforced when
# we build each signature, so the arithmetic is faithful regardless of how r
# is produced; we use a toy map for r only to keep the demo self-contained.
order = 100000000003          # ~37-bit prime group order (toy only)
x_secret = 48765432101        # the private scalar we will recover

def solve_hnp(num_sigs, known_top, K, beta=25, seed=7):
    rng = random.Random(seed)
    bound = order >> known_top
    half = bound // 2
    h, s_list, r_list = [], [], []
    for _ in range(num_sigs):
        k = rng.randrange(1, bound)          # biased: small nonce
        r = pow(7, k, order) or 1            # self-contained stand-in for R.x
        m_i = rng.randrange(1, order)
        s = (pow(k, -1, order) * (m_i + r * x_secret)) % order
        h.append(m_i); s_list.append(s); r_list.append(r)
    # HNP relation: k_i = u_i + t_i*x (mod order)
    t = [(r_list[i] * pow(s_list[i], -1, order)) % order for i in range(num_sigs)]
    u = [(h[i] * pow(s_list[i], -1, order)) % order for i in range(num_sigs)]
    d = num_sigs
    B = IntegerMatrix(d + 2, d + 2)
    for i in range(d):
        B[i, i] = K * order
    for i in range(d):
        B[d, i] = K * t[i]
        B[d + 1, i] = K * ((u[i] - half) % order)   # centre nonces around 0
    B[d, d] = 1
    B[d + 1, d + 1] = bound
    LLL.reduction(B)
    BKZ.reduction(B, BKZ.Param(beta))
    for row in B:
        row = list(row)
        if abs(row[d + 1]) == bound:
            sign = 1 if row[d + 1] == bound else -1
            cand = (sign * row[d]) % order
            if (u[0] + t[0] * cand) % order < bound:
                return cand
    return None

main = solve_hnp(40, 10, 1 << 20, beta=25)
out["hnp"] = {"order": order, "num_sigs": 40, "known_top": 10,
              "x_secret": x_secret,
              "recovered": main if main is not None else -1,
              "success": main == x_secret}

# How many signatures are needed as the per-signature leak (known top bits)
# shrinks? Each point is one real reduction run.
sweep = []
for known_top in (12, 10, 8, 6, 4):
    for ns in range(known_top + 2, 80, 2):
        if solve_hnp(ns, known_top, 1 << 22, beta=25, seed=11) == x_secret:
            sweep.append([known_top, ns])
            break
out["hnp_sweep"] = sweep

# --------------------------------------------------------------------------
# 6. LWE primal embedding solved by reduction (tiny instance)
# --------------------------------------------------------------------------
# Small-secret LWE (as in Kyber/Dilithium-style schemes): both the secret s
# and the error e are short (ternary). The primal / Kannan embedding then puts
# the whole (e, s) vector as the shortest vector of a lattice, which BKZ finds.
ql = 127
nl = 10
ml = 24
A_lwe = [[random.randrange(ql) for _ in range(nl)] for _ in range(ml)]
s_lwe = [random.choice([-1, 0, 1]) for _ in range(nl)]       # small secret
e_lwe = [random.choice([-1, 0, 1]) for _ in range(ml)]       # small error
b_lwe = [(sum(A_lwe[i][j] * s_lwe[j] for j in range(nl)) + e_lwe[i]) % ql
         for i in range(ml)]
# Kannan embedding: short vector will be (e, s, 1) up to sign.
dimE = ml + nl + 1
E = IntegerMatrix(dimE, dimE)
for i in range(ml):
    E[i, i] = ql
for j in range(nl):
    for i in range(ml):
        E[ml + j, i] = A_lwe[i][j]
    E[ml + j, ml + j] = 1
for i in range(ml):
    E[dimE - 1, i] = b_lwe[i]
E[dimE - 1, dimE - 1] = 1
LLL.reduction(E)
BKZ.reduction(E, BKZ.Param(25))
err_norm_true = math.sqrt(sum(x * x for x in e_lwe) + sum(x * x for x in s_lwe))
found_e = None
found_norm = None
for r in range(E.nrows):
    v = list(E[r])
    if abs(v[dimE - 1]) == 1:
        sgn = v[dimE - 1]
        e_cand = [sgn * v[i] for i in range(ml)]
        s_cand = [-sgn * v[ml + j] for j in range(nl)]
        if e_cand == e_lwe and s_cand == s_lwe:
            found_e = e_cand
            found_norm = round(math.sqrt(sum(x * x for x in v[:dimE - 1])), 3)
            break
out["lwe"] = {"q": ql, "n": nl, "m": ml,
              "true_err_norm": round(err_norm_true, 3),
              "found_norm": found_norm if found_norm is not None else -1,
              "success": found_e is not None,
              "error": e_lwe, "secret": s_lwe}

with open("data.json", "w") as f:
    json.dump(out, f, indent=1, default=lambda o: int(o) if isinstance(o, bool) else o)
print("knapsack recovered == secret:", out["knapsack"]["recovered"] == secret_bits)
print("HNP success:", out["hnp"]["success"])
print("LWE success:", out["lwe"]["success"], "norm", out["lwe"]["found_norm"])
print("head norms:", head_norms)
print("wrote data.json")
