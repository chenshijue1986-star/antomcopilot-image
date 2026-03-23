# Antom Payment Success Rate - Docker Image

基于 Python 3.11 构建的 Antom 支付成功率分析 Docker 镜像，包含数据拉取、分析和报告发送完整流程。

## 镜像功能

包含三个核心 Python 脚本：

1. **query_antom_psr_data.py** - 从 Antom API 拉取交易数据
2. **analyse_and_gen_report.py** - 分析数据并生成 PDF 报告（含图表）
3. **send_psr_report.py** - 发送邮件报告

## 环境要求

- Docker 运行环境
- 配置文件：~/antom/antom_conf.json（需挂载到容器内）

## 配置文件格式

在主机上创建配置文件 `~/antom/antom_conf.json`：

```json
{
  "merchant_id": "你的商户ID",
  "merchant_token": "你的商户token",
  "email_conf": {
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "username": "your_email@foxmail.com",
    "password": "你的邮箱密码或授权码",
    "sender_email": "your_email@foxmail.com"
  }
}
```

## 构建镜像

```bash
docker build -t antom-psr-analyzer:latest .
```

## 使用方法

### 方式一：分步执行

**1. 数据拉取**
```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest fetch \
  --date_range 20260310~20260318 \
  --merchant_id YOUR_MERCHANT_ID \
  --merchant_token YOUR_MERCHANT_TOKEN
```

**2. 数据分析与报告生成**
```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest analyze \
  --date 20260318
```

**3. 发送报告邮件**
```bash
docker run --rm \
  -v ~/antom:/root/antom \
  antom-psr-analyzer:latest send \
  --date 20260318 \
  --recipient recipient@example.com
```

### 方式二：一键执行所有步骤

创建执行脚本 `run-psr-analysis.sh`：

```bash
#!/bin/bash
DATE="20260318"
RECIPIENT="manager@example.com"
MERCHANT_ID="your_merchant_id"
MERCHANT_TOKEN="your_merchant_token"

echo "🚀 开始处理 ${DATE} 的支付成功率报告..."

# 步骤1: 拉取数据
echo "📥 拉取数据..."
docker run --rm -v ~/antom:/root/antom antom-psr-analyzer:latest fetch \
  --date_range ${DATE}~${DATE} \
  --merchant_id ${MERCHANT_ID} \
  --merchant_token ${MERCHANT_TOKEN}

# 步骤2: 生成报告
echo "📊 生成报告..."
docker run --rm -v ~/antom:/root/antom antom-psr-analyzer:latest analyze \
  --date ${DATE}

# 步骤3: 发送报告
echo "📧 发送报告..."
docker run --rm -v ~/antom:/root/antom antom-psr-analyzer:latest send \
  --date ${DATE} \
  --recipient ${RECIPIENT}

echo "✅ 处理完成！"
```

### 方式三：在 Kubernetes 中运行

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: antom-psr-analysis-20260318
spec:
  template:
    spec:
      containers:
      - name: psr-analyzer
        image: antom-psr-analyzer:latest
        args:
          - send
          - --date
          - "20260318"
          - --recipient
          - "manager@example.com"
        volumeMounts:
        - name: antom-config
          mountPath: /root/antom
          readOnly: true
      volumes:
      - name: antom-config
        hostPath:
          path: /Users/chenshijue/antom
      restartPolicy: Never
```

## 文件结构

容器内目录结构：
```
/root/antom/
├── antom_conf.json          # 配置文件（需从主机挂载）
└── success rate/            # 数据和分析结果存储目录
    ├── 20260310_raw_data.json         # 原始数据
    ├── 20260310/                       # 报告目录
    │   ├── 20260310-Payment-Success-Rate-Report-<merchant_id>.pdf
    │   └── images/                     # 图表文件
    │       ├── card_overall.png
    │       ├── card_error_pie.png
    │       ├── apm_overall.png
    │       └── apm_error_pie.png
    └── 20260310_executive_summary.txt  # 报告摘要
```

## Docker 镜像详情

- **基础镜像**: python:3.11-slim
- **安装依赖**: 
  - requests (HTTP 请求)
  - matplotlib (图表生成)
  - pandas (数据处理)
  - reportlab (PDF 生成)
  - numpy (数值计算)
- **工作目录**: /app
- **入口点**: /entrypoint.sh

## 常见问题

### Q1: 如何配置邮箱？
A: 修改 `~/antom/antom_conf.json` 文件中的 `email_conf` 部分，支持 QQ、Gmail、企业邮箱等任何 SMTP 服务。

### Q2: 数据存储在哪里？
A: 所有数据存储在主机的 `~/antom` 目录，通过 Docker 卷挂载到容器的 `/root/antom` 目录。

### Q3: 支持哪些日期格式？
A: 使用 YYYYMMDD 8位数字格式，如 20260318。

### Q4: 如何定时执行？
A: 使用 cron 或 Kubernetes CronJob，例如每天自动执行：
```bash
0 9 * * * /path/to/run-psr-analysis.sh
```

## 版本信息

- **版本**: 1.0.0
- **构建日期**: 2026-03-23
- **作者**: chenshijue

## 阿里云镜像仓库

推送到阿里云 ACR：
```bash
# 打标签
docker tag antom-psr-analyzer:latest \
  agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest

# 推送
docker push agentscope-registry.ap-southeast-1.cr.aliyuncs.com/your-namespace/antom-psr-analyzer:latest
```

然后在 Kubernetes 中直接使用该镜像。
