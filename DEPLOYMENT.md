# SpeakSense 服务器部署指南

本文档提供完整的服务器部署步骤，适用于从开发环境迁移到生产服务器。

## 📋 前置要求

- **操作系统**: Linux (Ubuntu 20.04+ 推荐) 或 macOS
- **Python**: 3.10
- **Conda**: Anaconda 或 Miniconda
- **内存**: 至少 8GB RAM
- **磁盘**: 至少 20GB 可用空间（用于模型文件）
- **网络**: 可访问 Hugging Face 和 GitHub（首次安装时需要下载模型）

## 🚀 快速部署

### 步骤 1: 上传项目文件

```bash
# 在本地机器上打包项目（排除不需要的文件）
cd /path/to/SpeakSense
tar -czf speaksense.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='logs/*.log' \
  --exclude='data/faq.db' \
  --exclude='data/audio_files/*' \
  --exclude='data/chromadb/*' \
  --exclude='venv' \
  --exclude='*.egg-info' \
  .

# 上传到服务器
scp speaksense.tar.gz user@your-server:/path/to/deployment/

# 在服务器上解压
ssh user@your-server
cd /path/to/deployment/
tar -xzf speaksense.tar.gz
cd SpeakSense
```

### 步骤 2: 运行自动部署脚本

```bash
# 给部署脚本添加执行权限
chmod +x deploy/*.sh

# 运行完整部署流程
./deploy/deploy.sh
```

部署脚本会自动完成：
- ✅ 创建 Conda 环境
- ✅ 安装所有依赖
- ✅ 下载所需模型
- ✅ 配置服务器IP
- ✅ 初始化数据库
- ✅ 启动所有服务
- ✅ 运行健康检查

---

## 📝 手动部署（分步骤）

如果自动部署遇到问题，可以按以下步骤手动部署：

### 1. 创建 Conda 环境

```bash
# 创建新环境
conda create -n speaksense python=3.10 -y
conda activate speaksense
```

### 2. 安装依赖

```bash
# 基础依赖
pip install -r requirements.txt

# 安装 MeloTTS
pip install git+https://github.com/myshell-ai/MeloTTS.git

# 验证安装
python -c "import torch; import whisper; import chromadb; print('Dependencies OK')"
```

### 3. 下载模型

```bash
# 下载 Whisper 模型
python -c "import whisper; whisper.load_model('base')"

# 下载 BGE 嵌入模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')"

# 下载 MeloTTS 模型
python -c "from melo.api import TTS; TTS(language='ZH')"
```

### 4. 配置服务器 IP

```bash
# 获取服务器IP
hostname -I | awk '{print $1}'

# 方式1: 使用环境变量
export SERVER_IP=your.server.ip

# 方式2: 编辑配置文件
vim config/config.yaml
# 修改 api_base_url 为你的服务器IP
```

### 5. 启动服务

```bash
# 启动所有服务
./run_all_services.sh

# 或者使用指定IP启动
SERVER_IP=192.168.1.100 ./run_all_services.sh
```

### 6. 验证部署

```bash
# 检查服务状态
curl http://localhost:8001/health  # ASR Service
curl http://localhost:8002/health  # Retrieval Service
curl http://localhost:8003/health  # Admin Service

# 测试完整流程
./deploy/test_deployment.sh
```

---

## 🔧 配置说明

### config/config.yaml

关键配置项：

```yaml
# API配置 - 修改为服务器IP
api_base_url: "http://YOUR_SERVER_IP"

# 数据库配置
database:
  path: "./data/faq.db"

# TTS配置
tts:
  engine: "melotts"  # melotts, paddlespeech, edge
  language: "auto"   # auto, zh, en
  output_dir: "./data/audio_files"

# 嵌入模型配置
embeddings:
  model_name: "BAAI/bge-small-zh-v1.5"
  device: "cpu"  # 或 "cuda" 如果有GPU

# ASR配置
asr:
  model_name: "base"  # tiny, base, small, medium, large
  language: "zh"      # zh, en, auto
```

### 端口配置

确保以下端口在防火墙中开放：

- `8001`: ASR 服务
- `8002`: Retrieval 服务
- `8003`: Admin 服务
- `8080`: 测试门户（开发用）
- `8090`: 生产管理门户

```bash
# Ubuntu/Debian 防火墙配置
sudo ufw allow 8001:8003/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 8090/tcp
```

---

## 📊 服务管理

### 启动服务

```bash
# 启动所有服务
./run_all_services.sh

# 使用指定IP启动
SERVER_IP=192.168.1.100 ./run_all_services.sh
```

### 停止服务

```bash
# 停止所有服务
./stop_all_services.sh
```

### 重启服务

```bash
# 创建重启脚本
./restart_all_services.sh
```

### 查看日志

```bash
# 实时查看所有日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/asr_service.log
tail -f logs/retrieval_service.log
tail -f logs/admin_service.log
```

---

## 🔍 故障排查

### 问题 1: 模型下载失败

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install -r requirements.txt
```

### 问题 2: 端口被占用

```bash
# 查找占用端口的进程
lsof -i:8001
lsof -i:8002
lsof -i:8003

# 强制停止
./stop_all_services.sh
```

### 问题 3: 依赖冲突

```bash
# 删除并重建环境
conda deactivate
conda remove -n speaksense --all -y
conda create -n speaksense python=3.10 -y
conda activate speaksense
pip install -r requirements.txt
```

### 问题 4: 数据库锁定

```bash
# 停止所有服务
./stop_all_services.sh

# 等待几秒
sleep 5

# 重启服务
./run_all_services.sh
```

---

## 🎯 生产环境建议

### 1. 使用 systemd 管理服务

创建系统服务文件确保开机自启：

```bash
# 参考 deploy/systemd/ 目录下的示例文件
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable speaksense-asr
sudo systemctl enable speaksense-retrieval
sudo systemctl enable speaksense-admin
```

### 2. 配置反向代理

使用 Nginx 作为反向代理：

```bash
# 参考 deploy/nginx/speaksense.conf
sudo cp deploy/nginx/speaksense.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/speaksense.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 设置日志轮转

```bash
# 参考 deploy/logrotate/speaksense
sudo cp deploy/logrotate/speaksense /etc/logrotate.d/
```

### 4. 数据备份

```bash
# 定期备份数据库和配置
./deploy/backup.sh

# 添加到 crontab
crontab -e
# 添加: 0 2 * * * /path/to/SpeakSense/deploy/backup.sh
```

---

## 📞 访问地址

部署完成后，可以通过以下地址访问：

- **管理门户**: http://YOUR_SERVER_IP:8090/portal/index.html
- **API文档**:
  - http://YOUR_SERVER_IP:8001/docs (ASR)
  - http://YOUR_SERVER_IP:8002/docs (Retrieval)
  - http://YOUR_SERVER_IP:8003/docs (Admin)

---

## 🔐 安全建议

1. **修改默认端口**: 编辑各服务的 main.py 修改端口
2. **启用HTTPS**: 配置 SSL 证书
3. **设置访问控制**: 使用防火墙限制IP访问
4. **定期更新**: 及时更新依赖包修复安全漏洞
5. **数据备份**: 定期备份数据库和音频文件

---

## 📚 更多信息

- GitHub: [SpeakSense](https://github.com/your-repo/speaksense)
- 文档: [完整文档](./docs/)
- 问题反馈: [Issues](https://github.com/your-repo/speaksense/issues)
