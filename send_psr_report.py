#!/usr/bin/env python3
"""
Antom Payment Success Rate Report Sender
Send payment success rate report emails with intelligent analysis
"""

import argparse
import json
import os
import sys
import smtplib
import platform
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import mimetypes


def get_config_path():
    """Get configuration file path, compatible with macOS, Linux and Windows"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom")
    else:
        base_dir = os.path.expanduser("~/antom")
    
    config_path = os.path.join(base_dir, "antom_conf.json")
    return config_path


def load_config():
    """Load configuration file"""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        print("Please configure antom_conf.json first")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error: Failed to read configuration file: {e}")
        sys.exit(1)


def get_report_file_path(date_str, merchant_id):
    """Get report file path"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom", "success rate")
    else:
        base_dir = os.path.expanduser("~/antom/success rate")
    
    report_dir = os.path.join(base_dir, date_str)
    filename = f"{date_str}-Payment-Success-Rate-Report-{merchant_id}.pdf"
    filepath = os.path.join(report_dir, filename)
    
    return filepath


def get_executive_summary_path(date_str):
    """Get executive summary file path"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom", "success rate")
    else:
        base_dir = os.path.expanduser("~/antom/success rate")
    
    report_dir = os.path.join(base_dir, date_str)
    filename = f"{date_str}_executive_summary.txt"
    filepath = os.path.join(report_dir, filename)
    
    return filepath


def get_raw_data_path(date_str):
    """Get raw data file path"""
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ["USERPROFILE"], "antom", "success rate")
    else:
        base_dir = os.path.expanduser("~/antom/success rate")
    
    filename = f"{date_str}_raw_data.json"
    filepath = os.path.join(base_dir, filename)
    
    return filepath


def load_raw_data(date_str):
    """Load raw data file"""
    data_file = get_raw_data_path(date_str)
    
    if not os.path.exists(data_file):
        return None
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load raw data {data_file}: {e}")
        return None


def load_previous_raw_data(date_str, days_back=1):
    """Load previous day's raw data"""
    try:
        current_date = datetime.strptime(date_str, "%Y%m%d")
        previous_date = current_date - timedelta(days=days_back)
        prev_date_str = previous_date.strftime("%Y%m%d")
        prev_data_file = get_raw_data_path(prev_date_str)
        
        if not os.path.exists(prev_data_file):
            return None
        
        with open(prev_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def analyze_card_risks(current_data, previous_data):
    """Analyze Card payment risks and generate intelligent insights"""
    if not current_data or 'card' not in current_data:
        return "No Card payment data available for analysis"
    
    insights = []
    warnings = []
    
    current_card = current_data['card']
    prev_card = previous_data.get('card', {}) if previous_data else {}
    
    # 1. Overall success rate analysis
    if 'total' in current_card:
        current_rate = (current_card['total'].get('success_count', 0) / 
                       current_card['total'].get('total_count', 1) * 100)
        
        prev_rate = 0
        if 'total' in prev_card and prev_card['total'].get('total_count', 0) > 0:
            prev_rate = (prev_card['total'].get('success_count', 0) / 
                        prev_card['total'].get('total_count', 1) * 100)
        
        rate_change = current_rate - prev_rate
        
        if prev_rate > 0:
            if abs(rate_change) > 10:
                warnings.append(f"⚠️  CRITICAL: Success rate {'dropped' if rate_change < 0 else 'increased'} by {abs(rate_change):.1f}% compared to yesterday")
            elif abs(rate_change) > 5:
                insights.append(f"📊 Success rate {'decreased' if rate_change < 0 else 'increased'} by {abs(rate_change):.1f}% compared to yesterday")
        
        if current_rate < 60:
            warnings.append(f"🚨 CRITICAL: Overall success rate is critically low at {current_rate:.1f}%")
        elif current_rate < 70:
            warnings.append(f"⚠️  WARNING: Overall success rate is below acceptable threshold at {current_rate:.1f}%")
        elif current_rate < 80:
            insights.append(f"📈 Success rate is at {current_rate:.1f}% - room for improvement")
        else:
            insights.append(f"✅ Overall success rate is healthy at {current_rate:.1f}%")
        
        insights.append(f"📊 Volume: {current_card['total'].get('total_count', 0)} total, {current_card['total'].get('success_count', 0)} successful")
    
    # 2. Authentication method analysis
    if 'auth' in current_card and prev_card:
        current_auth = current_card['auth']
        prev_auth = prev_card.get('auth', {})
        
        insights.append("")
        insights.append("🔐 Authentication Analysis:")
        
        if '3ds' in current_auth and 'non_3ds' in current_auth:
            rate_3ds = (current_auth['3ds'].get('success_count', 0) / 
                       current_auth['3ds'].get('total_count', 1) * 100) if current_auth['3ds'].get('total_count', 0) > 0 else 0
            rate_non3ds = (current_auth['non_3ds'].get('success_count', 0) / 
                          current_auth['non_3ds'].get('total_count', 1) * 100) if current_auth['non_3ds'].get('total_count', 0) > 0 else 0
            
            vol_3ds = current_auth['3ds'].get('total_count', 0)
            vol_non3ds = current_auth['non_3ds'].get('total_count', 0)
            total_auth = vol_3ds + vol_non3ds
            
            if total_auth > 0:
                pct_3ds = (vol_3ds / total_auth) * 100
                
                if pct_3ds > 30:
                    warnings.append(f"⚠️  3DS usage is high ({pct_3ds:.1f}%) - may impact user experience")
                
                if rate_3ds < rate_non3ds - 15:
                    warnings.append(f"🚨 3DS success rate ({rate_3ds:.1f}%) significantly lower than Non-3DS ({rate_non3ds:.1f}%)")
                
                insights.append(f"  • 3DS: {rate_3ds:.1f}% success rate, {vol_3ds} transactions ({pct_3ds:.1f}%)")
                insights.append(f"  • Non-3DS: {rate_non3ds:.1f}% success rate, {vol_non3ds} transactions ({100-pct_3ds:.1f}%)")
    
    # 3. Error code analysis
    if 'error_code' in current_card:
        current_errors = {k: v for k, v in current_card['error_code'].items() 
                         if k != 'pay_success' and v > 0}
        prev_errors = {k: v for k, v in prev_card.get('error_code', {}).items() 
                      if k != 'pay_success' and v > 0}
        
        if current_errors:
            insights.append("")
            insights.append("❌ Error Code Analysis:")
            
            # Sort by count
            sorted_errors = sorted(current_errors.items(), key=lambda x: x[1], reverse=True)
            
            for error_code, count in sorted_errors[:3]:
                prev_count = prev_errors.get(error_code, 0)
                change_pct = ((count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                if prev_count > 0:
                    if change_pct > 100:
                        warnings.append(f"🚨 {error_code} has increased by {change_pct:.0f}% - INVESTIGATE IMMEDIATELY")
                    elif change_pct > 50:
                        warnings.append(f"⚠️  {error_code} has increased by {change_pct:.0f}% - monitor closely")
                
                pct_of_total = (count / current_card['total'].get('total_count', 1) * 100)
                insights.append(f"  • {error_code}: {count} transactions ({pct_of_total:.1f}% of total)")
    
    # 4. Country performance analysis
    if 'country' in current_card:
        countries_data = []
        for country_code, country_data in current_card['country'].items():
            rate = (country_data.get('success_count', 0) / 
                   country_data.get('total_count', 1) * 100) if country_data.get('total_count', 0) > 0 else 0
            vol = country_data.get('total_count', 0)
            countries_data.append((country_code, rate, vol))
        
        # Sort by volume
        countries_data.sort(key=lambda x: x[2], reverse=True)
        
        if countries_data:
            insights.append("")
            insights.append("🌍 Top Markets Performance:")
            
            for country_code, rate, vol in countries_data[:3]:
                if rate < 50:
                    warnings.append(f"⚠️  {country_code} success rate is critically low ({rate:.1f}%)")
                insights.append(f"  • {country_code}: {rate:.1f}% success rate, {vol} transactions")
    
    # 5. Bank performance analysis
    if 'bank' in current_card:
        bank_data = []
        for bank_name, bank_info in current_card['bank'].items():
            rate = (bank_info.get('success_count', 0) / 
                   bank_info.get('total_count', 1) * 100) if bank_info.get('total_count', 0) > 0 else 0
            vol = bank_info.get('total_count', 0)
            bank_name_clean = bank_name.split('_')[0] if '_' in bank_name else bank_name
            bank_data.append((bank_name_clean, rate, vol))
        
        # Sort by volume
        bank_data.sort(key=lambda x: x[2], reverse=True)
        
        if bank_data:
            insights.append("")
            insights.append("🏦 Top Banks Performance:")
            
            for bank_name, rate, vol in bank_data[:3]:
                insights.append(f"  • {bank_name}: {rate:.1f}% success rate, {vol} transactions")
    
    # 6. Additional warnings
    if warnings:
        warnings.insert(0, "🚨 WARNINGS REQUIRING IMMEDIATE ATTENTION:")
        warnings.append("")
    
    return "\n".join(warnings + insights) if warnings else "\n".join(insights)


def analyze_apm_risks(current_data, previous_data):
    """Analyze APM payment risks and generate intelligent insights"""
    if not current_data or 'apm' not in current_data:
        return "No APM payment data available for analysis"
    
    insights = []
    warnings = []
    
    current_apm = current_data['apm']
    prev_apm = previous_data.get('apm', {}) if previous_data else {}
    
    # 1. Overall success rate analysis
    if 'total' in current_apm:
        current_rate = (current_apm['total'].get('success_count', 0) / 
                       current_apm['total'].get('total_count', 1) * 100)
        
        prev_rate = 0
        if 'total' in prev_apm and prev_apm['total'].get('total_count', 0) > 0:
            prev_rate = (prev_apm['total'].get('success_count', 0) / 
                        prev_apm['total'].get('total_count', 1) * 100)
        
        rate_change = current_rate - prev_rate
        
        if prev_rate > 0:
            if abs(rate_change) > 10:
                warnings.append(f"⚠️  CRITICAL: APM success rate {'dropped' if rate_change < 0 else 'increased'} by {abs(rate_change):.1f}% compared to yesterday")
            elif abs(rate_change) > 5:
                insights.append(f"📊 APM success rate {'decreased' if rate_change < 0 else 'increased'} by {abs(rate_change):.1f}% compared to yesterday")
        
        if current_rate < 60:
            warnings.append(f"🚨 CRITICAL: APM success rate is critically low at {current_rate:.1f}%")
        elif current_rate < 70:
            warnings.append(f"⚠️  WARNING: APM success rate is below acceptable threshold at {current_rate:.1f}%")
        elif current_rate < 80:
            insights.append(f"📈 APM success rate is at {current_rate:.1f}% - room for improvement")
        else:
            insights.append(f"✅ APM success rate is healthy at {current_rate:.1f}%")
        
        insights.append(f"📊 Volume: {current_apm['total'].get('total_count', 0)} total, {current_apm['total'].get('success_count', 0)} successful")
    
    # 2. System type analysis
    if 'system_type' in current_apm:
        system_data = []
        for system_type, system_info in current_apm['system_type'].items():
            rate = (system_info.get('success_count', 0) / 
                   system_info.get('total_count', 1) * 100) if system_info.get('total_count', 0) > 0 else 0
            vol = system_info.get('total_count', 0)
            system_data.append((system_type, rate, vol))
        
        # Sort by volume
        system_data.sort(key=lambda x: x[2], reverse=True)
        
        if system_data:
            insights.append("")
            insights.append("💻 System Type Performance:")
            
            min_rate = min([s[1] for s in system_data])
            if min_rate < 60:
                low_systems = [s[0] for s in system_data if s[1] < 60]
                warnings.append(f"⚠️  {', '.join(low_systems)} system type(s) have critically low success rates (<60%)")
            
            for system_type, rate, vol in system_data:
                insights.append(f"  • {system_type.replace('_', ' ').title()}: {rate:.1f}% success rate, {vol} transactions")
    
    # 3. Error code analysis
    if 'error_code' in current_apm:
        current_errors = {k: v for k, v in current_apm['error_code'].items() 
                         if k != 'pay_success' and v > 0}
        prev_errors = {k: v for k, v in prev_apm.get('error_code', {}).items() 
                      if k != 'pay_success' and v > 0}
        
        if current_errors:
            insights.append("")
            insights.append("❌ Error Code Analysis:")
            
            # Sort by count
            sorted_errors = sorted(current_errors.items(), key=lambda x: x[1], reverse=True)
            
            for error_code, count in sorted_errors[:3]:
                prev_count = prev_errors.get(error_code, 0)
                change_pct = ((count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                if prev_count > 0:
                    if change_pct > 100:
                        warnings.append(f"🚨 {error_code} has increased by {change_pct:.0f}% - INVESTIGATE IMMEDIATELY")
                    elif change_pct > 50:
                        warnings.append(f"⚠️  {error_code} has increased by {change_pct:.0f}% - monitor closely")
                
                pct_of_total = (count / current_apm['total'].get('total_count', 1) * 100)
                insights.append(f"  • {error_code}: {count} transactions ({pct_of_total:.1f}%)")
    
    # 4. Additional warnings
    if warnings:
        warnings.insert(0, "🚨 WARNINGS REQUIRING IMMEDIATE ATTENTION:")
        warnings.append("")
    
    return "\n".join(warnings + insights) if warnings else "\n".join(insights)


def send_email_with_attachment(smtp_config, recipient, subject, body, attachment_path):
    """
    Send email with attachment
    
    Args:
        smtp_config: SMTP configuration dictionary
        recipient: Recipient email address
        subject: Email subject
        body: Email body
        attachment_path: Attachment path
    """
    # Create email object
    msg = MIMEMultipart()
    msg['From'] = smtp_config['username']
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Add email body
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Add attachment
    if os.path.exists(attachment_path):
        filename = os.path.basename(attachment_path)
        
        # Guess file type
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)
        
        with open(attachment_path, 'rb') as f:
            mime = MIMEBase(maintype, subtype)
            mime.set_payload(f.read())
            
        encoders.encode_base64(mime)
        mime.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(mime)
        
        print(f"Attachment added: {filename}")
    else:
        print(f"Warning: Attachment file not found: {attachment_path}")
    
    # Connect to SMTP server and send email
    try:
        print(f"Connecting to SMTP server {smtp_config['smtp_server']}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
        
        # Enable TLS if needed
        if smtp_config.get('use_tls', True):
            server.starttls()
        
        # Login
        server.login(smtp_config['username'], smtp_config['password'])
        print("Login successful")
        
        # Send email
        text = msg.as_string()
        server.sendmail(smtp_config['username'], recipient, text)
        print(f"Email successfully sent to: {recipient}")
        
        # Close connection
        server.quit()
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"Error: SMTP authentication failed, please check username and password: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"Error: Email sending failed: {e}")
        return False
    except Exception as e:
        print(f"Error: Unknown error occurred while sending email: {e}")
        return False


def generate_email_content(date_str, executive_summary_path):
    """Generate email content with executive summary"""
    # Read executive summary from file
    try:
        with open(executive_summary_path, 'r', encoding='utf-8') as f:
            executive_summary = f.read()
    except:
        executive_summary = "Executive Summary is not available."
    
    content = f"""Dear Merchant,

Please find attached your Payment Success Rate Report for {date_str}:

{'=' * 60}
EXECUTIVE SUMMARY
{'=' * 60}

{executive_summary}

{'=' * 60}
DETAILED REPORT ATTACHED
{'=' * 60}

The attached PDF contains complete analysis including:
• Comprehensive success rate trends and comparisons
• Detailed error code distribution charts
• Country and bank performance breakdowns
• System type analysis for APM payments
• Historical data comparisons and actionable recommendations

Please review the detailed report for full insights.

Best regards,
Antom Payment Success Rate Analytics System

This is an automated report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."""
    return content


def main():
    parser = argparse.ArgumentParser(description='Send payment success rate report email with intelligent analysis')
    parser.add_argument('--date', required=True, help='Report date, format: YYYYMMDD')
    parser.add_argument('--recipient', required=True, help='Recipient email address')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, "%Y%m%d")
    except ValueError:
        print(f"Error: Date format is incorrect, should be YYYYMMDD format")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    merchant_id = config.get("merchant_id")
    if not merchant_id:
        print("Error: merchant_id is missing from configuration file")
        sys.exit(1)
    
    email_conf = config.get("email_conf")
    if not email_conf:
        print("Error: email_conf is missing from configuration file")
        sys.exit(1)
    
    # Validate email_conf fields
    required_fields = ["smtp_server", "smtp_port", "username", "password"]
    for field in required_fields:
        if field not in email_conf:
            print(f"Error: email_conf is missing required field: {field}")
            sys.exit(1)
    
    # Get report file path
    report_file_path = get_report_file_path(args.date, merchant_id)
    if not os.path.exists(report_file_path):
        print(f"Error: Report file not found: {report_file_path}")
        print(f"Please confirm that the report for {args.date} has been generated using analyse_and_gen_report tool")
        sys.exit(1)
    
    # Get executive summary file path
    executive_summary_path = get_executive_summary_path(args.date)
    if not os.path.exists(executive_summary_path):
        print(f"Warning: Executive summary not found: {executive_summary_path}")
    
    # Generate email content
    subject = f"{args.date}-Payment Success Rate Report"
    body = generate_email_content(args.date, executive_summary_path)
    
    # Send email
    print(f"Sending {args.date} payment success rate report to {args.recipient}...")
    success = send_email_with_attachment(email_conf, args.recipient, subject, body, report_file_path)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Email sending failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
