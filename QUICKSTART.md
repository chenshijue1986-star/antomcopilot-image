# 🚀 快速开始指南

## 📋 准备步骤

### 1. 准备配置文件

在主机上创建配置文件目录和文件：

```bash
mkdir -p ~/antom
cat > ~/antom/antom_conf.json << 'EOF'
{
  "merchant_id": "2190170132223313",
  "merchant_token": "你的商户token",
  "email_conf": {
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "username": "chenshijue@foxmail.com",
    "password": "你的邮箱授权码",
    "sender_email": "chenshijue@foxmail.com"
  }
}
EOF

chmod 600 ~/antom/antom_conf.json
```

**注意**：
- 如果使用 QQ 邮箱，密码需要是「授权码」而不是登录密码
- 在 QQ 邮箱设置中生成 SMTP 授权码
- smtp_port: 465（SSL）或 587（TLS）

### 2. 确保项目文件完整

在 `~/GitRespository/antomcopilot-image/` 目录下应有以下文件：

```
.
├── Dockerfile                      # Docker 镜像构建文件
├── query_antom_psr_data.py         # 数据拉取脚本
├── analyse_and_gen_report.py       # 分析报告脚本
├── send_psr_report.py             # 邮件发送脚本
├── requirements.txt               # Python 依赖
├── README.md                      # 完整文档
├── QUICKSTART.md                  # 本快速指南
├── build-and-push.sh             # 构建推送脚本
├── test-local.sh                 # 本地测试脚本
├── run-in-k8s.sh                 # K8s 执行脚本
├── antom_conf.example.json       # 配置示例
└── .gitignore                    # Git 忽略文件
```

### 3. 构建 Docker 镜像

```bash
cd ~/GitRespository/antomcopilot-image

docker build -t antom-psr-analyzer:latest .
```

构建过程约 2-5 分钟（首次构建），会安装所有 Python 依赖。

### 4. 本地测试

运行测试脚本验证镜像：

```bash
./test-local.sh
```

测试内容包括：
- Python 环境检查
- 依赖库验证
- 脚本完整性检查
- 配置文件挂载测试

## 🎯 使用示例

### 场景一：手动分步执行

**步骤 1: 拉取数据**

```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest fetch \
  --date_range 20260310~20260318 \
  --merchant_id 2190170132223313 \
  --merchant_token your_token_here
```

输出：
```
正在从antom获取数据，日期范围: 20260310~20260318...
成功获取数据，日期范围: 20260310~20260318
原始数据已保存到: /root/antom/success rate/20260310_raw_data.json
```

**步骤 2: 生成报告**

```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest analyze \
  --date 20260318
```

输出：
```
✅ 图表生成完成！
📊 报告生成完成: /root/antom/success rate/20260318/20260318-Payment-Success-Rate-Report-2190170132223313.pdf
```

**步骤 3: 发送邮件**

```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest send \
  --date 20260318 \
  --recipient manager@example.com
```

输出：
```
✅ 邮件发送成功！
```

### 场景二：一键执行所有步骤

使用提供的脚本：

```bash
# 进入项目目录
cd ~/GitRespository/antomcopilot-image

# 运行一键脚本（参数: 日期 收件人）
./run-in-k8s.sh 20260318 manager@example.com
```

这会创建 Kubernetes Job 自动执行所有步骤。

### 场景三：在 IntelliJ IDEA 中开发测试

1. **启动 AgentScope Studio**：
   ```bash
   export NODE_TLS_REJECT_UNAUTHORIZED=0
   agentscope-studio
   ```

2. **确保 Kubernetes 连接正常**：
   ```bash
   kubectl --kubeconfig=~/.kube/config get nodes
   ```

3. **创建配置文件**：
   ```bash
   mkdir -p ~/antom
   # 创建并填写 antom_conf.json
   ```

