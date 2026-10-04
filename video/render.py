#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格密码学 & 格攻击 讲解视频渲染器。
用 cairo 逐帧绘制，原始 RGB 直接管道给 ffmpeg 编码，不落盘 PNG。
所有数值来自 data.json（compute.py 跑出的真实约化/攻击结果）。
"""
import cairo, math, json, sys, subprocess, os

W, H, FPS = 1280, 720, 30
DATA = json.load(open(os.path.join(os.path.dirname(__file__), "data.json")))

# ---- palette (dark, high-contrast) ------------------------------------
BG      = (0.047, 0.055, 0.086)
BG2     = (0.078, 0.090, 0.133)
FG      = (0.901, 0.925, 0.968)
MUT     = (0.52, 0.57, 0.66)
ACC     = (0.38, 0.76, 1.00)   # cyan-blue
ACC2    = (1.00, 0.72, 0.30)   # amber
GOOD    = (0.42, 0.86, 0.55)   # green
BAD     = (0.98, 0.45, 0.52)   # red
VIOLET  = (0.72, 0.56, 1.00)
GRIDC   = (0.20, 0.24, 0.32)

FONT = "WenQuanYi Zen Hei"
MONO = "WenQuanYi Zen Hei Mono"

def ease(t):                      # smoothstep
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
def eio(t):                       # ease-in-out cubic
    t = max(0.0, min(1.0, t))
    return 4*t*t*t if t < .5 else 1-((-2*t+2)**3)/2

# ---------------------------------------------------------------- Painter
class P:
    def __init__(s):
        s.surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        s.c = cairo.Context(s.surf)
    def bg(s, grad=True):
        c = s.c
        if grad:
            g = cairo.LinearGradient(0, 0, 0, H)
            g.add_color_stop_rgb(0, *BG2); g.add_color_stop_rgb(1, *BG)
            c.set_source(g)
        else:
            c.set_source_rgb(*BG)
        c.rectangle(0, 0, W, H); c.fill()
    def set(s, col, a=1.0):
        s.c.set_source_rgba(col[0], col[1], col[2], a)
    def font(s, size, bold=False, mono=False):
        s.c.select_font_face(MONO if mono else FONT, cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        s.c.set_font_size(size)
    def text(s, x, y, txt, col=FG, size=28, bold=False, center=False,
             right=False, a=1.0, mono=False):
        s.font(size, bold, mono); s.set(col, a)
        xb, yb, tw, th, _, _ = s.c.text_extents(txt)
        tx = x - tw/2 - xb if center else (x - tw - xb if right else x)
        s.c.move_to(tx, y); s.c.show_text(txt)
        return tw
    def tw(s, txt, size, bold=False, mono=False):
        s.font(size, bold, mono); return s.c.text_extents(txt)[2]
    def line(s, x1, y1, x2, y2, col=FG, w=2, a=1.0, dash=None):
        s.c.save(); s.set(col, a); s.c.set_line_width(w)
        if dash: s.c.set_dash(dash)
        s.c.move_to(x1, y1); s.c.line_to(x2, y2); s.c.stroke(); s.c.restore()
    def arrow(s, x1, y1, x2, y2, col=ACC, w=3, a=1.0, head=11):
        s.c.save(); s.set(col, a); s.c.set_line_width(w)
        s.c.move_to(x1, y1); s.c.line_to(x2, y2); s.c.stroke()
        ang = math.atan2(y2-y1, x2-x1)
        for d in (-0.42, 0.42):
            s.c.move_to(x2, y2)
            s.c.line_to(x2-head*math.cos(ang+d), y2-head*math.sin(ang+d))
        s.c.stroke(); s.c.restore()
    def dot(s, x, y, r, col=FG, a=1.0):
        s.set(col, a); s.c.arc(x, y, r, 0, 2*math.pi); s.c.fill()
    def rrect(s, x, y, w, h, r, col, a=1.0, fill=True, lw=2):
        c = s.c; c.save()
        c.new_sub_path()
        c.arc(x+w-r, y+r, r, -math.pi/2, 0)
        c.arc(x+w-r, y+h-r, r, 0, math.pi/2)
        c.arc(x+r, y+h-r, r, math.pi/2, math.pi)
        c.arc(x+r, y+r, r, math.pi, 1.5*math.pi)
        c.close_path(); s.set(col, a)
        if fill: c.fill()
        else: c.set_line_width(lw); c.stroke()
        c.restore()
    def out(s):
        s.surf.flush()
        return bytes(s.surf.get_data())

# progress-bar footer + small scene label
def chrome(p, label, sub_idx, total, t_global):
    p.text(70, 70, label, col=ACC, size=26, bold=True)
    p.line(70, 88, 70 + p.tw(label, 26, True), 88, col=ACC, w=3)
    # section dots
    x0 = W - 70 - (total-1)*26
    for i in range(total):
        on = i == sub_idx
        p.dot(x0 + i*26, 70, 6 if on else 4,
              col=ACC if on else MUT, a=1 if on else .5)

def title_card(p, t, zh, en, col=FG):
    a = ease(t/0.6)
    p.text(W/2, H/2-20, zh, col=col, size=64, bold=True, center=True, a=a)
    a2 = ease((t-0.3)/0.6)
    p.text(W/2, H/2+42, en, col=MUT, size=26, center=True, a=a2)

# fade helper for whole-scene in/out
def fade(p, t, dur, fin=0.5, fout=0.5):
    if t < fin: return ease(t/fin)
    if t > dur-fout: return ease((dur-t)/fout)
    return 1.0
