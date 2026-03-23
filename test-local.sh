#!/bin/bash

# 本地测试脚本

IMAGE_NAME="antom-psr-analyzer"
VERSION="1.0.0"

echo "🧪 本地测试 Antom PSR Analyzer"
echo "======================================"
echo ""

# 检查配置文件
if [ ! -f "${HOME}/antom/antom_conf.json" ]; then
    echo "❌ 错误: 配置文件不存在"
    echo "   请创建: ${HOME}/antom/antom_conf.json"
    echo ""
    echo "示例配置:"
    cat <<'EOFCONFIG'
{
  "merchant_id": "你的商户ID",
  "merchant_token": "你的商户token",
  "email_conf": {
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "username": "your_email@foxmail.com",
    "password": "your_password",
    "sender_email": "your_email@foxmail.com"
  }
}
EOFCONFIG
    exit 1
fi

echo "✅ 配置文件存在"
echo ""

# 测试1: Python 环境
echo "📋 测试1: Python 环境"
echo "----------------------"
docker run --rm ${IMAGE_NAME}:${VERSION} python3 --version
echo ""

# 测试2: 检查依赖
echo "📦 测试2: 检查依赖"
echo "----------------------"
docker run --rm ${IMAGE_NAME}:${VERSION} python3 -c "\
import requests; print('✅ requests: OK')\
import matplotlib; print('✅ matplotlib: OK')\
import pandas; print('✅ pandas: OK')\
import reportlab; print('✅ reportlab: OK')\
import numpy; print('✅ numpy: OK')"
echo ""

# 测试3: 检查脚本
echo "📄 测试3: 检查脚本"
echo "----------------------"
docker run --rm ${IMAGE_NAME}:${VERSION} ls -lh /app/
echo ""

# 测试4: 配置文件挂载测试
echo "🔍 测试4: 配置文件挂载测试"
echo "----------------------"
docker run --rm -v ${HOME}/antom:/root/antom \
  ${IMAGE_NAME}:${VERSION} \
  python3 -c "\
import json;\
import os;\
config_path = '/root/antom/antom_conf.json';\
print(f'配置文件路径: {config_path}');\
print(f'文件存在: {os.path.exists(config_path)}');\
if os.path.exists(config_path):\
    with open(config_path) as f:\
        config = json.load(f);\
    print(f'商户ID: {config.get(\"merchant_id\", \"未设置\")}');\
    print(f'邮件配置: {\"已配置\" if \"email_conf\" in config else \"未配置\"}')"
echo ""

echo "======================================"
echo "✅ 测试完成！"
echo ""
echo "📝 下一步:"
echo "1. 确保配置文件填写正确"
echo "2. 运行实际数据测试:"
echo "   docker run --rm -v \${HOME}/antom:/root/antom \\"
echo "     ${IMAGE_NAME}:${VERSION} fetch \\"
echo "     --date_range 20260310~20260318 \\"
echo "     --merchant_id YOUR_ID \\"
echo "     --merchant_token YOUR_TOKEN"
echo ""
echo "3. 构建并推送:"
echo "   ./build-and-push.sh"
echo ""
