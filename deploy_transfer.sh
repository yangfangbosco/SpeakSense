#!/bin/bash
# SpeakSense 数据传输脚本
# 只负责传输代码和模型到远程服务器

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONFIG_FILE=".deploy_config"

echo "============================================================"
echo "SpeakSense 数据传输工具"
echo "============================================================"
echo ""

# 加载或输入配置
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${BLUE}发现配置文件，加载配置...${NC}"
    source "$CONFIG_FILE"
    echo ""
    echo "配置信息："
    echo -e "  用户名: ${YELLOW}${REMOTE_USER}${NC}"
    echo -e "  服务器: ${YELLOW}${REMOTE_HOST}${NC}"
    echo -e "  路径:   ${YELLOW}${REMOTE_PATH}${NC}"
    echo ""
    read -p "是否使用此配置？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        USE_OLD_CONFIG=false
    else
        USE_OLD_CONFIG=true
    fi
else
    USE_OLD_CONFIG=false
fi

if [ "$USE_OLD_CONFIG" = false ]; then
    echo -e "${BLUE}请输入部署配置：${NC}"
    echo ""

    # 输入远程用户名
    read -p "远程服务器用户名: " REMOTE_USER
    if [ -z "$REMOTE_USER" ]; then
        echo -e "${RED}错误：用户名不能为空${NC}"
        exit 1
    fi

    # 输入远程服务器地址
    read -p "远程服务器地址 (IP 或域名): " REMOTE_HOST
    if [ -z "$REMOTE_HOST" ]; then
        echo -e "${RED}错误：服务器地址不能为空${NC}"
        exit 1
    fi

    # 输入远程路径
    read -p "远程 SpeakSense 项目路径: " REMOTE_PATH
    if [ -z "$REMOTE_PATH" ]; then
        echo -e "${RED}错误：项目路径不能为空${NC}"
        exit 1
    fi

    # 保存配置
    echo ""
    read -p "是否保存此配置？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > "$CONFIG_FILE" << EOF
# SpeakSense 部署配置
# 自动生成于 $(date)
REMOTE_USER="$REMOTE_USER"
REMOTE_HOST="$REMOTE_HOST"
REMOTE_PATH="$REMOTE_PATH"
EOF
        echo -e "${GREEN}✓ 配置已保存到 $CONFIG_FILE${NC}"
    fi
    echo ""
fi

REMOTE="${REMOTE_USER}@${REMOTE_HOST}"

echo -e "${GREEN}传输配置：${NC}"
echo -e "  目标服务器: ${YELLOW}${REMOTE}${NC}"
echo -e "  目标路径:   ${YELLOW}${REMOTE_PATH}${NC}"
echo ""

# 测试连接
echo "1. 测试远程连接..."
if ssh -o ConnectTimeout=5 ${REMOTE} "echo '连接成功'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 连接成功${NC}"
else
    echo -e "${RED}✗ 无法连接到远程服务器${NC}"
    echo "请检查："
    echo "  - 服务器地址和用户名是否正确"
    echo "  - SSH 密钥是否已配置"
    exit 1
fi
echo ""

# 检查本地文件
echo "2. 检查本地文件完整性..."
MISSING_FILES=0

# 检查代码文件
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt 不存在${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}✓ requirements.txt${NC}"
fi

if [ ! -d "services" ]; then
    echo -e "${RED}✗ services/ 目录不存在${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}✓ services/${NC}"
fi

if [ ! -d "portal" ]; then
    echo -e "${RED}✗ portal/ 目录不存在${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}✓ portal/${NC}"
fi

# 检查模型文件
if [ ! -d "models/CosyVoice2-0.5B" ]; then
    echo -e "${RED}✗ models/CosyVoice2-0.5B 不存在${NC}"
    MISSING_FILES=1
else
    SIZE=$(du -sh models/CosyVoice2-0.5B | cut -f1)
    echo -e "${GREEN}✓ models/CosyVoice2-0.5B ($SIZE)${NC}"
fi

if [ ! -d "models/wetext" ]; then
    echo -e "${RED}✗ models/wetext 不存在${NC}"
    MISSING_FILES=1
else
    SIZE=$(du -sh models/wetext | cut -f1)
    echo -e "${GREEN}✓ models/wetext ($SIZE)${NC}"
