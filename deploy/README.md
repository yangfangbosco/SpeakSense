# SpeakSense 部署脚本

本目录包含 SpeakSense 的完整部署脚本和工具。

## 📁 脚本说明

| 脚本 | 功能 | 用途 |
|------|------|------|
| `deploy.sh` | 完整部署 | 自动化完成环境配置、依赖安装、模型下载、服务启动 |
| `check_environment.sh` | 环境检查 | 验证系统是否满足部署要求 |
| `test_deployment.sh` | 部署测试 | 测试所有服务是否正常工作 |
| `backup.sh` | 数据备份 | 备份数据库、音频文件和配置 |
| `restore.sh` | 数据恢复 | 从备份恢复数据 |

## 🚀 快速开始

### 1. 检查环境

```bash
./deploy/check_environment.sh
```

### 2. 执行部署

```bash
./deploy/deploy.sh
```

部署脚本会自动完成：
- ✅ 创建 Conda 环境
- ✅ 安装所有依赖
- ✅ 下载 AI 模型
- ✅ 配置服务器 IP
- ✅ 启动所有服务
- ✅ 运行健康检查

### 3. 测试部署

```bash
./deploy/test_deployment.sh
```

## 📋 详细部署步骤

### 方式一：自动部署（推荐）

```bash
# 1. 上传项目到服务器
scp -r /path/to/SpeakSense user@server:/path/to/

# 2. SSH 到服务器
ssh user@server
cd /path/to/SpeakSense

# 3. 运行部署脚本
./deploy/deploy.sh

# 4. 测试部署
./deploy/test_deployment.sh
```

### 方式二：手动部署

参见 [DEPLOYMENT.md](../DEPLOYMENT.md) 的详细步骤。

## 🔧 使用指定的服务器 IP

```bash
# 部署时指定 IP
SERVER_IP=192.168.1.100 ./deploy/deploy.sh

# 或设置环境变量
export SERVER_IP=192.168.1.100
./deploy/deploy.sh
```

## 💾 备份与恢复

### 创建备份

```bash
# 手动备份
./deploy/backup.sh

# 定时备份（添加到 crontab）
crontab -e
# 添加：0 2 * * * /path/to/SpeakSense/deploy/backup.sh
```

备份文件位置：`./backups/speaksense_backup_YYYYMMDD_HHMMSS.tar.gz`

### 从备份恢复

```bash
# 列出可用备份
ls -lh ./backups/

# 恢复指定备份
./deploy/restore.sh ./backups/speaksense_backup_20250118_120000.tar.gz
```

## 🔍 故障排查

### 查看部署日志

```bash
# 查看所有服务日志
tail -f logs/*.log

# 查看特定服务
tail -f logs/asr_service.log
tail -f logs/retrieval_service.log
tail -f logs/admin_service.log
```

### 重新部署

```bash
# 停止服务
./stop_all_services.sh

# 清理数据（可选）
./clean_data.sh

# 重新部署
./deploy/deploy.sh
```

### 常见问题

#### 1. Conda 环境冲突

```bash
# 删除旧环境
conda deactivate
conda remove -n speaksense --all -y

# 重新部署
./deploy/deploy.sh
```

#### 2. 端口被占用

```bash
# 查找占用进程
lsof -i:8001
lsof -i:8002
lsof -i:8003

# 停止所有服务
./stop_all_services.sh
```

#### 3. 模型下载失败

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com

# 重新运行部署
./deploy/deploy.sh
```

## 📊 生产环境配置

### 使用 systemd 管理服务

```bash
# 复制服务文件
sudo cp deploy/systemd/*.service /etc/systemd/system/

# 重载并启用服务
sudo systemctl daemon-reload
sudo systemctl enable speaksense-asr
sudo systemctl enable speaksense-retrieval
sudo systemctl enable speaksense-admin

# 启动服务
sudo systemctl start speaksense-asr
sudo systemctl start speaksense-retrieval
sudo systemctl start speaksense-admin
```

### 配置 Nginx 反向代理

```bash
# 复制配置文件
sudo cp deploy/nginx/speaksense.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/speaksense.conf /etc/nginx/sites-enabled/

# 测试并重载 Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## 📞 获取帮助

- 详细文档：[DEPLOYMENT.md](../DEPLOYMENT.md)
- 主 README：[../README.md](../README.md)
- 问题反馈：GitHub Issues

## 📝 更新日志

- 2025-01-18: 创建完整部署脚本套件
- 支持自动化部署、备份、恢复功能
