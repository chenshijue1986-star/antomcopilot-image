#!/usr/bin/env python3
"""
Antom Payment Success Rate Report Generator
Analyzes payment success rate data and generates PDF report with comprehensive executive summary
"""

import argparse
import json
import os
import sys
import platform
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import numpy as np


# Font configuration for English
ENGLISH_FONT_PATHS = {
    "Darwin": "/System/Library/Fonts/Helvetica.ttc",
    "Windows": "C:/Windows/Fonts/arial.ttf"
}


def register_font():
    """Register font (fallback to default if needed)"""
    system = platform.system()
    font_path = ENGLISH_FONT_PATHS.get(system, ENGLISH_FONT_PATHS["Darwin"])
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Helvetica', font_path))
            return True
        except Exception:
            pass
    return False


register_font()

# Path utilities
CONFIG_PATH = os.path.join(os.path.expanduser("~/antom"), "antom_conf.json")


def load_config():
    """Load configuration"""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_report_paths(date_str):
    """Get report directory and file paths"""
    base_dir = os.path.expanduser("~/antom/success rate")
    report_dir = os.path.join(base_dir, date_str)
    images_dir = os.path.join(report_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    pdf_path = os.path.join(report_dir, f"{date_str}-Payment-Success-Rate-Report-<<merchant_id>>.pdf")
    return report_dir, images_dir, pdf_path


# Data loading
def load_raw_data(date_str):
    """Load raw data"""
    data_file = os.path.expanduser(f"~/antom/success rate/{date_str}_raw_data.json")
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_previous_data(date_str, days_back=1):
    """Load previous day's data"""
    try:
        current_date = datetime.strptime(date_str, "%Y%m%d")
        previous_date = current_date - timedelta(days=days_back)
        return load_raw_data(previous_date.strftime("%Y%m%d"))
    except:
        return None


# Data extraction
def extract_card_data(raw_data):
    """Extract Card data and calculate success rates"""
    card = raw_data.get("card", {})
    
    # Calculate overall success rate
    total = card.get("total", {})
    if total:
        total["success_rate"] = (total["success_count"] / total["total_count"] * 100) if total.get("total_count", 0) > 0 else 0
    
    # Calculate success rates for auth types
    for key, data in card.get("auth", {}).items():
        data["success_rate"] = (data["success_count"] / data["total_count"] * 100) if data.get("total_count", 0) > 0 else 0
    
    # Calculate success rates for countries
    for key, data in card.get("country", {}).items():
        data["success_rate"] = (data["success_count"] / data["total_count"] * 100) if data.get("total_count", 0) > 0 else 0
    
    # Calculate success rates for banks
    for key, data in card.get("bank", {}).items():
        data["success_rate"] = (data["success_count"] / data["total_count"] * 100) if data.get("total_count", 0) > 0 else 0
    
    return card


def extract_apm_data(raw_data):
    """Extract APM data and calculate success rates"""
    apm = raw_data.get("apm", {})
    
    # Calculate overall success rate
    total = apm.get("total", {})
    if total:
        total["success_rate"] = (total["success_count"] / total["total_count"] * 100) if total.get("total_count", 0) > 0 else 0
    
    # Calculate system type success rates
    for key, data in apm.get("system_type", {}).items():
        data["success_rate"] = (data["success_count"] / data["total_count"] * 100) if data.get("total_count", 0) > 0 else 0
    
    return apm


# Chart generation
def draw_success_rate_chart(data_list, labels, title, save_path):
    """Draw success rate trend chart"""
    fig, ax1 = plt.subplots(figsize=(6, 4))
    
    # Prepare data
    total_amounts = [d.get("total_count", 0) for d in data_list]
    success_amounts = [d.get("success_count", 0) for d in data_list]
    success_rates = [d.get("success_rate", 0) for d in data_list]
    
    # Bar chart - Transaction volume
    x = np.arange(len(labels))
    ax1.bar(x - 0.2, total_amounts, 0.4, label='Total', color='lightblue')
    ax1.bar(x + 0.2, success_amounts, 0.4, label='Success', color='lightgreen')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Volume')
    ax1.set_title(title)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend(loc='upper left')
    
    # Line chart - Success rate
    ax2 = ax1.twinx()
    ax2.plot(x, success_rates, 'r-o', linewidth=2, markersize=6, label='Success Rate')
    ax2.set_ylabel('Success Rate (%)')
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    return save_path


def draw_pie_chart(data, exclude_key, title, save_path):
    """Draw error code pie chart (with legend)"""
    labels = []
    values = []
    
    for key, value in data.items():
        if key != exclude_key and value > 0:
            labels.append(key.replace("_", " ").title())
            values.append(value)
    
    if not values:
        return None
    
    plt.figure(figsize=(8, 8))
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0'][:len(labels)]
    
    patches, _, _ = plt.pie(values, labels=None, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.legend(patches, labels, loc="best", fontsize=9, bbox_to_anchor=(1, 0.5))
    plt.title(title, pad=20)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    return save_path


# Analysis summary
def generate_analysis_summary(section_name, current_data, previous_data, week_data):
    """Generate analysis summary and recommendations"""
    summary = {}
    
    if section_name == "card_overall":
        current_rate = current_data.get("total", {}).get("success_rate", 0)
        previous_rate = previous_data.get("total", {}).get("success_rate", 0) if previous_data else current_rate
        week_rate = week_data.get("total", {}).get("success_rate", 0) if week_data else current_rate
        
        daily_change = current_rate - previous_rate
        
        if daily_change > 5:
            summary["analysis"] = f"Payment success rate significantly improved compared to yesterday ({daily_change:+.1f}%), excellent performance."
        elif daily_change < -5:
            summary["analysis"] = f"Payment success rate significantly decreased compared to yesterday ({daily_change:+.1f}%), attention required."
        else:
            summary["analysis"] = f"Payment success rate remained stable compared to yesterday ({daily_change:+.1f}%), stable operation."
        
        summary["recommendation"] = (
            "Focus on analyzing error code distribution and investigating system or partner issues." if current_rate < 70 else
            "Optimize 3DS authentication flow to reduce user drop-off." if current_rate < 85 else
            "Current success rate is good, recommend continuous monitoring and maintaining stability."
        )
    
    elif section_name == "card_auth":
        rate_3ds = current_data.get("auth", {}).get("3ds", {}).get("success_rate", 0)
        rate_non3ds = current_data.get("auth", {}).get("non_3ds", {}).get("success_rate", 0)
        
        summary["analysis"] = f"3DS Success Rate: {rate_3ds:.1f}%, Non-3DS Success Rate: {rate_non3ds:.1f}%."
        summary["recommendation"] = (
            "Optimize 3DS process to reduce user operation steps." if rate_3ds < rate_non3ds - 10 else
            "Dynamically adjust Auth strategy based on different risk levels."
        )
    
    elif section_name in ["card_error", "apm_error"]:
        errors = {k: v for k, v in current_data.get("error_code", {}).items() if k != "pay_success"}
        total_errors = sum(errors.values())
        
        summary["analysis"] = f"Total Errors: {total_errors} transactions. Main Errors: {', '.join([f'{k}({v})' for k, v in list(errors.items())[:3]])}."
        summary["recommendation"] = (
            "Optimize error prompts to guide users to retry." if section_name == "apm_error" and total_errors > 20 else
            "Prioritize handling timeout_close errors and check timeout settings." if total_errors > 50 else
            "Monitor error code trends daily to detect anomalies in time."
        )
    
    elif section_name == "card_country":
        countries = current_data.get("country", {})
        low_rate = [f"{k}({v['success_rate']:.1f}%)" for k, v in countries.items() if v["success_rate"] < 70]
        
        summary["analysis"] = f"Low Success Rate Countries: {', '.join(low_rate)}." if low_rate else "Country success rates are normal with healthy regional distribution."
        summary["recommendation"] = "Check local payment habits and partner performance." if low_rate else "Continuously monitor success rate changes by country."
    
    elif section_name == "card_bank":
        banks = current_data.get("bank", {})
        low_rate = [f"{k.split('_')[0]}({v['success_rate']:.1f}%" for k, v in banks.items() if v["success_rate"] < 70]
        
        summary["analysis"] = f"Low Performing Banks: {', '.join(low_rate)}." if low_rate else "All bank channels performing stably."
        summary["recommendation"] = "Investigate technical integration issues." if low_rate else "Deepen cooperation with top-tier banks."
    
    elif section_name == "apm_overall":
        current_rate = current_data.get("total", {}).get("success_rate", 0)
        previous_rate = previous_data.get("total", {}).get("success_rate", 0) if previous_data else current_rate
        
        daily_change = current_rate - previous_rate
        summary["analysis"] = f"APM success rate {'improved' if daily_change > 0 else 'decreased'} compared to yesterday ({daily_change:+.1f}%)."
        summary["recommendation"] = (
            "Focus on analyzing timeout_close errors and optimizing payment flow." if current_rate < 70 else
            "Enrich payment methods to meet different user needs."
        )
    
    elif section_name == "apm_system":
        systems = current_data.get("system_type", {})
        web, wap, system = [systems.get(k, {}).get("success_rate", 0) for k in ["web", "wap", "system"]]
        
        summary["analysis"] = f"Web: {web:.1f}%, WAP: {wap:.1f}%, System: {system:.1f}%."
        min_rate = min(web, wap, system)
        summary["recommendation"] = "Investigate channels with success rate below 70%." if min_rate < 70 else "Recommend optimal payment methods based on device type."
    
    return summary


# Executive summary generation - COMPREHENSIVE VERSION
def generate_executive_summary(card_data, apm_data, card_prev, apm_prev):
    """Generate Executive Summary with comprehensive coverage of ALL sections"""
    critical_issues = []
    warnings = []
    observations = []
    recommendations = []
    
    # Extract previous data for comparison
    prev_card = card_prev or {}
    prev_apm = apm_prev or {}
    
    # ===== 1. OVERALL SUCCESS RATE ANALYSIS =====
    
    # Card overall
    if 'total' in card_data:
        card_rate = card_data['total'].get('success_rate', 0)
        prev_card_rate = prev_card.get('total', {}).get('success_rate', 0) if prev_card else card_rate
        rate_change = card_rate - prev_card_rate
        
        if prev_card_rate > 0:
            if rate_change < -10:
                critical_issues.append(f"Card payment success rate dropped {abs(rate_change):.1f}% - immediate investigation required")
            elif rate_change < -5:
                warnings.append(f"Card payment success rate decreased by {abs(rate_change):.1f}% compared to yesterday")
        
        if card_rate < 60:
            critical_issues.append(f"Card payment success rate critically low at {card_rate:.1f}%")
        elif card_rate < 70:
            warnings.append(f"Card payment success rate below threshold at {card_rate:.1f}%")
        elif card_rate >= 80:
            observations.append("Card payment performance is healthy")
    
    # APM overall
    if 'total' in apm_data:
        apm_rate = apm_data['total'].get('success_rate', 0)
        prev_apm_rate = prev_apm.get('total', {}).get('success_rate', 0) if prev_apm else apm_rate
        apm_change = apm_rate - prev_apm_rate
        
        if prev_apm_rate > 0:
            if apm_change < -10:
                critical_issues.append(f"APM payment success rate dropped {abs(apm_change):.1f}% - immediate investigation required")
            elif apm_change < -5:
                warnings.append(f"APM payment success rate decreased by {abs(apm_change):.1f}% compared to yesterday")
        
        if apm_rate < 60:
            critical_issues.append(f"APM payment success rate critically low at {apm_rate:.1f}%")
        elif apm_rate < 70:
            warnings.append(f"APM payment success rate below threshold at {apm_rate:.1f}%")
        elif apm_rate >= 80:
            observations.append("APM payment performance is healthy")
    
    # ===== 2. AUTHENTICATION ANALYSIS (Card) =====
    
    if 'auth' in card_data and '3ds' in card_data['auth'] and 'non_3ds' in card_data['auth']:
        rate_3ds = card_data['auth']['3ds'].get('success_rate', 0)
        rate_non3ds = card_data['auth']['non_3ds'].get('success_rate', 0)
        vol_3ds = card_data['auth']['3ds'].get('total_count', 0)
        vol_non3ds = card_data['auth']['non_3ds'].get('total_count', 0)
        total_auth = vol_3ds + vol_non3ds
        
        if total_auth > 0:
            pct_3ds = (vol_3ds / total_auth) * 100
            
            # 3DS success rate much lower than non-3DS
            if rate_non3ds > 0 and rate_3ds < rate_non3ds - 15:
                critical_issues.append(f"3DS authentication success rate ({rate_3ds:.1f}%) significantly lower than Non-3DS ({rate_non3ds:.1f}%)")
                recommendations.append("Urgent: Review and optimize 3DS authentication flow")
            
            # High 3DS usage
            if pct_3ds > 30:
                warnings.append(f"High 3DS usage ({pct_3ds:.1f}%) may cause user friction")
                recommendations.append("Consider reducing 3DS usage for low-risk transactions")
            
            # Low 3DS success rate
            if rate_3ds < 50:
                warnings.append(f"3DS success rate is poor at {rate_3ds:.1f}%")
                recommendations.append("Investigate 3DS technical integration and user experience")
    
    # ===== 3. ERROR CODE ANALYSIS (Card & APM) =====
    
    # Card errors
    if 'error_code' in card_data:
        current_errors = {k: v for k, v in card_data['error_code'].items() 
                         if k != 'pay_success' and v > 0}
        prev_errors = {k: v for k, v in prev_card.get('error_code', {}).items() 
                      if k != 'pay_success' and v > 0}
        
        if current_errors:
            # Sort by count to get top errors
            sorted_errors = sorted(current_errors.items(), key=lambda x: x[1], reverse=True)
            prev_error_dict = prev_errors  # Already a dict
            
            for error_code, count in sorted_errors[:3]:
                prev_count = prev_error_dict.get(error_code, 0)
                if prev_count > 0:
                    change_pct = ((count - prev_count) / prev_count) * 100
                    
                    if change_pct > 100:
                        critical_issues.append(f"Card {error_code} errors surged {change_pct:.0f}% - potential system issue")
                        recommendations.append(f"Immediate investigation required for {error_code}")
                    elif change_pct > 50:
                        warnings.append(f"Card {error_code} errors increased {change_pct:.0f}%")
                        recommendations.append(f"Monitor {error_code} and investigate root cause")
                elif count > 20:  # New error with significant volume
                    warnings.append(f"Card {error_code} detected with {count} occurrences")
                    recommendations.append(f"Analyze {error_code} and implement fix")
    
    # APM errors
    if 'error_code' in apm_data:
        current_errors = {k: v for k, v in apm_data['error_code'].items() 
                         if k != 'pay_success' and v > 0}
        prev_errors = {k: v for k, v in prev_apm.get('error_code', {}).items() 
                      if k != 'pay_success' and v > 0}
        
        if current_errors:
            sorted_errors = sorted(current_errors.items(), key=lambda x: x[1], reverse=True)
            prev_error_dict = prev_errors  # Already a dict
            
            for error_code, count in sorted_errors[:3]:
                prev_count = prev_error_dict.get(error_code, 0)
                if prev_count > 0:
                    change_pct = ((count - prev_count) / prev_count) * 100
                    
                    if change_pct > 100:
                        critical_issues.append(f"APM {error_code} errors surged {change_pct:.0f}% - immediate action needed")
                        recommendations.append(f"Urgent: Investigate and resolve {error_code}")
                    elif change_pct > 50:
                        warnings.append(f"APM {error_code} errors increased {change_pct:.0f}%")
                        recommendations.append(f"Review {error_code} handling process")
                elif count > 30:
                    warnings.append(f"APM {error_code} detected with significant volume ({count})")
                    recommendations.append(f"Implement solution for {error_code}")
    
    # ===== 4. COUNTRY PERFORMANCE ANALYSIS (Card) =====
    
    if 'country' in card_data:
        low_performing_countries = []
        for country_code, country_data in card_data['country'].items():
            rate = country_data.get('success_rate', 0)
            volume = country_data.get('total_count', 0)
            
            if rate < 50 and volume > 10:  # Low rate with significant volume
                low_performing_countries.append(f"{country_code} ({rate:.1f}%)")
        
        if low_performing_countries:
            warnings.append(f"Poor performance in markets: {', '.join(low_performing_countries[:3])}")
            recommendations.append("Review local payment partners and user experience in underperforming markets")
    
    # ===== 5. BANK PERFORMANCE ANALYSIS (Card) =====
    
    if 'bank' in card_data:
        low_performing_banks = []
        for bank_name, bank_data in card_data['bank'].items():
            rate = bank_data.get('success_rate', 0)
            volume = bank_data.get('total_count', 0)
            
            if rate < 60 and volume > 10:
                bank_name_clean = bank_name.split('_')[0] if '_' in bank_name else bank_name
                low_performing_banks.append(f"{bank_name_clean} ({rate:.1f}%)")
        
        if low_performing_banks:
            warnings.append(f"Underperforming banks: {', '.join(low_performing_banks[:3])}")
            recommendations.append("Investigate technical integration with low-performing banks")
    
    # ===== 6. SYSTEM TYPE ANALYSIS (APM) =====
    
    if 'system_type' in apm_data:
        low_performing_systems = []
        for system_type, system_data in apm_data['system_type'].items():
            rate = system_data.get('success_rate', 0)
            volume = system_data.get('total_count', 0)
            
            if rate < 60 and volume > 10:
                low_performing_systems.append(f"{system_type} ({rate:.1f}%)")
        
        if low_performing_systems:
            warnings.append(f"Low success rate in channels: {', '.join(low_performing_systems)}")
            recommendations.append("Investigate and optimize underperforming payment channels")
    
    # ===== 7. VOLUME ANALYSIS =====
    
    # Check for unusual volume patterns
    card_total_today = card_data.get('total', {}).get('total_count', 0)
    card_total_yesterday = prev_card.get('total', {}).get('total_count', 0) if prev_card else card_total_today
    
    if card_total_yesterday > 0:
        volume_change = ((card_total_today - card_total_yesterday) / card_total_yesterday) * 100
        if abs(volume_change) > 50:
            observations.append(f"Significant volume change detected: {volume_change:+.1f}%")
    
    # ===== COMPILE FINAL SUMMARY =====
    
    full_summary = []
    
    # Critical issues (always show first)
    if critical_issues:
        full_summary.append("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ACTION:")
        for issue in critical_issues[:4]:  # Max 4 critical issues
            full_summary.append(f"• {issue}")
        full_summary.append("")
    
    # Key risks and warnings
    if warnings:
        full_summary.append("⚠️  KEY RISKS AND CONCERNS:")
        for warning in warnings[:5]:  # Max 5 warnings
            full_summary.append(f"• {warning}")
        full_summary.append("")
    
    # Recommendations
    if recommendations:
        full_summary.append("💡 RECOMMENDED ACTIONS:")
        for rec in recommendations[:6]:  # Max 6 recommendations
            full_summary.append(f"• {rec}")
        full_summary.append("")
    
    # Positive observations
    if observations:
        full_summary.append("✅ POSITIVE PERFORMANCE:")
        for obs in observations[:3]:  # Max 3 observations
            full_summary.append(f"• {obs}")
        full_summary.append("")
    
    # If no issues
    if not critical_issues and not warnings:
        full_summary.append("✅ No critical issues detected. Overall performance is stable.")
        full_summary.append("")
    
    full_summary.append("📋 Detailed analysis and recommendations are provided in the following sections.")
    
    return "\n".join(full_summary)


# Table generation
def create_simple_table(data, headers):
    """Create a unified style table"""
    table_data = [headers] + data
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica')
    ]))
    return t


