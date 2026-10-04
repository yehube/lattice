# -*- coding: utf-8 -*-
"""视频各场景的绘制函数。每个 scene(p, t, dur) 在局部时间 t(秒)绘制一帧。"""
import math
from render import (P, W, H, BG, BG2, FG, MUT, ACC, ACC2, GOOD, BAD, VIOLET,
                    GRIDC, DATA, ease, eio, chrome, title_card, fade)

# ---------- narration caption band (bottom) ----------------------------
def wrap(p, txt, size, maxw):
    out, cur = [], ""
    for ch in txt:
        if p.tw(cur+ch, size) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur: out.append(cur)
    return out

def caption(p, t, lines_spec):
    """lines_spec: list of (start, text). Shows the latest-started caption,
    typed-in, inside a bottom band."""
    cur = None
    for st, tx in lines_spec:
        if t >= st: cur = (st, tx)
    if not cur: return
    st, tx = cur
    size = 27
    rect_y, rect_h = H-104, 92
    p.rrect(60, rect_y, W-120, rect_h, 14, BG2, a=0.9)
    p.line(60, rect_y, 60, rect_y+rect_h, col=ACC, w=4)
    lines = wrap(p, tx, size, W-210)[:2]
    # typing reveal over 0.9s
    prog = min(1.0, (t-st)/0.9)
    total = sum(len(l) for l in lines)
    show = int(total*prog)
    y = rect_y + (38 if len(lines) > 1 else 56)
    cnt = 0
    for ln in lines:
        if cnt >= show: break
        seg = ln[:max(0, show-cnt)]
        p.text(96, y, seg, col=FG, size=size)
        cnt += len(ln); y += 38

# ---------- lattice coordinate mapper ----------------------------------
class Grid:
    def __init__(s, cx, cy, scale):
        s.cx, s.cy, s.scale = cx, cy, scale
    def px(s, x, y):
        return s.cx + x*s.scale, s.cy - y*s.scale

def draw_lattice(p, g, rng=7, col=GRIDC, dotcol=MUT, a=1.0, dotr=3):
    for i in range(-rng, rng+1):
        x1,y1 = g.px(i, -rng); x2,y2 = g.px(i, rng)
        p.line(x1,y1,x2,y2, col=col, w=1, a=0.5*a)
        x1,y1 = g.px(-rng, i); x2,y2 = g.px(rng, i)
        p.line(x1,y1,x2,y2, col=col, w=1, a=0.5*a)
    for i in range(-rng, rng+1):
        for j in range(-rng, rng+1):
            x,y = g.px(i,j); p.dot(x,y, dotr, col=dotcol, a=a)

# =======================================================================
# S1  TITLE
# =======================================================================
def s_title(p, t, dur):
    p.bg()
    g = Grid(W/2, H/2, 46)
    sp = ease(min(1.0, t/1.6))
    p.c.save(); p.c.translate(0, (1-sp)*30)
    for i in range(-9,10):
        for j in range(-6,7):
            x,y = g.px(i,j); p.dot(x,y,2.2, col=GRIDC, a=0.8*sp)
    p.c.restore()
    a = ease(min(1.0,(t-0.4)/1.0))
    # two basis vectors spinning into place
    p.arrow(*g.px(0,0), *g.px(2,1), col=ACC, w=4, a=a)
    p.arrow(*g.px(0,0), *g.px(1,2), col=ACC2, w=4, a=a)
    title_card(p, t-0.8, "格密码学 与 格攻击", "Lattice Cryptography & Lattice Attacks")
    if t > 2.8:
        p.text(W/2, H/2+96, "从 LLL 约化到 BKZ 演进算法 · 以及它们如何攻破密码",
               col=ACC, size=24, center=True, a=ease((t-2.8)/1.0))