fi

if [ ! -d "models/embedding/bge-small-zh-v1.5" ]; then
    echo -e "${RED}✗ models/embedding/bge-small-zh-v1.5 不存在${NC}"
    MISSING_FILES=1
else
    SIZE=$(du -sh models/embedding/bge-small-zh-v1.5 | cut -f1)
    echo -e "${GREEN}✓ models/embedding/bge-small-zh-v1.5 ($SIZE)${NC}"
fi

if [ ! -d "third_party/CosyVoice" ]; then
    echo -e "${RED}✗ third_party/CosyVoice 不存在${NC}"
    MISSING_FILES=1
else
    SIZE=$(du -sh third_party/CosyVoice | cut -f1)
    echo -e "${GREEN}✓ third_party/CosyVoice ($SIZE)${NC}"
fi

if [ ! -d "$HOME/.cache/whisper" ]; then
    echo -e "${YELLOW}⚠ ~/.cache/whisper 不存在${NC}"
else
    SIZE=$(du -sh ~/.cache/whisper | cut -f1)
    echo -e "${GREEN}✓ ~/.cache/whisper ($SIZE)${NC}"
fi

if [ ! -d "$HOME/.cache/huggingface" ]; then
    echo -e "${YELLOW}⚠ ~/.cache/huggingface 不存在${NC}"
else
    SIZE=$(du -sh ~/.cache/huggingface | cut -f1)
    echo -e "${GREEN}✓ ~/.cache/huggingface ($SIZE)${NC}"
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo -e "${RED}错误：缺少必需文件${NC}"
    exit 1
fi
echo ""

# 显示传输计划
echo "3. 传输模式选择："
echo ""
echo "rsync 支持增量同步，会自动跳过未变化的文件"
echo ""
echo "请选择传输模式："
echo "  1) 增量同步（推荐）- 只传输变化的文件，速度快"
echo "  2) 完整同步 - 强制检查所有文件（用于首次部署或数据验证）"
echo ""
read -p "请选择 (1/2，默认 1): " -n 1 -r
echo ""

if [[ -z $REPLY ]] || [[ $REPLY =~ ^[1]$ ]]; then
    SYNC_MODE="incremental"
    RSYNC_OPTS="-avz --progress"
    echo -e "${GREEN}✓ 选择：增量同步模式${NC}"
elif [[ $REPLY =~ ^[2]$ ]]; then
    SYNC_MODE="full"
    RSYNC_OPTS="-avz --progress --checksum"
    echo -e "${GREEN}✓ 选择：完整同步模式（使用 checksum 验证）${NC}"
else
    echo -e "${RED}错误：无效选择${NC}"
    exit 1
fi
echo ""

echo "4. 传输计划："
echo "   将传输/同步以下内容："
echo "   - 项目代码（所有源文件和脚本）"
echo "   - models/CosyVoice2-0.5B/ (约 4.8GB)"
echo "   - models/wetext/ (约 13MB)"
echo "   - models/embedding/bge-small-zh-v1.5/ (约 182MB)"
echo "   - third_party/CosyVoice/ (约 71MB)"
if [ -d "$HOME/.cache/whisper" ]; then
    echo "   - ~/.cache/whisper/ (约 1.6GB)"
fi
if [ -d "$HOME/.cache/huggingface" ]; then
    echo "   - ~/.cache/huggingface/ (约 1.7GB, 可选)"
fi
echo ""
if [ "$SYNC_MODE" = "incremental" ]; then
    echo "   ${GREEN}增量模式：只传输变化的文件，大幅节省时间${NC}"
    echo "   预计时间：首次 20-35 分钟，后续更新 1-5 分钟"
else
    echo "   ${YELLOW}完整模式：检查并传输所有文件${NC}"
    echo "   预计时间：20-35 分钟"
fi
echo ""

# 确认传输
echo -e "${YELLOW}准备开始传输${NC}"
read -p "是否继续？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消传输"
    exit 0
fi
echo ""

