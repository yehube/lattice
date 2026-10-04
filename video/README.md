# 格密码学 & 格攻击 讲解视频

`lattice_crypto.mp4` —— 1280×720 / 30fps / 约 2 分 21 秒，中文讲解（屏幕字幕即旁白）。

## 内容结构（13 个场景）

| # | 场景 | 要点 |
|---|------|------|
| 1 | 标题 | 格密码学与格攻击 |
| 2 | 什么是格 | 基向量的整数组合 = 点阵 |
| 3 | 好基 vs 坏基 | 同一个格、不同质量的基 = 陷门来源 |
| 4 | SVP / CVP | 两大困难问题，抗量子 |
| 5 | 二维约化 | Lagrange–Gauss 约化（动态缩放，真实步骤）|
| 6 | Babai 取整 | 好基解对 CVP、坏基舍入出错（真实数据）|
| 7 | LLL 算法 | 尺寸约化 + Lovász 条件，多项式时间 |
| 8 | 基向量轮廓 | log‖b*‖ 轮廓在 LLL→BKZ-10/20/40 下压平（真实 fpylll 运行）|
| 9 | 演进算法 | BKZ 滑块、枚举/筛法、progressive-BKZ、G6K/BKZ 2.0 |
| 10 | 攻击① 背包密码 | Merkle–Hellman 被 LLL（Lagarias–Odlyzko 嵌入）攻破 |
| 11 | 攻击② HNP | 有偏随机数 → BKZ 恢复 ECDSA 式签名私钥 |
| 12 | 攻击③ LWE | primal/Kannan 嵌入，还原误差 e 与三元密钥 s；与 Kyber/Dilithium 安全性的关系 |
| 13 | 小结 | 格约化：攻防同源 |

## 数据全部来自真实计算

`compute.py` 用 **fpylll** 跑真实的 LLL / BKZ，并完成三类攻击实例，结果写入 `data.json`：

- 背包：LLL 完整恢复 8 位私密子集 ✓
- HNP：40 个有偏签名，BKZ-20 直接读出私钥 `x = 48765432101` ✓
- LWE：n=10, m=24, q=127 三元密钥，primal 嵌入 BKZ-25 完整还原 (e, s) ✓
- GSO 轮廓：60 维最短向量范数 2,511,251 → 1,744（缩短约 1,440 倍）

## 复现

```bash
pip install numpy pycairo fpylll cysignals     # 依赖
python3 compute.py      # 跑真实约化/攻击 → data.json
python3 build.py        # 渲染并用 ffmpeg 编码 → lattice_crypto.mp4
```

渲染用 cairo 逐帧绘制，原始 RGB 直接管道给 ffmpeg（不落盘 PNG）。
中文字体使用 WenQuanYi Zen Hei。