# =======================================================================
# S2  WHAT IS A LATTICE
# =======================================================================
def s_lattice(p, t, dur):
    p.bg(); chrome(p, "什么是格 / Lattice", 0, 6, t)
    g = Grid(430, 380, 52)
    af = fade(p, t, dur)
    draw_lattice(p, g, rng=6, a=ease(min(1,t/1.0))*af)
    b1, b2 = (2,1), (1,2)
    # animate the two basis vectors, then all integer combinations lighting up
    a1 = ease(min(1,(t-1.0)/0.8))
    p.arrow(*g.px(0,0), *g.px(*b1), col=ACC, w=4, a=a1*af)
    p.arrow(*g.px(0,0), *g.px(*b2), col=ACC2, w=4, a=a1*af)
    if t > 1.2:
        p.text(*g.px(*b1), " b₁", col=ACC, size=24, bold=True, a=a1)
        p.text(*g.px(*b2), " b₂", col=ACC2, size=24, bold=True, a=a1)
    # sweep highlight of a lattice point = integer combo
    if t > 2.4:
        k = (t-2.4)*1.1
        pts = [(2,1),(3,3),(-1,1),(0,3),(-2,-1),(1,-1)]
        for idx,(i,j) in enumerate(pts):
            if k > idx+0.5:
                x,y = g.px(i,j); p.dot(x,y,7, col=GOOD, a=af)
    # right: formula
    p.text(760, 230, "格 = 一组基向量的", col=FG, size=30, a=af)
    p.text(760, 272, "所有整数线性组合", col=FG, size=30, a=af)
    p.rrect(760, 300, 420, 64, 12, BG2, a=0.8*af)
    p.text(780, 342, "Λ = { a·b₁ + c·b₂ :  a,c ∈ Z }",
           col=ACC, size=26, bold=True, a=af, mono=True)
    p.text(760, 430, "· 离散、无限、规则排列的点阵", col=MUT, size=24, a=af)
    p.text(760, 468, "· 同一个格可由不同的基生成", col=MUT, size=24, a=af)
    p.text(760, 506, "· 维度 n 可以非常高（几百~上千）", col=MUT, size=24, a=af)
    caption(p, t, [(0.3,"格，就是由几个基向量所有整数组合构成的、无限延伸的规则点阵。"),
                   (5.0,"关键在于：同一个点阵，可以用完全不同的两组基向量来描述。")])

# =======================================================================
# S3  GOOD vs BAD BASIS
# =======================================================================
def s_basis(p, t, dur):
    p.bg(); chrome(p, "好基 vs 坏基 / Basis quality", 1, 6, t)
    af = fade(p, t, dur)
    gL = Grid(360, 400, 40); gR = Grid(930, 400, 40)
    for g in (gL, gR):
        draw_lattice(p, g, rng=7, a=af)
    p.text(360, 150, "好基（短、近正交）", col=GOOD, size=26, bold=True, center=True, a=af)
    p.text(930, 150, "坏基（长、近平行）", col=BAD, size=26, bold=True, center=True, a=af)
    a1 = ease(min(1,(t-0.6)/0.8))
    p.arrow(*gL.px(0,0), *gL.px(1,0), col=GOOD, w=4, a=a1*af)
    p.arrow(*gL.px(0,0), *gL.px(0,1), col=GOOD, w=4, a=a1*af)
    # bad basis vectors (long, near-parallel) — same lattice
    a2 = ease(min(1,(t-1.4)/0.8))
    p.arrow(*gR.px(0,0), *gR.px(4,5), col=BAD, w=4, a=a2*af)
    p.arrow(*gR.px(0,0), *gR.px(5,6), col=BAD, w=4, a=a2*af)
    if t > 2.6:
        p.text(W/2, 560, "两边是同一个格 —— 但基的“质量”天差地别",
               col=FG, size=28, center=True, a=ease((t-2.6)/0.8)*af)
        p.text(W/2, 598, "密码学正是把秘密藏进“好基”，把公开信息做成“坏基”",
               col=MUT, size=23, center=True, a=ease((t-3.2)/0.8)*af)
    caption(p, t, [(0.3,"向量又短又接近垂直的，是“好基”；又长又几乎平行的，是“坏基”。"),
                   (5.0,"好基让格上的问题变容易，坏基让它们变得极难——这正是陷门的来源。")])