# 在远程创建目录结构
echo "5. 在远程服务器创建目录..."
ssh ${REMOTE} "mkdir -p ${REMOTE_PATH}/{models,third_party,services,portal,shared,logs,config} ~/.cache/{whisper,huggingface}"
echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# 传输项目代码
echo "6. 传输项目代码..."
echo "   正在同步源文件和脚本..."
rsync ${RSYNC_OPTS} \
    --exclude='*.pyc' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='.deploy_config' \
    --exclude='logs/' \
    --exclude='*.log' \
    --exclude='services/*/data/' \
    --exclude='models/' \
    --exclude='third_party/' \
    --exclude='.cache/' \
    --exclude='backup_*/' \
    --exclude='offline-packages/' \
    --exclude='test_*.py' \
    --exclude='test_*.wav' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    ./ ${REMOTE}:${REMOTE_PATH}/
echo -e "${GREEN}✓ 项目代码同步完成${NC}"
echo ""

# 传输项目模型
echo "7. 同步项目模型..."
echo "   [1/4] 正在同步 models/CosyVoice2-0.5B/..."
rsync ${RSYNC_OPTS} models/CosyVoice2-0.5B/ ${REMOTE}:${REMOTE_PATH}/models/CosyVoice2-0.5B/
echo -e "${GREEN}✓ CosyVoice2 模型同步完成${NC}"
echo ""

echo "   [2/4] 正在同步 models/wetext/..."
rsync ${RSYNC_OPTS} models/wetext/ ${REMOTE}:${REMOTE_PATH}/models/wetext/
echo -e "${GREEN}✓ wetext 模型同步完成${NC}"
echo ""

echo "   [3/4] 正在同步 models/embedding/bge-small-zh-v1.5/..."
rsync ${RSYNC_OPTS} models/embedding/bge-small-zh-v1.5/ ${REMOTE}:${REMOTE_PATH}/models/embedding/bge-small-zh-v1.5/
echo -e "${GREEN}✓ BGE Embedding 模型同步完成${NC}"
echo ""

echo "   [4/4] 正在同步 third_party/CosyVoice/..."
rsync ${RSYNC_OPTS} third_party/CosyVoice/ ${REMOTE}:${REMOTE_PATH}/third_party/CosyVoice/
echo -e "${GREEN}✓ CosyVoice 代码同步完成${NC}"
echo ""

# 传输缓存模型
echo "8. 同步缓存模型到用户目录..."
if [ -d "$HOME/.cache/whisper" ]; then
    echo "   [1/2] 正在同步 Whisper 模型..."
    rsync ${RSYNC_OPTS} ~/.cache/whisper/ ${REMOTE}:~/.cache/whisper/
    echo -e "${GREEN}✓ Whisper 模型同步完成${NC}"
    echo ""
fi

if [ -d "$HOME/.cache/huggingface" ]; then
    echo "   [2/2] 正在同步 HuggingFace 模型..."
    rsync ${RSYNC_OPTS} ~/.cache/huggingface/ ${REMOTE}:~/.cache/huggingface/
    echo -e "${GREEN}✓ HuggingFace 模型同步完成${NC}"
    echo ""
fi

# 传输环境构建脚本
echo "9. 传输环境构建脚本..."
if [ -f "deploy_setup.sh" ]; then
    scp deploy_setup.sh ${REMOTE}:${REMOTE_PATH}/
    ssh ${REMOTE} "chmod +x ${REMOTE_PATH}/deploy_setup.sh"
    echo -e "${GREEN}✓ 环境构建脚本已上传${NC}"
else
    echo -e "${YELLOW}⚠ deploy_setup.sh 不存在，跳过${NC}"
fi
echo ""

echo "============================================================"
echo -e "${GREEN}✓ 数据同步完成！${NC}"
echo "============================================================"
echo ""
echo "下一步：在远程服务器上构建环境"
echo ""
echo "方式 1：SSH 登录后手动执行"
echo "  ssh ${REMOTE}"
echo "  cd ${REMOTE_PATH}"
echo "  ./deploy_setup.sh"
echo ""
echo "方式 2：本地直接执行（推荐）"
echo "  ssh -t ${REMOTE} 'cd ${REMOTE_PATH} && ./deploy_setup.sh'"
echo ""
read -p "是否现在在远程服务器上执行环境构建？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "开始在远程服务器上构建环境..."
    ssh -t ${REMOTE} "cd ${REMOTE_PATH} && ./deploy_setup.sh"
else
    echo ""
    echo "请稍后手动执行环境构建脚本"
fi