4. **创建测试 Pod**：
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: antom-psr-test
   spec:
     containers:
     - name: test
       image: antom-psr-analyzer:latest
       command: ["sleep", "3600"]
       volumeMounts:
       - name: config
         mountPath: /root/antom
     volumes:
     - name: config
       hostPath:
         path: /Users/chenshijue/antom
     restartPolicy: Never
   ```

5. **在 Pod 中测试**：
   ```bash
   kubectl exec -it antom-psr-test -- /bin/bash
   # 在容器内执行: python3 /app/query_antom_psr_data.py --date_range 20260318~20260318 --merchant_id xxx --merchant_token xxx
   ```

## 📦 推送到阿里云 ACR

### 方式一：使用脚本（推荐）

```bash
./build-and-push.sh
```

脚本会：
1. 构建镜像
2. 本地测试
3. 提示登录阿里云 ACR
4. 打标签
5. 推送镜像
6. 创建 Kubernetes 执行脚本

### 方式二：手动推送

```bash
# 登录阿里云 ACR
docker login agentscope-registry.ap-southeast-1.cr.aliyuncs.com

# 打标签
docker tag antom-psr-analyzer:latest \
  agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest

# 推送
docker push agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest
```

### 方式三：在 GitHub Actions 中自动构建（高级）

创建 `.github/workflows/build-and-push.yml`：

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Login to Alibaba Cloud ACR
      uses: aliyun/acr-login@v1
      with:
        login-server: https://agentscope-registry.ap-southeast-1.cr.aliyuncs.com
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}

    - name: Build and push
      run: |
        docker build -t antom-psr-analyzer:${{ github.sha }} .
        docker tag antom-psr-analyzer:${{ github.sha }} \
          agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest
        docker push agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest
```

## 🔧 故障排查

### 问题 1: 配置文件找不到

**错误信息**：
```
错误: 配置文件不存在: /root/antom/antom_conf.json
```

**解决方案**：
```bash
# 主机上创建配置文件
mkdir -p ~/antom
cat > ~/antom/antom_conf.json << 'EOF'
{...}
EOF

# Docker 运行时挂载卷
docker run -v ~/antom:/root/antom ...
```

### 问题 2: 邮件发送失败

**错误信息**：
```
错误: SMTP认证失败
```

**解决方案**：
- QQ 邮箱：使用授权码而不是登录密码
- Gmail：需要开启「不够安全的应用」或使用应用专用密码
- 企业邮箱：确认 SMTP 服务已开启

### 问题 3: 数据文件找不到

**错误信息**：
```
错误: Data file not found: /root/antom/success rate/20260318_raw_data.json
```

**解决方案**：
确保按正确顺序执行：
1. 先执行 `fetch` 拉取数据
2. 再执行 `analyze` 生成报告
3. 最后执行 `send` 发送邮件

### 问题 4: 中文字符显示异常

**错误信息**：
PDF 报告中中文显示为方框

**解决方案**：
这是已知问题，镜像使用英文字体生成 PDF，确保图表和数据使用英文标签。

## 📚 核心脚本参数说明

### query_antom_psr_data.py

```
参数:
  --date_range YYYYMMDD~YYYYMMDD  # 日期范围（必需）
  --merchant_id ID                # 商户ID（可选，从配置文件读取）
  --merchant_token TOKEN          # 商户token（可选，从配置文件读取）

输出:
  ~/antom/success rate/{start_date}_raw_data.json
```

### analyse_and_gen_report.py

```
参数:
  --date YYYYMMDD  # 分析日期（必需）

输入:
  ~/antom/success rate/{date}_raw_data.json

输出:
  ~/antom/success rate/{date}/
    ├── {date}-Payment-Success-Rate-Report-{merchant_id}.pdf
    └── images/
        ├── card_overall.png
        ├── card_error_pie.png
        ├── apm_overall.png
        └── apm_error_pie.png
```

### send_psr_report.py

```
参数:
  --date YYYYMMDD            # 报告日期（必需）
  --recipient EMAIL          # 收件人邮箱（必需）

输入:
  ~/antom/success rate/{date}/{date}-Payment-Success-Rate-Report-{merchant_id}.pdf

输出:
  发送邮件到指定收件人
```

## 🎉 完成！

现在你已经完成了：
- ✅ 创建了 Docker 镜像项目
- ✅ 配置了 Python 环境和依赖
- ✅ 打包了三个核心脚本
- ✅ 创建了完整的文档和脚本
- ✅ 准备好推送到阿里云 ACR

下一步：
1. 配置 `~/antom/antom_conf.json`
2. 构建镜像：`docker build -t antom-psr-analyzer .`
3. 本地测试：`./test-local.sh`
4. 推送到 ACR：`./build-and-push.sh`
5. 在 Kubernetes 中运行：`./run-in-k8s.sh`
