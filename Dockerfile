# Use Python 3.11 slim base image from NetEase mirror
FROM hub-mirror.c.163.com/library/python:3.11-slim

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

# Create entrypoint script
RUN echo '#!/bin/bash\n\
CMD="$1"\n\
shift\n\
case "$CMD" in\n\
    fetch)\n\
        python3 /app/query_antom_psr_data.py "$@"\n\
        ;;\n\
    analyze)\n\
        python3 /app/analyse_and_gen_report.py "$@"\n\
        ;;\n\
    send)\n\
        python3 /app/send_psr_report.py "$@"\n\
        ;;\n\
    *)\n\
        echo "Usage: docker run <image> {fetch|analyze|send} [args...]"\n\
        echo "  fetch --date_range YYYYMMDD~YYYYMMDD --merchant_id ID --merchant_token TOKEN"\n\
        echo "  analyze --date YYYYMMDD"\n\
        echo "  send --date YYYYMMDD --recipient email@example.com"\n\
        exit 1\n\
        ;;\n\
esac' > /entrypoint.sh && chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