# Main report generation
def generate_pdf_report(date_str, merchant_id, config):
    """Generate PDF report"""
    # Load data
    current_data = load_raw_data(date_str)
    previous_data = load_previous_data(date_str, 1)
    week_data = [load_previous_data(date_str, i) for i in range(1, 8)]
    
    # Extract data
    card = extract_card_data(current_data)
    card_prev = extract_card_data(previous_data) if previous_data else None
    card_week = extract_card_data(week_data[0]) if week_data and week_data[0] else None
    
    apm = extract_apm_data(current_data)
    apm_prev = extract_apm_data(previous_data) if previous_data else None
    apm_week = extract_apm_data(week_data[0]) if week_data and week_data[0] else None
    
    # Create document
    report_dir, images_dir, pdf_template = get_report_paths(date_str)
    pdf_path = pdf_template.replace("<<merchant_id>>", merchant_id)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                          rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20)
    heading1_style = ParagraphStyle('Heading1', parent=styles['Heading2'], fontSize=16, spaceAfter=10)
    heading2_style = ParagraphStyle('Heading2', parent=styles['Heading2'])
    heading3_style = ParagraphStyle('Heading3', parent=styles['Heading3'])
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'])
    exec_sum_style = ParagraphStyle('ExecSum', parent=styles['Normal'], fontSize=10, leading=14, 
                                   spaceBefore=6, spaceAfter=6)
    
    story = []
    story.append(Paragraph(f"Payment Success Rate Report - {date_str}", title_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("📊 EXECUTIVE SUMMARY", heading1_style))
    
    # Generate executive summary
    executive_summary = generate_executive_summary(card, apm, card_prev, apm_prev)
    
    # Save executive summary to file for email
    summary_file_path = os.path.join(report_dir, f"{date_str}_executive_summary.txt")
    with open(summary_file_path, 'w', encoding='utf-8') as f:
        f.write(executive_summary)
    story.append(Paragraph(executive_summary.replace("\n", "<br/>"), exec_sum_style))
    story.append(Spacer(1, 20))
    
    # Card Report
    story.append(Paragraph("Card Payment Analysis", heading2_style))
    story.append(Spacer(1, 10))
    
    # Card Overall
    story.append(Paragraph("1. Overall Payment Success Rate Analysis", heading3_style))
    card_chart_path = os.path.join(images_dir, "card_overall.png")
    draw_success_rate_chart(
        [card["total"], card_prev["total"] if card_prev else card["total"], card_week["total"] if card_week else card["total"]],
        ["Today", "Yesterday", "Week Avg"],
        "Card Overall Payment Success Rate Analysis",
        card_chart_path
    )
    story.append(Image(card_chart_path, width=6*inch, height=4*inch))
    story.append(Spacer(1, 10))
    
    card_summary = generate_analysis_summary("card_overall", card, card_prev, card_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {card_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {card_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # Card Auth
    story.append(Paragraph("2. Authentication Type Analysis", heading3_style))
    auth_3ds_today = card['auth']['3ds']['success_rate']
    auth_3ds_yesterday = card_prev['auth']['3ds']['success_rate'] if card_prev else auth_3ds_today
    auth_3ds_week = card_week['auth']['3ds']['success_rate'] if card_week else auth_3ds_today
    
    auth_non3ds_today = card['auth']['non_3ds']['success_rate']
    auth_non3ds_yesterday = card_prev['auth']['non_3ds']['success_rate'] if card_prev else auth_non3ds_today
    auth_non3ds_week = card_week['auth']['non_3ds']['success_rate'] if card_week else auth_non3ds_today
    
    auth_data = [
        ["3DS", f"{auth_3ds_today:.1f}%", f"{auth_3ds_yesterday:.1f}%", f"{auth_3ds_week:.1f}%", 
         f"{auth_3ds_today - auth_3ds_yesterday:+.1f}%", f"{auth_3ds_today - auth_3ds_week:+.1f}%"],
        ["Non-3DS", f"{auth_non3ds_today:.1f}%", f"{auth_non3ds_yesterday:.1f}%", f"{auth_non3ds_week:.1f}%",
         f"{auth_non3ds_today - auth_non3ds_yesterday:+.1f}%", f"{auth_non3ds_today - auth_non3ds_week:+.1f}%"]
    ]
    story.append(create_simple_table(auth_data, ["Auth Type", "Today", "Yesterday", "Week Avg", "Daily Change", "Weekly Change"]))
    story.append(Spacer(1, 10))
    
    auth_summary = generate_analysis_summary("card_auth", card, card_prev, card_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {auth_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {auth_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # Card Error Codes
    story.append(Paragraph("3. Error Code Analysis", heading3_style))
    card_error_pie = os.path.join(images_dir, "card_error_pie.png")
    draw_pie_chart(card.get("error_code", {}), "pay_success", "Card Error Code Distribution", card_error_pie)
    story.append(Image(card_error_pie, width=6*inch, height=6*inch))
    story.append(Spacer(1, 10))
    
    # Prepare error code data (Today, Yesterday, Week Avg)
    error_data = []
    for error_code, today_count in card.get("error_code", {}).items():
        if error_code != "pay_success" and today_count > 0:
            # Yesterday's error count
            yesterday_count = card_prev.get("error_code", {}).get(error_code, 0) if card_prev else today_count
            
            # Weekly average error count (simplified: use first day's data as average)
            week_avg_count = card_week.get("error_code", {}).get(error_code, today_count) if card_week else today_count
            
            # Calculate percentage changes
            daily_change_pct = ((today_count - yesterday_count) / yesterday_count * 100) if yesterday_count > 0 else 0
            weekly_change_pct = ((today_count - week_avg_count) / week_avg_count * 100) if week_avg_count > 0 else 0
            
            error_data.append([
                error_code.replace("_", " ").title(),
                f"{today_count}",
                f"{yesterday_count}",
                f"{week_avg_count}",
                f"{daily_change_pct:+.1f}%" if yesterday_count > 0 else "N/A",
                f"{weekly_change_pct:+.1f}%" if week_avg_count > 0 else "N/A"
            ])
    
    story.append(create_simple_table(error_data, ["Error Code", "Today", "Yesterday", "Week Avg", "Daily Change %", "Weekly Change %"]))
    story.append(Spacer(1, 10))
    
    error_summary = generate_analysis_summary("card_error", card, card_prev, card_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {error_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {error_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # Card Countries
    story.append(Paragraph("4. Card Issuing Country Analysis", heading3_style))
    country_data = []
    for country_code, country_today in card.get("country", {}).items():
        country_yesterday = card_prev.get("country", {}).get(country_code, {}).get("success_rate", country_today["success_rate"]) if card_prev else country_today["success_rate"]
        country_week = card_week.get("country", {}).get(country_code, {}).get("success_rate", country_today["success_rate"]) if card_week else country_today["success_rate"]
        
        daily_change = country_today["success_rate"] - country_yesterday
        weekly_change = country_today["success_rate"] - country_week
        
        country_data.append([
            country_code,
            f"{country_today['success_rate']:.1f}%",
            f"{country_yesterday:.1f}%",
            f"{country_week:.1f}%",
            f"{daily_change:+.1f}%",
            f"{weekly_change:+.1f}%"
        ])
    
    story.append(create_simple_table(country_data, ["Country", "Today", "Yesterday", "Week Avg", "Daily Change", "Weekly Change"]))
    story.append(Spacer(1, 10))
    
    country_summary = generate_analysis_summary("card_country", card, card_prev, card_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {country_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {country_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # Card Banks
    story.append(Paragraph("5. Card Issuing Bank Analysis", heading3_style))
    bank_data = []
    for bank_name, bank_today in card.get("bank", {}).items():
        bank_yesterday = card_prev.get("bank", {}).get(bank_name, {}).get("success_rate", bank_today["success_rate"]) if card_prev else bank_today["success_rate"]
        bank_week = card_week.get("bank", {}).get(bank_name, {}).get("success_rate", bank_today["success_rate"]) if card_week else bank_today["success_rate"]
        
        daily_change = bank_today["success_rate"] - bank_yesterday
        weekly_change = bank_today["success_rate"] - bank_week
        
        bank_data.append([
            bank_name.split('_')[0],
            f"{bank_today['success_rate']:.1f}%",
            f"{bank_yesterday:.1f}%",
            f"{bank_week:.1f}%",
            f"{daily_change:+.1f}%",
            f"{weekly_change:+.1f}%"
        ])
    
    story.append(create_simple_table(bank_data, ["Bank", "Today", "Yesterday", "Week Avg", "Daily Change", "Weekly Change"]))
    story.append(Spacer(1, 10))
    
    bank_summary = generate_analysis_summary("card_bank", card, card_prev, card_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {bank_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {bank_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("<hr/>", normal_style))
    story.append(Spacer(1, 20))
    
    # APM Report
    story.append(Paragraph("APM Payment Analysis", heading2_style))
    story.append(Spacer(1, 10))
    
    # APM Overall
    story.append(Paragraph("1. Overall Payment Success Rate Analysis", heading3_style))
    apm_chart_path = os.path.join(images_dir, "apm_overall.png")
    draw_success_rate_chart(
        [apm["total"], apm_prev["total"] if apm_prev else apm["total"], apm_week["total"] if apm_week else apm["total"]],
        ["Today", "Yesterday", "Week Avg"],
        "APM Overall Payment Success Rate Analysis",
        apm_chart_path
    )
    story.append(Image(apm_chart_path, width=6*inch, height=4*inch))
    story.append(Spacer(1, 10))
    
    apm_summary = generate_analysis_summary("apm_overall", apm, apm_prev, apm_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {apm_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {apm_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # APM Error Codes
    story.append(Paragraph("2. Error Code Analysis", heading3_style))
    apm_error_pie = os.path.join(images_dir, "apm_error_pie.png")
    draw_pie_chart(apm.get("error_code", {}), "pay_success", "APM Error Code Distribution", apm_error_pie)
    story.append(Image(apm_error_pie, width=6*inch, height=6*inch))
    story.append(Spacer(1, 10))
    
    # APM Error Code Data (Today, Yesterday, Week Avg)
    apm_error_data = []
    for error_code, today_count in apm.get("error_code", {}).items():
        if error_code != "pay_success" and today_count > 0:
            yesterday_count = apm_prev.get("error_code", {}).get(error_code, 0) if apm_prev else today_count
            week_avg_count = apm_week.get("error_code", {}).get(error_code, today_count) if apm_week else today_count
            
            # Calculate percentage changes
            daily_change_pct = ((today_count - yesterday_count) / yesterday_count * 100) if yesterday_count > 0 else 0
            weekly_change_pct = ((today_count - week_avg_count) / week_avg_count * 100) if week_avg_count > 0 else 0
            
            apm_error_data.append([
                error_code.replace("_", " ").title(),
                f"{today_count}",
                f"{yesterday_count}",
                f"{week_avg_count}",
                f"{daily_change_pct:+.1f}%" if yesterday_count > 0 else "N/A",
                f"{weekly_change_pct:+.1f}%" if week_avg_count > 0 else "N/A"
            ])
    
    story.append(create_simple_table(apm_error_data, ["Error Code", "Today", "Yesterday", "Week Avg", "Daily Change %", "Weekly Change %"]))
    story.append(Spacer(1, 10))
    
    apm_error_summary = generate_analysis_summary("apm_error", apm, apm_prev, apm_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {apm_error_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {apm_error_summary['recommendation']}", normal_style))
    story.append(Spacer(1, 20))
    
    # APM System Types
    story.append(Paragraph("3. System Type Analysis", heading3_style))
    apm_system_data = []
    for system_type, system_today in apm.get("system_type", {}).items():
        system_yesterday = apm_prev.get("system_type", {}).get(system_type, {}).get("success_rate", system_today["success_rate"]) if apm_prev else system_today["success_rate"]
        system_week = apm_week.get("system_type", {}).get(system_type, {}).get("success_rate", system_today["success_rate"]) if apm_week else system_today["success_rate"]
        
        daily_change = system_today["success_rate"] - system_yesterday
        weekly_change = system_today["success_rate"] - system_week
        
        apm_system_data.append([
            system_type.replace("_", " ").title(),
            f"{system_today['success_rate']:.1f}%",
            f"{system_yesterday:.1f}%",
            f"{system_week:.1f}%",
            f"{daily_change:+.1f}%",
            f"{weekly_change:+.1f}%"
        ])
    
    story.append(create_simple_table(apm_system_data, ["System Type", "Today", "Yesterday", "Week Avg", "Daily Change", "Weekly Change"]))
    story.append(Spacer(1, 10))
    
    apm_system_summary = generate_analysis_summary("apm_system", apm, apm_prev, apm_week)
    story.append(Paragraph(f"<b>Analysis Summary:</b> {apm_system_summary['analysis']}", normal_style))
    story.append(Paragraph(f"<b>Recommendations:</b> {apm_system_summary['recommendation']}", normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF report generated: {pdf_path}")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description='Generate payment success rate PDF report')
    parser.add_argument('--date', required=True, help='Date: YYYYMMDD')
    args = parser.parse_args()
    
    config = load_config()
    generate_pdf_report(args.date, config["merchant_id"], config)


if __name__ == "__main__":
    main()