# =======================================================================
# S4  HARD PROBLEMS: SVP / CVP
# =======================================================================
def s_hard(p, t, dur):
    p.bg(); chrome(p, "困难问题 SVP / CVP", 2, 6, t)
    af = fade(p, t, dur)
    gL = Grid(360, 380, 46); gR = Grid(930, 380, 46)
    for g in (gL, gR):
        draw_lattice(p, g, rng=6, a=af)
    # SVP: shortest nonzero vector
    p.text(360, 140, "SVP：最短向量问题", col=ACC, size=26, bold=True, center=True, a=af)
    if t > 0.8:
        a = ease(min(1,(t-0.8)/0.8))
        p.c.save(); p.set(ACC, 0.25*af)
        x,y = gL.px(0,0); p.c.arc(x,y, 1.0*46*a, 0, 2*math.pi); p.c.fill(); p.c.restore()
        p.arrow(*gL.px(0,0), *gL.px(1,0), col=ACC, w=4, a=a*af)
        p.text(*gL.px(1,0)," 最短≠0 向量", col=ACC, size=20, a=a*af)
    # CVP: closest to a target
    p.text(930, 140, "CVP：最近向量问题", col=ACC2, size=26, bold=True, center=True, a=af)
    tx,ty = 2.4, 1.6
    if t > 1.6:
        a = ease(min(1,(t-1.6)/0.8))
        p.dot(*gR.px(tx,ty), 7, col=BAD, a=a*af)
        p.text(*gR.px(tx,ty), " 目标 t", col=BAD, size=20, a=a*af)
        p.arrow(*gR.px(2,2), *gR.px(tx,ty), col=ACC2, w=3, a=a*af)
        p.dot(*gR.px(2,2), 7, col=GOOD, a=a*af)
        p.text(*gR.px(2,2), "最近格点 ", col=GOOD, size=20, right=True, a=a*af)
    if t > 3.0:
        a = ease((t-3.0)/0.8)*af
        p.rrect(W/2-430, 512, 860, 92, 14, BG2, a=0.9*a)
        p.text(W/2, 548, "在高维里，仅凭“坏基”求 SVP / CVP 被认为是指数级困难",
               col=FG, size=26, center=True, a=a)
        p.text(W/2, 586, "—— 甚至能抵抗量子计算机，这就是“后量子密码”的根基",
               col=ACC, size=24, center=True, a=a)
    caption(p, t, [(0.3,"格上有两个核心难题：找最短的非零向量 SVP，和找离目标最近的格点 CVP。"),
                   (5.5,"维度一高，只拿坏基去解它们就是指数级困难，连量子计算机也没有已知的有效算法。")])

# =======================================================================
# S5  2D GAUSS / LAGRANGE REDUCTION  (real data: DATA['gauss'])
# =======================================================================
def s_gauss(p, t, dur):
    p.bg(); chrome(p, "二维约化 (Lagrange–Gauss)", 3, 6, t)
    af = fade(p, t, dur)
    steps = DATA["gauss"]["steps"]
    # step every 1.4s
    hold = 1.4
    n = len(steps)
    fi = t/hold
    idx = min(n-1, int(fi))
    frac = eio(min(1.0, fi-idx))
    cur = steps[idx]
    nxt = steps[min(n-1, idx+1)]
    def lerp(a,b,f): return [a[i]+(b[i]-a[i])*f for i in range(2)]
    v1 = lerp(cur[0], nxt[0], frac); v2 = lerp(cur[1], nxt[1], frac)
    # dynamic zoom so the two vectors always roughly fill the view
    mx = max(math.hypot(*v1), math.hypot(*v2), 1e-6)
    scale = 240.0 / mx
    g = Grid(430, 380, scale)
    rng = min(28, int(max(6, 320/scale)) + 1)
    draw_lattice(p, g, rng=rng, col=GRIDC, dotcol=(0.3,0.34,0.42),
                 a=0.9*af, dotr=1.6)
    p.arrow(*g.px(0,0), *g.px(*v1), col=ACC, w=4, a=af)
    p.arrow(*g.px(0,0), *g.px(*v2), col=ACC2, w=4, a=af)
    p.text(*g.px(*v1), " b₁", col=ACC, size=22, bold=True, a=af)
    p.text(*g.px(*v2), " b₂", col=ACC2, size=22, bold=True, a=af)
    # panel: operation log
    px0 = 880
    p.text(px0, 170, "约化循环", col=FG, size=30, bold=True, a=af)
    p.text(px0, 212, "① 若 b₂ 比 b₁ 短 → 交换", col=MUT, size=22, a=af)
    p.text(px0, 248, "② b₂ ← b₂ - round(μ)·b₁", col=MUT, size=22, a=af)
    p.text(px0, 284, "   μ = (b₁·b₂) / (b₁·b₁)", col=MUT, size=20, a=af, mono=True)
    p.text(px0, 320, "③ 直到 round(μ) = 0 停止", col=MUT, size=22, a=af)
    nxt_idx = min(n-1, idx)
    op = steps[nxt_idx][2]; mu = steps[nxt_idx][3]
    lab = {"start":"初始（坏基）","swap":"交换 b₁↔b₂","reduce":f"约化  μ = {mu}"}[op]
    p.rrect(px0, 360, 320, 60, 12, BG2, a=0.85*af)
    p.text(px0+20, 398, f"步骤 {idx}/{n-1} : {lab}",
           col=ACC if op!="swap" else ACC2, size=22, bold=True, a=af)
    # norms
    import math as _m
    L1 = _m.hypot(*v1); L2 = _m.hypot(*v2)
    p.text(px0, 470, f"|b₁| = {L1:6.1f}", col=ACC, size=24, a=af, mono=True)
    p.text(px0, 506, f"|b₂| = {L2:6.1f}", col=ACC2, size=24, a=af, mono=True)
    if idx >= n-1:
        p.text(px0, 560, "√ 得到最短、近正交的好基", col=GOOD, size=24, bold=True,
               a=ease((t-(n-1)*hold)/0.6)*af)
    caption(p, t, [(0.3,"二维的约化算法很直观：谁短谁当 b₁，再从长的里减掉它的整数倍，反复做。"),
                   (6.0,"几步之后，又长又斜的坏基，就被“拉直、缩短”成一组最优的好基。")])

