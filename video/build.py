#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐帧渲染并直接管道给 ffmpeg 编码为 mp4（不落盘 PNG）。"""
import subprocess, sys, time, os
from render import P, W, H, FPS
from scenes import SCENES

OUT = os.path.join(os.path.dirname(__file__), "lattice_crypto.mp4")
total = sum(d for _,_,d in SCENES)
nframes = int(total*FPS)
print(f"scenes={len(SCENES)}  duration={total:.1f}s  frames={nframes}")

ff = subprocess.Popen([
    "ffmpeg","-y","-f","rawvideo","-pixel_format","bgr0",
    "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0",
    "-c:v","libx264","-pix_fmt","yuv420p","-crf","20",
    "-preset","medium","-movflags","+faststart", OUT],
    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

t0 = time.time(); done = 0
for name, fn, dur in SCENES:
    sf = int(dur*FPS)
    for f in range(sf):
        t = f/FPS
        p = P()
        fn(p, t, dur)
        ff.stdin.write(p.out())
        done += 1
        if done % 150 == 0:
            el = time.time()-t0
            print(f"  {done}/{nframes}  ({done/nframes*100:4.1f}%)  "
                  f"{done/el:5.1f} fps  scene={name}")
ff.stdin.close()
ff.wait()
sz = os.path.getsize(OUT)/1e6
print(f"done in {time.time()-t0:.1f}s  ->  {OUT}  ({sz:.1f} MB)")
