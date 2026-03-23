# Use AgentScope runtime sandbox browser image as base
FROM agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/runtime-sandbox-browser:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy Python scripts
COPY query_antom_psr_data.py /app/
COPY analyse_and_gen_report.py /app/
COPY send_psr_report.py /app/

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /root/antom/success_rate

# Set Python path
ENV PYTHONPATH="/app:$PYTHONPATH"

# Make scripts executable
RUN chmod +x /app/*.py

# Copy entrypoint script (using COPY instead of inline RUN)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default: start HTTP service (AgentScope mode)
CMD []