# =======================================================================
# S6  BABAI CVP good vs bad  (real data: DATA['babai'])
# =======================================================================
def s_babai(p, t, dur):
    p.bg(); chrome(p, "用基解 CVP：Babai 取整", 4, 6, t)
    af = fade(p, t, dur)
    d = DATA["babai"]
    g = Grid(W/2, 400, 11)
    draw_lattice(p, g, rng=34, col=GRIDC, dotcol=(0.3,0.34,0.42), a=0.9*af, dotr=1.4)
    tgt = d["target"]
    p.dot(*g.px(*tgt), 7, col=VIOLET, a=af)
    p.text(*g.px(*tgt), "  目标 t", col=VIOLET, size=22, bold=True, a=af)
    # good basis parallelepiped + rounded point
    gb = d["good_basis"]
    a1 = ease(min(1,(t-0.6)/0.8))
    p.arrow(*g.px(0,0), *g.px(*gb[0]), col=GOOD, w=3, a=a1*af)
    p.arrow(*g.px(0,0), *g.px(*gb[1]), col=GOOD, w=3, a=a1*af)
    if t > 1.6:
        a = ease(min(1,(t-1.6)/0.8))*af
        gp = d["good_pt"]
        p.dot(*g.px(*gp), 8, col=GOOD, a=a)
        p.line(*g.px(*tgt), *g.px(*gp), col=GOOD, w=2, a=a, dash=[6,5])
        p.text(*g.px(*gp), "好基→正确最近点 ", col=GOOD, size=20, right=True, a=a)
    # bad basis rounded point (wrong)
    bb = d["bad_basis"]
    if t > 2.8:
        a = ease(min(1,(t-2.8)/0.8))*af
        p.arrow(*g.px(0,0), *g.px(*bb[0]), col=BAD, w=2, a=0.6*a)
        p.arrow(*g.px(0,0), *g.px(*bb[1]), col=BAD, w=2, a=0.6*a)
        bp = d["bad_pt"]
        p.dot(*g.px(*bp), 8, col=BAD, a=a)
        p.line(*g.px(*tgt), *g.px(*bp), col=BAD, w=2, a=a, dash=[6,5])
        p.text(*g.px(*bp), " 坏基→错得离谱", col=BAD, size=20, a=a)
    if t > 4.0:
        a = ease((t-4.0)/0.8)*af
        p.rrect(W/2-400, 560, 800, 48, 12, BG2, a=0.9*a)
        p.text(W/2, 592, "同一道 CVP：好基一步算对，坏基舍入到错误的格点",
               col=FG, size=26, center=True, a=a)
    caption(p, t, [(0.3,"解最近向量，最朴素的办法是把目标用基向量表出、再四舍五入。"),
                   (5.2,"好基下这一步就对；坏基下同样的四舍五入，却会落到完全错误的格点上。")])

# =======================================================================
# S7  LLL algorithm
# =======================================================================
def s_lll(p, t, dur):
    p.bg(); chrome(p, "LLL：高维的格约化", 5, 6, t)
    af = fade(p, t, dur)
    p.text(W/2, 150, "LLL 算法 (1982)", col=ACC, size=40, bold=True, center=True, a=af)
    p.text(W/2, 192, "Lenstra · Lenstra · Lovász —— 把二维约化推广到 n 维",
           col=MUT, size=24, center=True, a=af)
    rows = [
        ("① 尺寸约化", "对每个 b_i 减去前面向量的整数倍，使 Gram-Schmidt 系数 |μ| ≤ 1/2", ACC),
        ("② Lovász 条件", "若交换 b_i, b_{i+1} 能让正交化向量更“均衡”，就交换", ACC2),
        ("③ 反复进行", "直到基“既短又近正交”，整个过程是多项式时间", GOOD),
    ]
    for i,(h,b,col) in enumerate(rows):
        a = ease(min(1,(t-0.8-i*0.9)/0.8))*af
        y = 252 + i*86
        p.rrect(160, y, W-320, 76, 14, BG2, a=0.8*a)
        p.text(190, y+36, h, col=col, size=28, bold=True, a=a)
        p.text(190, y+66, b, col=FG, size=22, a=a)
    if t > 4.2:
        a = ease((t-4.2)/0.8)*af
        p.rrect(160, 524, W-320, 66, 14, (0.10,0.14,0.10), a=0.9*a)
        p.text(W/2, 566, "LLL 多项式时间内给出“足够短”的基 —— 密码分析的万能撬棍",
               col=GOOD, size=26, center=True, bold=True, a=a)
    caption(p, t, [(0.3,"LLL 把二维那套“尺寸约化 + 条件交换”推广到任意维度。"),
                   (5.0,"它在多项式时间里就能得到足够短的基，是几乎所有格攻击的第一步。")])

