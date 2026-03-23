#!/bin/bash

# Antom PSR Analyzer - Build and Push Script
# 自动构建 Docker 镜像并推送到阿里云 ACR

set -e

# 配置参数
IMAGE_NAME="antom-psr-analyzer"
VERSION="1.0.0"
ACR_REGISTRY="agentscope-registry.ap-southeast-1.cr.aliyuncs.com"
ACR_NAMESPACE="your-namespace"  # 修改为阿里云 ACR 命名空间
FULL_IMAGE_NAME="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:${VERSION}"
LATEST_IMAGE_NAME="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:latest"

echo "🐳 Docker 镜像构建与推送脚本"
echo "======================================"
echo ""

# 步骤 1: 构建镜像
echo "📦 步骤 1: 构建 Docker 镜像..."
docker build -t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:latest .
echo "✅ 镜像构建成功"
echo ""

# 步骤 2: 本地测试
echo "🧪 步骤 2: 本地测试镜像..."
echo "测试 Python 版本:"
docker run --rm ${IMAGE_NAME}:${VERSION} python3 --version
echo ""

# 步骤 3: 检查配置文件
echo "🔍 步骤 3: 检查配置文件..."
if [ -f "${HOME}/antom/antom_conf.json" ]; then
    echo "✅ 配置文件存在: ${HOME}/antom/antom_conf.json"
else
    echo "⚠️  警告: 配置文件不存在，请先创建:"
    echo "   mkdir -p ${HOME}/antom"
    echo "   创建 ${HOME}/antom/antom_conf.json 文件"
fi
echo ""

# 步骤 4: 登录阿里云 ACR
echo "🔐 步骤 4: 登录阿里云容器镜像服务..."
echo "请访问: https://cr.console.aliyun.com/"
echo "获取登录凭证"
echo ""
echo "执行登录命令:"
echo "docker login ${ACR_REGISTRY}"
echo ""
read -p "已执行登录？(按回车继续)"

# 步骤 5: 打标签
echo "🏷️  步骤 5: 为镜像打标签..."
docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}
docker tag ${IMAGE_NAME}:latest ${LATEST_IMAGE_NAME}
echo "✅ 标签创建成功"
echo "  - ${FULL_IMAGE_NAME}"
echo "  - ${LATEST_IMAGE_NAME}"
echo ""

# 步骤 6: 推送镜像
echo "📤 步骤 6: 推送镜像到阿里云 ACR..."
docker push ${FULL_IMAGE_NAME}
docker push ${LATEST_IMAGE_NAME}
echo "✅ 镜像推送成功"
echo ""

# 步骤 7: 验证
echo "✅ 步骤 7: 验证远程镜像..."
echo "镜像地址: ${FULL_IMAGE_NAME}"
echo ""
echo "在 Kubernetes 中使用:"
echo "  image: ${FULL_IMAGE_NAME}"
echo ""
echo "拉取测试:"
echo "  docker pull ${FULL_IMAGE_NAME}"
echo ""

# 步骤 8: 创建一键执行脚本
echo "📜 步骤 8: 创建一键执行脚本..."
cat > run-in-k8s.sh << 'EOFRUN'
#!/bin/bash
# Kubernetes Job 执行脚本

DATE="${1:-$(date +%Y%m%d)}"
RECIPIENT="${2:-manager@example.com}"

echo "🚀 在 Kubernetes 中执行 Antom PSR 分析..."
echo "日期: ${DATE}"
echo "收件人: ${RECIPIENT}"

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: antom-psr-analysis-${DATE}
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: psr-analyzer
        image: agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest
        args:
          - send
          - --date
          - "${DATE}"
          - --recipient
          - "${RECIPIENT}"
        volumeMounts:
        - name: antom-config
          mountPath: /root/antom
          readOnly: true
      volumes:
      - name: antom-config
        hostPath:
          path: /Users/chenshijue/antom
      restartPolicy: Never
  backoffLimit: 3
EOF

echo "✅ Job 已提交，查看状态:"
echo "  kubectl get jobs"
echo "  kubectl describe job antom-psr-analysis-${DATE}"
echo "  kubectl logs -l job-name=antom-psr-analysis-${DATE}"
EOFRUN

chmod +x run-in-k8s.sh
echo "✅ 脚本创建成功: run-in-k8s.sh"
echo ""

echo "======================================"
echo "🎉 构建和推送完成！"
echo ""
echo "📋 后续步骤:"
echo "1. 确保配置文件存在: ${HOME}/antom/antom_conf.json"
echo "2. 本地测试: ./test-local.sh"
echo "3. Kubernetes 部署: ./run-in-k8s.sh 20260318 recipient@example.com"
echo ""
echo "📦 镜像信息:"
echo "  本地镜像: ${IMAGE_NAME}:${VERSION}"
echo "  远程镜像: ${FULL_IMAGE_NAME}"
echo ""
echo "🚀 快速开始:"
echo "  docker run --rm -v \${HOME}/antom:/root/antom ${FULL_IMAGE_NAME} send --date 20260318 --recipient manager@example.com"
echo ""
