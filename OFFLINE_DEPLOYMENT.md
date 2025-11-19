# SpeakSense 离线部署指南

本文档说明如何确保 SpeakSense 系统在完全断网的环境下正常运行。

## 已实现的离线功能

### 1. 本地模型存储

所有模型都存储在项目本地，无需网络访问：

```
SpeakSense/
├── models/
│   ├── CosyVoice2-0.5B/          # CosyVoice2 TTS 模型 (~4.5GB)
│   │   ├── llm.pt                # 语言模型
│   │   ├── flow.pt               # Flow 模型
│   │   ├── hift.pt               # HiFi-GAN 模型
│   │   ├── speech_tokenizer_v2.onnx
│   │   ├── campplus.onnx         # 说话人验证
│   │   ├── CosyVoice-BlankEN/    # 英文模型
│   │   └── reference_speaker.wav # 参考音频
│   │
│   └── wetext/                   # 文本归一化模型 (~13MB)
│       ├── zh/tn/                # 中文 TN 模型
│       │   ├── tagger.fst
│       │   └── verbalizer.fst
│       ├── en/tn/                # 英文 TN 模型
│       │   ├── tagger.fst
│       │   └── verbalizer.fst
│       └── ...
│
└── third_party/
    └── CosyVoice/                # CosyVoice 代码库
```

### 2. 自动模型加载

系统会自动检测并使用本地模型：

```python
# 在 frontend.py 中
if os.path.exists(wetext_model_dir):
    # 使用本地 wetext 模型
    logging.info(f'Using local wetext model from: {wetext_model_dir}')
else:
    # 降级到在线下载（仅当本地模型不存在时）
    logging.warning('Local model not found, will download from ModelScope')
```

## 离线部署检查清单

### 步骤 1: 验证所有模型文件存在

```bash
# 检查 CosyVoice2 模型
ls -lh models/CosyVoice2-0.5B/

# 应该包含以下关键文件：
# - llm.pt (~1.9GB)
# - flow.pt (~430MB)
# - hift.pt (~80MB)
# - speech_tokenizer_v2.onnx (~473MB)
# - campplus.onnx (~27MB)

# 检查 wetext 模型
ls -lh models/wetext/

# 应该包含：
# - zh/tn/tagger.fst
# - zh/tn/verbalizer.fst
# - en/tn/tagger.fst
# - en/tn/verbalizer.fst
```

### 步骤 2: 测试离线运行

```bash
# 运行离线测试脚本
python test_offline.py

# 预期输出：
# ✓ 离线模式测试成功！
# ✓ 系统可以完全离线运行！
```

### 步骤 3: 检查日志

启动服务后，检查日志应该看到：

```
INFO Using local wetext model from: .../models/wetext
✓ CosyVoice2 model loaded successfully!
```

**不应该看到**：
```
DEBUG Starting new HTTPS connection (1): www.modelscope.cn:443
```

## 其他离线组件

### ASR (Whisper)
- Whisper 模型会自动下载到 `~/.cache/whisper/`
- 首次运行时需要网络，之后可离线使用
- 模型大小：base (~140MB)

### 向量数据库 (ChromaDB)
- 完全本地化，存储在 `services/retrieval_service/data/chromadb/`
- 无需网络连接

### Embedding 模型 (BGE)
- 模型会自动下载到 `~/.cache/huggingface/`
- 首次运行时需要网络，之后可离线使用
- 模型: BAAI/bge-small-zh-v1.5 (~100MB)

## 完全离线部署流程

如果需要在**从未联网**的服务器上部署：

### 1. 在有网络的机器上准备

```bash
# 1. 克隆项目
git clone <repository> SpeakSense

# 2. 安装依赖
cd SpeakSense
pip install -r requirements.txt

# 3. 运行一次系统，下载所有模型
python test_cosyvoice.py

# 4. 收集所有模型文件
mkdir offline-models
cp -r models/ offline-models/
cp -r ~/.cache/whisper/ offline-models/whisper/
cp -r ~/.cache/huggingface/ offline-models/huggingface/
cp -r ~/.cache/modelscope/ offline-models/modelscope/
```

### 2. 在离线服务器上部署

```bash
# 1. 复制项目和模型
scp -r SpeakSense/ offline-server:/path/
scp -r offline-models/ offline-server:/path/

# 2. 在离线服务器上恢复模型
cd /path/SpeakSense/
mkdir -p ~/.cache/
cp -r /path/offline-models/whisper ~/.cache/
cp -r /path/offline-models/huggingface ~/.cache/
cp -r /path/offline-models/modelscope ~/.cache/

# 3. 测试离线运行
python test_offline.py

# 4. 启动服务
./run_all_services.sh
```

## 验证离线运行

### 方法 1: 网络监控

```bash
# 启动服务
./run_all_services.sh

# 在另一个终端监控网络连接
lsof -i -P | grep python

# 应该只看到本地端口 (8001, 8002, 8003)，没有外部连接
```

### 方法 2: 防火墙规则

```bash
# 临时禁用外网访问
sudo pfctl -e  # macOS
# 或
sudo iptables -A OUTPUT -p tcp --dport 80 -j DROP   # Linux
sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP

# 测试系统功能
curl http://localhost:8003/admin/preview_audio?text=测试

# 恢复网络
sudo pfctl -d  # macOS
# 或
sudo iptables -F OUTPUT  # Linux
```

## 故障排查

### 问题: 仍然看到 ModelScope 连接

**症状**:
```
DEBUG Starting new HTTPS connection (1): www.modelscope.cn:443
```

**解决方案**:
1. 检查 wetext 模型是否存在：`ls models/wetext/`
2. 检查 frontend.py 是否已修改：`grep "local wetext" third_party/CosyVoice/cosyvoice/cli/frontend.py`
3. 重启服务：`./stop_all_services.sh && ./run_all_services.sh`

### 问题: 模型加载失败

**症状**:
```
FileNotFoundError: [Errno 2] No such file or directory: '.../models/wetext/zh/tn/tagger.fst'
```

**解决方案**:
1. 重新复制 wetext 模型：
   ```bash
   cp -r ~/.cache/modelscope/hub/pengzhendong/wetext models/
   ```
2. 验证文件结构：
   ```bash
   find models/wetext -name "*.fst"
   ```

## 性能优化

离线部署时的性能建议：

1. **使用 SSD**: 模型文件较大，建议使用 SSD 存储
2. **预热模型**: 首次启动会加载模型到内存，需要 20-30 秒
3. **内存要求**: 建议至少 8GB RAM（CosyVoice2 需要 ~2GB）
4. **CPU 推理**: 在 CPU 上 RTF (Real-Time Factor) 约为 5-7，即生成 1 秒音频需要 5-7 秒

## 更新说明

- **版本**: v1.0 (2025-11-19)
- **CosyVoice2 版本**: 0.5B
- **wetext 版本**: 0.0.4
- **测试状态**: ✓ 已验证完全离线运行

## 总结

✅ **已实现离线功能**:
- [x] CosyVoice2 TTS 模型本地化
- [x] wetext 文本归一化模型本地化
- [x] 自动检测并使用本地模型
- [x] 离线测试脚本验证

⚠️ **首次部署注意事项**:
- Whisper、BGE embedding 模型需要首次联网下载
- 下载后可永久离线使用
- 建议在有网络环境下完成初始化

🎯 **离线部署成功标志**:
- 日志显示 "Using local wetext model"
- 无 modelscope.cn 网络连接
- test_offline.py 测试通过