# =======================================================================
# S8  GSO PROFILE raw->LLL->BKZ (real data: DATA['profiles'])
# =======================================================================
def s_profile(p, t, dur):
    p.bg(); chrome(p, "约化的威力：基向量轮廓", 0, 7, t)
    af = fade(p, t, dur)
    prof = DATA["profiles"]; hn = DATA["head_norms"]; n = DATA["dim"]
    order = ["raw","LLL","BKZ-10","BKZ-20","BKZ-40"]
    names = {"raw":"原始坏基","LLL":"LLL 约化","BKZ-10":"BKZ-10",
             "BKZ-20":"BKZ-20","BKZ-40":"BKZ-40"}
    cols  = {"raw":BAD,"LLL":ACC,"BKZ-10":ACC2,"BKZ-20":VIOLET,"BKZ-40":GOOD}
    # which profiles to show: reveal one every 1.8s, interpolate transition
    hold = 2.0
    stage = min(len(order)-1, int(t/hold))
    frac = eio(min(1.0,(t/hold)-stage))
    # plot area
    X0,Y0,PW,PH = 150, 180, 680, 380
    p.rrect(X0-30, Y0-40, PW+60, PH+90, 14, BG2, a=0.5*af)
    allv = [v for k in order for v in prof[k]]
    vmin, vmax = min(allv), max(allv)
    def X(i): return X0 + i/(n-1)*PW
    def Y(v): return Y0 + PH - (v-vmin)/(vmax-vmin)*PH
    # axes
    p.line(X0, Y0, X0, Y0+PH, col=MUT, w=2, a=af)
    p.line(X0, Y0+PH, X0+PW, Y0+PH, col=MUT, w=2, a=af)
    p.text(X0-36, Y0-8, "log |b_i*|", col=MUT, size=20, a=af)
    p.text(X0+PW, Y0+PH+34, "基向量序号 i →", col=MUT, size=20, right=True, a=af)
    # faded earlier curves
    for s in range(stage):
        k = order[s]
        p.c.save(); p.set(cols[k], 0.28*af); p.c.set_line_width(2)
        for i,v in enumerate(prof[k]):
            (p.c.move_to if i==0 else p.c.line_to)(X(i), Y(v))
        p.c.stroke(); p.c.restore()
    # current curve interpolating prev->cur
    prev = prof[order[max(0,stage-1)]]; cur = prof[order[stage]]
    p.c.save(); p.set(cols[order[stage]], af); p.c.set_line_width(3.5)
    for i in range(n):
        v = prev[i] + (cur[i]-prev[i])*frac
        (p.c.move_to if i==0 else p.c.line_to)(X(i), Y(v))
    p.c.stroke(); p.c.restore()
    # legend + current head norm
    lx = 880
    p.text(lx, 180, "头部向量范数", col=FG, size=26, bold=True, a=af)
    for i,k in enumerate(order):
        on = i <= stage
        y = 230 + i*58
        p.dot(lx+10, y-8, 7, col=cols[k], a=(1 if on else .3)*af)
        p.text(lx+34, y, names[k], col=cols[k] if on else MUT,
               size=24, bold=on, a=(1 if on else .4)*af)
        p.text(lx+300, y, f"{hn[k]:>8d}", col=FG if on else MUT, size=24,
               right=True, a=(1 if on else .4)*af, mono=True)
    fac = hn["raw"]/hn["BKZ-40"]
    if stage >= len(order)-1 and frac > 0.9:
        a = ease((t-(len(order)-1)*hold-0.2)/0.6)*af
        p.text(lx, 560, f"最短向量缩短 ≈ {fac:,.0f} 倍", col=GOOD, size=26,
               bold=True, a=a)
    caption(p, t, [(0.3,"这条曲线是每个基向量正交化后的长度——坏基时陡峭倾斜。"),
                   (4.5,"LLL 把它压平一截，BKZ 用更大的“块”继续压，块越大基越短。"),
                   (8.0,"真实运行：60 维里最短向量被缩短了上千倍。")])

