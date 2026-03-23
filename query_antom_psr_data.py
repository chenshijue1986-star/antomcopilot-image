#!/usr/bin/env python3
"""
Antom Payment Success Rate Data Query Tool
从antom服务端获取用户的交易数据
"""

import argparse
import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
import platform

# 默认配置
DEFAULT_BOT_ID = "2026031710103500118"
DEFAULT_BIZ_USER_ID = "antom open claw"
DEFAULT_TOKEN = "138766e7-9c68-476f-9bd0-60f466d56faf"
API_ENDPOINT = "https://ibotservice.alipayplus.com/almpapi/v1/message/chat"


def get_config_path():
    """获取配置文件路径，兼容macOS、Linux和Windows"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom")
    else:
        base_dir = os.path.expanduser("~/antom")
    
    config_path = os.path.join(base_dir, "antom_conf.json")
    return config_path


def load_config():
    """加载配置文件"""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        print("请先配置antom_conf.json文件")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"错误: 读取配置文件失败: {e}")
        sys.exit(1)


def validate_config(config):
    """验证配置是否完整"""
    required_fields = ["merchant_id", "merchant_token", "email_conf"]
    
    for field in required_fields:
        if field not in config:
            print(f"错误: 配置文件缺少必要字段: {field}")
            sys.exit(1)
    
    # 验证email_conf
    email_conf = config["email_conf"]
    email_fields = ["smtp_server", "smtp_port", "username", "password"]
    
    for field in email_fields:
        if field not in email_conf:
            print(f"错误: email_conf缺少必要字段: {field}")
            sys.exit(1)
    
    return True


def create_directories():
    """创建必要的目录"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom")
    else:
        base_dir = os.path.expanduser("~/antom")
    
    success_rate_dir = os.path.join(base_dir, "success rate")
    
    os.makedirs(success_rate_dir, exist_ok=True)
    
    return success_rate_dir


def query_antom_api(date_range, merchant_id, merchant_token):
    """
    调用antom API获取支付成功率数据
    
    Args:
        date_range: 日期范围，格式: "20260310~20260312"
        merchant_id: 商户ID
        merchant_token: 商户token
    
    Returns:
        dict: API返回的JSON数据
    """
    # 解析日期范围
    try:
        start_date, end_date = date_range.split("~")
        datetime.strptime(start_date, "%Y%m%d")
        datetime.strptime(end_date, "%Y%m%d")
    except ValueError:
        print(f"错误: 日期格式不正确，应为YYYYMMDD~YYYYMMDD格式")
        sys.exit(1)
    
    # 构建请求payload
    text_content = f"商户ID是{merchant_id}，商户token是{merchant_token}，开始日期为{start_date}，结束日期为{end_date}。"
    
    payload = {
        "botId": DEFAULT_BOT_ID,
        "bizUserId": DEFAULT_BIZ_USER_ID,
        "token": DEFAULT_TOKEN,
        "stream": False,
        "chatContent": {
            "contentType": "TEXT",
            "text": text_content
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"正在从antom获取数据，日期范围: {date_range}...")
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # 检查是否有错误
        if "error" in result:
            print(f"错误: API返回错误: {result.get('error', '未知错误')}")
            sys.exit(1)
        
        print(f"成功获取数据，日期范围: {date_range}")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"错误: API请求失败: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 解析JSON响应失败: {e}")
        sys.exit(1)


def save_raw_data(data, start_date):
    """
    保存原始数据到文件
    
    Args:
        data: API返回的JSON数据
        start_date: 开始日期
    """
    success_rate_dir = create_directories()
    filename = f"{start_date}_raw_data.json"
    filepath = os.path.join(success_rate_dir, filename)
    
    try:
        # 确保子文件夹"success rate"存在
        os.makedirs(success_rate_dir, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"原始数据已保存到: {filepath}")
        return filepath
    except Exception as e:
        print(f"错误: 保存数据文件失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='从antom获取支付成功率数据')
    parser.add_argument('--date_range', required=True, help='日期范围，格式: YYYYMMDD~YYYYMMDD')
    parser.add_argument('--merchant_id', help='商户ID（可选，从配置文件读取）')
    parser.add_argument('--merchant_token', help='商户token（可选，从配置文件读取）')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    validate_config(config)
    
    # 获取merchant_id和merchant_token
    merchant_id = args.merchant_id or config.get("merchant_id")
    merchant_token = args.merchant_token or config.get("merchant_token")
    
    if not merchant_id or not merchant_token:
        print("错误: merchant_id和merchant_token必须提供（通过参数或配置文件）")
        sys.exit(1)
    
    # 获取数据
    data = query_antom_api(args.date_range, merchant_id, merchant_token)
    
    # 解析开始日期
    start_date = args.date_range.split("~")[0]
    
    # 保存数据
    save_raw_data(data, start_date)


if __name__ == "__main__":
    main()
