#!/bin/bash
# 打包所有离线模型文件，用于在断网服务器上部署

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/offline-packages"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="speaksense_offline_models_$TIMESTAMP.tar.gz"

echo "============================================================"
echo "SpeakSense 离线模型打包工具"
echo "============================================================"

# 创建打包目录
echo ""
echo "1. 创建打包目录..."
mkdir -p "$PACKAGE_DIR"

# 检查并打包 CosyVoice2 模型
echo ""
echo "2. 检查 CosyVoice2 模型..."
if [ -d "$SCRIPT_DIR/models/CosyVoice2-0.5B" ]; then
    echo "   ✓ CosyVoice2-0.5B 模型存在"
    SIZE=$(du -sh "$SCRIPT_DIR/models/CosyVoice2-0.5B" | cut -f1)
    echo "   大小: $SIZE"
else
    echo "   ✗ CosyVoice2-0.5B 模型不存在！"
    echo "   请先运行: python download_cosyvoice_model.py"
    exit 1
fi

# 检查并打包 wetext 模型
echo ""
echo "3. 检查 wetext 模型..."
if [ -d "$SCRIPT_DIR/models/wetext" ]; then
    echo "   ✓ wetext 模型存在"
    SIZE=$(du -sh "$SCRIPT_DIR/models/wetext" | cut -f1)
    echo "   大小: $SIZE"
else
    echo "   ✗ wetext 模型不存在！"
    echo "   正在从缓存复制..."
    if [ -d "$HOME/.cache/modelscope/hub/pengzhendong/wetext" ]; then
        cp -r "$HOME/.cache/modelscope/hub/pengzhendong/wetext" "$SCRIPT_DIR/models/"
        echo "   ✓ wetext 模型已复制"
    else
        echo "   ✗ 缓存中也不存在 wetext 模型！"
        echo "   请先运行一次系统以下载模型"
        exit 1
    fi
fi

# 检查 Whisper 模型
echo ""
echo "4. 检查 Whisper 模型..."
WHISPER_CACHE="$HOME/.cache/whisper"
if [ -d "$WHISPER_CACHE" ]; then
    echo "   ✓ Whisper 模型存在"
    SIZE=$(du -sh "$WHISPER_CACHE" | cut -f1)
    echo "   大小: $SIZE"
    INCLUDE_WHISPER=true
else
    echo "   ⚠ Whisper 模型不存在（首次运行时会自动下载）"
    INCLUDE_WHISPER=false
fi

# 检查 BGE embedding 模型
echo ""
echo "5. 检查 BGE embedding 模型..."
BGE_CACHE="$HOME/.cache/huggingface/hub"
if [ -d "$BGE_CACHE" ]; then
    echo "   ✓ HuggingFace 模型存在"
    SIZE=$(du -sh "$BGE_CACHE" | cut -f1)
    echo "   大小: $SIZE"
    INCLUDE_BGE=true
else
    echo "   ⚠ BGE 模型不存在（首次运行时会自动下载）"
    INCLUDE_BGE=false
fi

# 开始打包
echo ""
echo "6. 开始打包模型..."
cd "$SCRIPT_DIR"

# 创建临时目录结构
TEMP_DIR="$PACKAGE_DIR/temp_package"
mkdir -p "$TEMP_DIR"

# 复制项目模型
echo "   - 打包 CosyVoice2 和 wetext 模型..."
cp -r models "$TEMP_DIR/"

# 复制缓存模型（如果存在）
if [ "$INCLUDE_WHISPER" = true ]; then
    echo "   - 打包 Whisper 模型..."
    mkdir -p "$TEMP_DIR/cache/whisper"
    cp -r "$WHISPER_CACHE"/* "$TEMP_DIR/cache/whisper/"
fi

if [ "$INCLUDE_BGE" = true ]; then
    echo "   - 打包 BGE embedding 模型..."
    mkdir -p "$TEMP_DIR/cache/huggingface"
    cp -r "$BGE_CACHE" "$TEMP_DIR/cache/huggingface/"
fi

# 创建安装脚本
echo "   - 创建安装脚本..."
cat > "$TEMP_DIR/install_models.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
# 离线模型安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "SpeakSense 离线模型安装"
echo "============================================================"

# 复制项目模型
echo ""
echo "1. 安装项目模型..."
if [ -d "$SCRIPT_DIR/models" ]; then
    echo "   - 安装 CosyVoice2 模型..."
    mkdir -p ./models
    cp -r "$SCRIPT_DIR/models"/* ./models/
    echo "   ✓ 项目模型安装完成"
fi

# 复制缓存模型
echo ""
echo "2. 安装缓存模型..."
if [ -d "$SCRIPT_DIR/cache/whisper" ]; then
    echo "   - 安装 Whisper 模型..."
    mkdir -p "$HOME/.cache/whisper"
    cp -r "$SCRIPT_DIR/cache/whisper"/* "$HOME/.cache/whisper/"
    echo "   ✓ Whisper 模型安装完成"
fi

if [ -d "$SCRIPT_DIR/cache/huggingface" ]; then
    echo "   - 安装 BGE embedding 模型..."
    mkdir -p "$HOME/.cache/huggingface"
    cp -r "$SCRIPT_DIR/cache/huggingface"/* "$HOME/.cache/huggingface/"
    echo "   ✓ BGE embedding 模型安装完成"
fi

echo ""
echo "============================================================"
echo "✓ 所有模型安装完成！"
echo "============================================================"
echo ""
echo "测试离线运行:"
echo "  python test_offline.py"
echo ""
echo "启动服务:"
echo "  ./run_all_services.sh"
echo ""
INSTALL_SCRIPT

chmod +x "$TEMP_DIR/install_models.sh"

# 创建 README
cat > "$TEMP_DIR/README.txt" << 'README'
SpeakSense 离线模型包
=====================

包含内容:
- models/CosyVoice2-0.5B/  : CosyVoice2 TTS 模型
- models/wetext/           : 文本归一化模型
- cache/whisper/          : Whisper ASR 模型（如果可用）
- cache/huggingface/      : BGE embedding 模型（如果可用）

安装步骤:

1. 将此包复制到目标服务器的 SpeakSense 项目目录

2. 解压:
   tar -xzf speaksense_offline_models_*.tar.gz

3. 运行安装脚本:
   cd offline_models/
   ./install_models.sh

4. 测试离线运行:
   cd ..
   python test_offline.py

5. 启动服务:
   ./run_all_services.sh

详细文档请参考:
- OFFLINE_DEPLOYMENT.md

支持联系:
- GitHub Issues: <repository_url>
README

# 打包
echo "   - 压缩打包..."
cd "$PACKAGE_DIR"
tar -czf "$PACKAGE_NAME" -C temp_package .

# 清理临时目录
rm -rf temp_package

# 显示结果
echo ""
echo "============================================================"
echo "✓ 打包完成！"
echo "============================================================"
echo ""
echo "包文件: $PACKAGE_DIR/$PACKAGE_NAME"
echo "大小: $(du -sh "$PACKAGE_DIR/$PACKAGE_NAME" | cut -f1)"
echo ""
echo "在离线服务器上安装:"
echo "  1. 复制文件到服务器 SpeakSense 目录"
echo "  2. tar -xzf $PACKAGE_NAME"
echo "  3. cd offline_models && ./install_models.sh"
echo ""
echo "详细说明请查看: OFFLINE_DEPLOYMENT.md"
echo ""