# =======================================================================
# S9  BKZ evolution: enumeration / sieving / progressive / G6K
# =======================================================================
def s_bkz(p, t, dur):
    p.bg(); chrome(p, "演进算法：BKZ 及其加速", 1, 7, t)
    af = fade(p, t, dur)
    p.text(W/2, 140, "BKZ = LLL + 块内求 SVP", col=ACC, size=36, bold=True, center=True, a=af)
    p.text(W/2, 182, "块大小 β 越大 → 基越短，但代价指数增长", col=MUT, size=24, center=True, a=af)
    # block sliding illustration
    y = 250
    nblk = 14
    bx0 = 200; bw = (W-400)/nblk
    beta = 4
    slide = (t*2.2) % (nblk-beta+1)
    for i in range(nblk):
        p.rrect(bx0+i*bw+3, y, bw-6, 40, 6, BG2, a=0.7*af)
    s0 = int(slide)
    for i in range(s0, min(nblk, s0+beta)):
        p.rrect(bx0+i*bw+3, y, bw-6, 40, 6, ACC, a=0.5*af)
    p.text(W/2, y+70, "↑ 在滑动的 β 维窗口内求最短向量，整条基逐步变短",
           col=MUT, size=22, center=True, a=af)
    rows = [
        ("枚举 Enumeration", "超指数 2^O(β²)，内存小；progressive-BKZ 逐步加大 β", ACC),
        ("筛法 Sieving", "单指数 2^O(β) 时间与内存；大 β 下更快", ACC2),
        ("G6K / BKZ 2.0", "现代实现：剪枝枚举 + GPU 筛法，刷新格挑战记录", GOOD),
    ]
    for i,(h,b,col) in enumerate(rows):
        a = ease(min(1,(t-1.2-i*0.9)/0.8))*af
        yy = 360 + i*82
        p.rrect(160, yy, W-320, 70, 12, BG2, a=0.8*a)
        p.text(190, yy+32, h, col=col, size=26, bold=True, a=a)
        p.text(190, yy+60, b, col=FG, size=21, a=a)
    caption(p, t, [(0.3,"BKZ 在 LLL 外面套一层：在每个 β 维小块里精确求最短向量，再滑动窗口。"),
                   (5.0,"求块内 SVP 靠枚举或筛法；progressive-BKZ、G6K 这些演进算法不断把可攻破的维度推高。")])

# =======================================================================
# S10  KNAPSACK attack (real data)
# =======================================================================
def s_knap(p, t, dur):
    p.bg(); chrome(p, "攻击①  背包密码 (Merkle–Hellman)", 2, 7, t)
    af = fade(p, t, dur)
    d = DATA["knapsack"]
    p.text(90, 150, "公开背包  (坏基里的难题)", col=ACC, size=26, bold=True, a=af)
    pub = d["pub"]; bits = d["bits"]; rec = d["recovered"]
    # show public key
    pstr = "[ " + "  ".join(f"{v}" for v in pub) + " ]"
    p.text(90, 196, "pub = "+pstr, col=FG, size=22, a=af, mono=True)
    p.text(90, 236, f"公开和 S = {d['S']}", col=ACC2, size=23, a=af, mono=True)
    p.text(90, 272, "问题：哪些元素相加 = S ？（子集和，NP 难）",
           col=MUT, size=22, a=af)
    # lattice embedding box
    a2 = ease(min(1,(t-1.4)/0.8))*af
    p.rrect(90, 310, 520, 150, 14, BG2, a=0.8*a2)
    p.text(110, 348, "Lagarias–Odlyzko 嵌入：", col=ACC, size=24, bold=True, a=a2)
    p.text(110, 384, "把 (pub, S) 排成一个格的基，", col=FG, size=22, a=a2)
    p.text(110, 416, "01 选择向量 = 格中一个异常短的向量", col=FG, size=22, a=a2)
    p.text(110, 448, "→ 交给 LLL", col=GOOD, size=22, bold=True, a=a2)
    # LLL machine + recovered bits
    if t > 3.0:
        a = ease(min(1,(t-3.0)/0.8))*af
        p.arrow(640, 400, 740, 400, col=GOOD, w=4, a=a)
        p.text(690, 382, "LLL", col=GOOD, size=22, bold=True, center=True, a=a)
        bx = 780
        for i,b in enumerate(rec):
            on = (t-3.6) > i*0.18
            col = GOOD if (on and b) else (BG2 if on else MUT)
            p.rrect(bx+i*54, 360, 46, 60, 8, col, a=(1 if on else .3)*af)
            if on:
                p.text(bx+i*54+23, 400, str(b), col=FG if b else MUT,
                       size=30, bold=True, center=True, a=af)
        p.text(bx, 340, "恢复出的 01 选择", col=GOOD, size=22, bold=True, a=a)
    if t > 5.4:
        ok = rec == bits
        a = ease((t-5.4)/0.8)*af
        p.text(90, 540, ("√ 真实运行：LLL 完全恢复私密子集 —— 背包密码就此被攻破"
                         if ok else "结果见上"),
               col=GOOD, size=26, bold=True, a=a)
    caption(p, t, [(0.3,"80 年代的背包密码，把子集和难题当陷门——看似是 NP 难问题。"),
                   (4.0,"但把公钥嵌成一个格，正确答案恰好是其中一个超短向量。"),
                   (7.0,"LLL 一跑，私密的 0/1 选择被原样还原。真实数据，攻破成功。")])

