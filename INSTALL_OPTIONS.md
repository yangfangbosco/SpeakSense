# SpeakSense 安装选项

根据你的需求选择合适的安装方式。

## 🎯 TTS 引擎对比

| 引擎 | 质量 | 速度 | 大小 | 网络 | 推荐 |
|------|------|------|------|------|------|
| **MeloTTS** | ⭐⭐⭐⭐⭐ | 快 | 中等 | 不需要 | ✅ 主要推荐 |
| PaddleSpeech | ⭐⭐⭐⭐ | 中等 | 大 (~500MB) | 不需要 | 备选 |
| Edge TTS | ⭐⭐⭐⭐⭐ | 最快 | 最小 | **需要** | 在线使用 |

---

## 安装方案

### 方案1: 完整安装（推荐）

适合：生产环境，想要所有选项

```bash
conda create -n speaksense python=3.10 -y
conda activate speaksense

# 安装所有依赖
pip install -r requirements.txt

# 安装 MeloTTS
pip install git+https://github.com/myshell-ai/MeloTTS.git
```

**包含所有TTS引擎：**
- ✅ MeloTTS（主要）
- ✅ PaddleSpeech（备选）
- ✅ Edge TTS（在线）

---

### 方案2: 精简安装（MeloTTS Only）

适合：快速部署，只需要本地TTS

**步骤1: 修改 requirements.txt**

注释掉 PaddleSpeech 相关行：

```bash
# 编辑 requirements.txt，找到这两行并注释掉：
# paddlepaddle==2.6.2
# paddlespeech==1.4.1
```

**步骤2: 安装**

```bash
conda create -n speaksense python=3.10 -y
conda activate speaksense

pip install -r requirements.txt
pip install git+https://github.com/myshell-ai/MeloTTS.git
```

**优点：**
- ⚡ 安装速度快（少 ~500MB）
- 💾 磁盘占用小
- 🎯 MeloTTS 音质更好

**配置：**

编辑 `config/config.yaml`：

```yaml
tts:
  engine: "melotts"  # 使用 MeloTTS
  language: "auto"
```

---

### 方案3: 仅在线 TTS

适合：有稳定网络，不想下载大模型

**步骤1: 修改 requirements.txt**

注释掉：

```bash
# paddlepaddle==2.6.2
# paddlespeech==1.4.1
# unidic-lite  # MeloTTS 的依赖也可以注释
```

**步骤2: 安装**

```bash
pip install -r requirements.txt
# 不需要安装 MeloTTS
```

**配置：**

```yaml
tts:
  engine: "edge-tts"  # 使用在线TTS
  language: "auto"
```

**注意：** 需要互联网连接

---

## 🔧 依赖冲突说明

### librosa 版本

- **requirements.txt 指定：** `librosa==0.8.1`
- **原因：** PaddleSpeech 1.4.1 依赖 librosa 0.8.1
- **如果不用 PaddleSpeech：** 可以升级到 `librosa==0.10.1`

修改方法：

```bash
# 如果跳过 PaddleSpeech，可以升级 librosa
pip install librosa==0.10.1
```

---

## 📦 模型大小对比

### 完整安装

```
Whisper (base):     ~150 MB
BGE Embeddings:     ~400 MB
MeloTTS:            ~200 MB
PaddleSpeech:       ~500 MB
------------------------------------
总计:               ~1.25 GB
```

### 精简安装（无 PaddleSpeech）

```
Whisper (base):     ~150 MB
BGE Embeddings:     ~400 MB
MeloTTS:            ~200 MB
------------------------------------
总计:               ~750 MB
```

### 最小安装（Edge TTS）

```
Whisper (base):     ~150 MB
BGE Embeddings:     ~400 MB
Edge TTS:           ~5 MB
------------------------------------
总计:               ~555 MB
```

---

## 🚀 快速决策树

```
需要离线运行？
├─ 是 → 需要最好的音质？
│       ├─ 是 → 方案1（完整安装）
│       └─ 否 → 方案2（MeloTTS only）
└─ 否 → 方案3（Edge TTS）
```

---

## ⚠️ 故障排查

### 问题1: PaddleSpeech 安装失败

```bash
# 解决方案：跳过 PaddleSpeech
# 注释掉 requirements.txt 中的相关行
# 使用 MeloTTS 或 Edge TTS
```

### 问题2: librosa 版本冲突

```bash
# 如果使用 PaddleSpeech
pip install librosa==0.8.1

# 如果不使用 PaddleSpeech
pip install librosa==0.10.1
```

### 问题3: MeloTTS 安装慢

```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple git+https://github.com/myshell-ai/MeloTTS.git
```

---

## 💡 生产环境推荐

**推荐配置：** 方案2（MeloTTS Only）

**原因：**
- ✅ 音质好
- ✅ 速度快
- ✅ 完全离线
- ✅ 安装简单
- ✅ 磁盘占用小

**配置文件：**

```yaml
# config/config.yaml
tts:
  engine: "melotts"
  language: "auto"
  output_dir: "./data/audio_files"

# 如果有备选需求，可以配置 Edge TTS
# tts:
#   engine: "edge-tts"
#   language: "auto"
```

---

## 📞 需要帮助？

- 完整文档：[DEPLOYMENT.md](DEPLOYMENT.md)
- 主 README：[README.md](README.md)