# =======================================================================
# S11  HNP / biased-nonce attack (real data)
# =======================================================================
def s_hnp(p, t, dur):
    p.bg(); chrome(p, "攻击②  有偏随机数 → 签名私钥 (HNP)", 3, 7, t)
    af = fade(p, t, dur)
    d = DATA["hnp"]
    p.text(90, 150, "隐藏数问题 Hidden Number Problem", col=ACC, size=26, bold=True, a=af)
    p.text(90, 192, "签名：s = k^-1 (h + r·x)  mod n", col=FG, size=24, a=af, mono=True)
    p.text(90, 230, "若每次随机数 k 的高位泄露/有偏（k 偏小）……",
           col=ACC2, size=23, a=af)
    # biased nonce bars
    a1 = ease(min(1,(t-1.0)/0.8))*af
    p.text(90, 290, f"已知每个 k 的高 {d['known_top']} 位 = 0", col=MUT, size=22, a=a1)
    bx, by = 90, 320
    import random as _r
    _r.seed(3)
    for i in range(16):
        full = 150
        lead = full*d['known_top']/37
        p.rrect(bx+i*34, by, 26, full, 4, BG2, a=0.7*af)
        # zero high bits (leaked) shown dim, random low bits bright
        lo = full-lead
        p.rrect(bx+i*34, by+lead, 26, lo*(_r.uniform(.4,1)), 4, ACC2, a=af)
        p.rrect(bx+i*34, by, 26, lead, 4, BAD, a=0.5*af)
    p.text(bx, by+full+34, "红=已知为0的高位   橙=未知低位（k 偏小）",
           col=MUT, size=20, a=a1)
    # lattice -> key
    if t > 2.8:
        a = ease(min(1,(t-2.8)/0.8))*af
        p.rrect(700, 300, 490, 160, 14, BG2, a=0.82*a)
        p.text(724, 340, f"把 {d['num_sigs']} 个签名排成一个格", col=ACC, size=24, bold=True, a=a)
        p.text(724, 376, "私钥 x 藏在一个短向量里", col=FG, size=23, a=a)
        p.text(724, 412, "→ LLL + BKZ 约化", col=GOOD, size=23, bold=True, a=a)
        p.text(724, 446, "→ 直接读出私钥 x", col=GOOD, size=23, bold=True, a=a)
    if t > 4.6:
        a = ease((t-4.6)/0.8)*af
        p.rrect(90, 512, W-180, 92, 14, (0.10,0.14,0.10), a=0.92*a)
        p.text(W/2, 546, "真实运行结果", col=MUT, size=21, center=True, a=a)
        p.text(W/2, 586, f"恢复私钥 x = {d['recovered']}  "
               + ("√ 与真实私钥完全一致" if d["success"] else ""),
               col=GOOD, size=28, bold=True, center=True, a=a, mono=True)
    caption(p, t, [(0.3,"ECDSA 这类签名里，每次都要一个一次性随机数 k。"),
                   (3.2,"只要 k 稍有偏差——比如高位泄露、k 偏小——几十个签名排成一个格，"),
                   (6.4,"私钥就成了格里的一个短向量，BKZ 约化后被直接读出。这正是现实中的真实漏洞。")])

# =======================================================================
# S12  LWE primal attack & PQC relevance (real data)
# =======================================================================
def s_lwe(p, t, dur):
    p.bg(); chrome(p, "攻击③  LWE 与后量子密码", 4, 7, t)
    af = fade(p, t, dur)
    d = DATA["lwe"]
    p.text(90, 150, "LWE：带误差的学习问题", col=ACC, size=26, bold=True, a=af)
    p.text(90, 192, "b = A·s + e  (mod q)   —— e 是小误差",
           col=FG, size=24, a=af, mono=True)
    p.text(90, 230, "Kyber / Dilithium 等后量子标准的安全基石",
           col=ACC2, size=23, a=af)
    a1 = ease(min(1,(t-1.2)/0.8))*af
    p.rrect(90, 270, 540, 180, 14, BG2, a=0.8*a1)
    p.text(112, 308, "primal 攻击 (Kannan 嵌入)：", col=ACC, size=24, bold=True, a=a1)
    p.text(112, 344, "把 (A, b) 嵌成一个格，", col=FG, size=22, a=a1)
    p.text(112, 376, "误差向量 e 就是其中的最短向量，", col=FG, size=22, a=a1)
    p.text(112, 408, "→ BKZ 约化即可还原 e 与密钥 s", col=GOOD, size=22, bold=True, a=a1)
    if t > 2.8:
        a = ease(min(1,(t-2.8)/0.8))*af
        p.rrect(680, 270, 510, 180, 14, (0.10,0.14,0.10), a=0.88*a)
        p.text(702, 306, "真实运行 (n=%d, m=%d, q=%d, 三元密钥)" % (d["n"], d["m"], d["q"]),
               col=MUT, size=21, a=a)
        p.text(702, 344, f"目标 |(e,s)| 范数 = {d['true_err_norm']}", col=FG, size=23, a=a, mono=True)
        p.text(702, 380, f"约化找到的范数   = {d['found_norm']}", col=GOOD, size=23, a=a, mono=True)
        ok = d.get("success", abs(d['true_err_norm']-d['found_norm']) < 1e-6)
        p.text(702, 420, "√ 完整还原误差 e 与密钥 s" if ok else "→ 找到同等短向量",
               col=GOOD, size=23, bold=True, a=a)
    if t > 4.6:
        a = ease((t-4.6)/0.8)*af
        p.rrect(90, 498, W-180, 100, 14, BG2, a=0.9*a)
        p.text(W/2, 534, "于是“格约化”既是攻击武器，也是安全标尺：",
               col=FG, size=25, center=True, a=a)
        p.text(W/2, 574, "Kyber/Dilithium 的参数，正是按 BKZ 攻破所需的块大小 β 来选的",
               col=ACC, size=24, center=True, a=a)
    caption(p, t, [(0.3,"今天的后量子标准 Kyber、Dilithium 都建立在 LWE 难题上。"),
                   (3.4,"攻击它同样靠格：把方程嵌成格，小误差 e 就是最短向量，BKZ 去找。"),
                   (6.6,"所以参数安全性，恰恰用“攻破需要多大的 BKZ 块”来衡量——攻防同源。")])

# =======================================================================
# S13  SUMMARY
# =======================================================================
def s_end(p, t, dur):
    p.bg()
    af = fade(p, t, dur, fin=0.6, fout=0.8)
    p.text(W/2, 130, "一条主线", col=ACC, size=30, bold=True, center=True, a=af)
    items = [
        ("格 & 好基/坏基", "密码学的陷门：藏起好基，公开坏基", ACC),
        ("SVP / CVP", "高维下的指数级难题，抗量子", VIOLET),
        ("LLL → BKZ → G6K", "约化/演进算法：把坏基一步步变短", ACC2),
        ("背包 · HNP · LWE", "同一把撬棍，攻破经典与后量子密码", GOOD),
    ]
    for i,(h,b,col) in enumerate(items):
        a = ease(min(1,(t-0.6-i*0.6)/0.8))*af
        y = 210 + i*96
        p.dot(220, y+4, 8, col=col, a=a)
        p.text(250, y+12, h, col=col, size=30, bold=True, a=a)
        p.text(560, y+12, b, col=FG, size=24, a=a)
    if t > 3.6:
        a = ease((t-3.6)/0.8)*af
        p.text(W/2, 630, "格约化 —— 密码世界里攻与防的同一把钥匙",
               col=FG, size=30, bold=True, center=True, a=a)
    if t > 5.0:
        p.text(W/2, 676, "感谢观看", col=MUT, size=22, center=True,
               a=ease((t-5.0)/0.8)*af)

SCENES = [
    ("title",   s_title,   6.0),
    ("lattice", s_lattice, 11.0),
    ("basis",   s_basis,   10.0),
    ("hard",    s_hard,    11.0),
    ("gauss",   s_gauss,   13.0),
    ("babai",   s_babai,   11.0),
    ("lll",     s_lll,     11.0),
    ("profile", s_profile, 14.0),
    ("bkz",     s_bkz,     11.0),
    ("knap",    s_knap,    12.0),
    ("hnp",     s_hnp,     12.0),
    ("lwe",     s_lwe,     12.0),
    ("end",     s_end,     7.0),
]
