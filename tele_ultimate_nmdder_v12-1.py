#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TeleUltimate NMDDER - Complete Edition (Termux Optimized) - FINAL FIX
Version: 12.0.3 (No Updates Mode + Session Clean)
Developer: @NMDDER_DEV | Modified for Termux

Description:
    أداة شاملة لإدارة حسابات Telegram وأتمتة المهام المختلفة
    مصممة للعمل على Termux والبيئات المحمولة
    تدعم إدارة متعددة للحسابات والمجموعات والرسائل

Features:
    - إدارة حسابات متعددة (إضافة، فحص، نسخ احتياطي)
    - أدوات المراسلة (إرسال جماعي، جدولة، ردود تلقائية)
    - جمع وإضافة الأعضاء (Scraping & Adding)
    - إدارة المجموعات والقنوات
"""

# =============================================================================
# المكتبات الأساسية - Standard Libraries
# =============================================================================

import os
import sys
import csv
import time
import random
import asyncio
import traceback
import configparser
import subprocess
import re
import json
import shutil
import logging
from datetime import datetime, timedelta
from time import sleep

# =============================================================================
# إعدادات السجل - Logging Configuration
# =============================================================================

# إخفاء أخطاء Pyrogram لتقليل الضوضاء في السجل
logging.getLogger('pyrogram').setLevel(logging.ERROR)

# =============================================================================
# معالج استثناءات asyncio - Asyncio Exception Handler
# =============================================================================

def silence_peer_error(loop, context):
    """
    معالج مخصص لإخفاء أخطاء 'Peer id invalid' الشائعة في Pyrogram
    
    Args:
        loop: حلقة الأحداث asyncio الحالية
        context: سياق الاستثناء
    """
    if 'Peer id invalid' in str(context.get('exception')):
        return
    loop.default_exception_handler(context)

# =============================================================================
# تثبيت المكتبات المفقودة - Auto-install Missing Packages
# =============================================================================

def install_package(package: str) -> bool:
    """
    تثبيت مكتبة Python تلقائياً باستخدام pip
    
    Args:
        package: اسم المكتبة المراد تثبيتها
    
    Returns:
        bool: True إذا نجح التثبيت، False إذا فشل
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

# =============================================================================
# التحقق من وتثبيت مكتبات واجهة المستخدم - UI Libraries
# =============================================================================

try:
    import pyfiglet
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    # تعريف اختصارات الألوان للاستخدام السريع
    r, g, rs, w, cy, ye, mag, bl = (
        Fore.RED,      # r - أحمر (خطأ)
        Fore.GREEN,    # g - أخضر (نجاح)
        Fore.RESET,    # rs - إعادة تعيين
        Fore.WHITE,    # w - أبيض
        Fore.CYAN,     # cy - سماوي
        Fore.YELLOW,   # ye - أصفر
        Fore.MAGENTA,  # mag - أرجواني
        Fore.BLUE      # bl - أزرق
    )
except ImportError:
    print("[!] Installing UI libraries...")
    install_package('pyfiglet')
    install_package('colorama')
    import pyfiglet
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    r, g, rs, w, cy, ye, mag, bl = (
        Fore.RED, Fore.GREEN, Fore.RESET, Fore.WHITE,
        Fore.CYAN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE
    )

# =============================================================================
# التحقق من وتثبيت مكتبات Telegram - Telegram Libraries
# =============================================================================

try:
    import pyrogram
    from pyrogram import Client, types, filters, enums, raw
    from pyrogram.errors import *
    from telethon import utils as telethon_utils
except (ImportError, AttributeError):
    print(f"{Fore.RED}[!] Pyrogram or Telethon not detected or outdated. Installing now...{Fore.RESET}")
    install_package('pyrogram')
    install_package('telethon')
    import pyrogram
    from pyrogram import Client, types, filters, enums, raw
    from pyrogram.errors import *
    from telethon import utils as telethon_utils

# =============================================================================
# بيانات الاعتماد الثابتة - Fixed Credentials
# =============================================================================

# تحذير: هذه البيانات حساسة ويجب تخزينها في متغيرات بيئية
API_ID = 35923747
API_HASH = "6de1cf34ed1e68d94615ba7b45391dde"
DEVELOPER = "@NMDDER_DEV"

# =============================================================================
# الدوال المساعدة - Helper Functions
# =============================================================================

def safe_session_name(phone: str) -> str:
    """
    تحويل رقم الهاتف إلى اسم ملف آمن للجلسة
    
    Args:
        phone: رقم الهاتف (مثال: +966123456789)
    
    Returns:
        str: اسم ملف آمن يمكن استخدامه كاسم للجلسة
    
    Example:
        "+966123456789" -> "plus966123456789"
    """
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    cleaned = cleaned.replace('+', 'plus')
    if not cleaned:
        cleaned = "unknown"
    return cleaned

def ensure_files():
    """
    التأكد من وجود المجلدات والملفات الضرورية
    ينشئ المجلدات والملفات إذا لم تكن موجودة
    """
    # إنشاء المجلدات الرئيسية
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # قائمة الملفات المطلوبة
    files = [
        'phone.csv',      # قائمة أرقام الهواتف
        'message.csv',    # قوالب الرسائل
        'data.csv',       # بيانات الأعضاء المجمعين
        'done.csv',       # المهام المكتملة
        'banned.csv',     # الحسابات المحظورة
        'groups.csv',     # قائمة المجموعات
        'image.csv',      # قائمة الصور
        'schedule.csv',   # الرسائل المجدولة
        'auto_reply.csv', # إعدادات الردود التلقائية
        'proxy.csv',      # إعدادات البروكسي
        'keywords.csv',   # الكلمات المفتاحية
        'blacklist.csv'   # القائمة السوداء
    ]
    
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                pass  # إنشاء ملف فارغ

def get_phones() -> list:
    """
    قراءة قائمة أرقام الهواتف من ملف phone.csv
    
    Returns:
        list: قائمة بأرقام الهواتف المسجلة
    """
    if not os.path.exists('phone.csv'):
        return []
    with open('phone.csv', 'r', encoding='utf-8') as f:
        return [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

async def join_group_helper(client, link: str):
    """
    مساعد للانضمام إلى مجموعة أو قناة
    
    Args:
        client: كائن Client من Pyrogram
        link: رابط الدعوة أو معرف المجموعة
    
    Returns:
        Chat object أو None إذا فشل الانضمام
    """
    link = link.strip()
    try:
        # محاولة الانضمام عبر رابط دعوة
        if 't.me/joinchat/' in link or 't.me/+' in link:
            try:
                return await client.join_chat(link)
            except Exception:
                try:
                    return await client.get_chat(link)
                except:
                    return None
        else:
            # محاولة الحصول على المجموعة عبر المعرف
            username = link.replace('https://t.me/', '').replace('@', '')
            return await client.get_chat(username)
    except Exception:
        return None

def log_activity(action: str, details: str):
    """
    تسجيل النشاط في ملف السجل اليومي
    
    Args:
        action: نوع الإجراء المُنفذ
        details: تفاصيل إضافية عن الإجراء
    """
    log_file = f'logs/activity_{datetime.now().strftime("%Y%m%d")}.log'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {action}: {details}\n")

# =============================================================================
# واجهة المستخدم - User Interface
# =============================================================================

def banner():
    """
    عرض الشعار الرئيسي للبرنامج
    """
    os.system('clear')
    f = pyfiglet.Figlet(font='slant')
    print(f"{mag}{'='*60}")
    print(g + f.renderText(' N M D D E R '))
    print(f"{mag}{'='*60}")
    print(f"{cy}  [+] Version: 12.0.3 | Final Fix - No Peer Errors{rs}")
    print(f"{cy}  [+] Developer: {DEVELOPER}{rs}")
    print(f"{ye}  [+] Status: no_updates=True + Session Clean{rs}")
    print(f"{mag}{'='*60}\n")

def menu_option(num: int, text: str):
    """
    عرض خيار في القائمة بتنسيق موحد
    
    Args:
        num: رقم الخيار
        text: نص الخيار
    """
    print(f"{mag}[{ye}{num:2}{mag}] {w}{text}")

# =============================================================================
# إدارة الحسابات - Account Management Module
# =============================================================================

async def account_menu():
    """
    القائمة الرئيسية لإدارة الحسابات
    """
    while True:
        banner()
        print(f"{cy}--- ACCOUNT MANAGEMENT MENU ---{rs}")
        menu_option(1, "Login New Account")
        menu_option(2, "Check Account Status")
        menu_option(3, "Add Multiple Accounts (from phones_to_add.txt)")
        menu_option(4, "Remove Banned Accounts")
        menu_option(5, "Change Profile Picture (Mass)")
        menu_option(6, "Change Bio (Mass)")
        menu_option(7, "Change First Name (Mass)")
        menu_option(8, "Export All Sessions")
        menu_option(9, "Import Sessions")
        menu_option(10, "Backup Accounts")
        menu_option(11, "Restore Accounts")
        menu_option(0, "Back to Main Menu")
        
        choice = input(f"\n{mag}🎯 Select Option: {rs}").strip()
        
        if choice == '1': 
            await add_account()
        elif choice == '2': 
            await check_accounts()
        elif choice == '3': 
            await add_multiple_accounts()
        elif choice == '4': 
            await remove_banned_accounts()
        elif choice == '5': 
            await mass_change_profile_pic()
        elif choice == '6': 
            await mass_change_bio()
        elif choice == '7': 
            await mass_change_name()
        elif choice == '8': 
            await export_sessions()
        elif choice == '9': 
            await import_sessions()
        elif choice == '10': 
            await backup_accounts()
        elif choice == '11': 
            await restore_accounts()
        elif choice == '0': 
            break

async def add_account():
    """
    إضافة حساب Telegram جديد
    يطلب رقم الهاتف وينشئ جلسة جديدة
    """
    banner()
    print(f"{ye}--- [Login New Account] ---{rs}")
    phone = input(f"{cy}Phone Number (+...): {rs}").strip()
    if not phone: 
        return
    
    session = safe_session_name(phone)
    try:
        # إنشاء عميل جديد مع تعطيل التحديثات لتقليل استهلاك الموارد
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         phone_number=phone, no_updates=True) as app:
            me = await app.get_me()
            print(f"{g}✅ Success: {me.first_name}{rs}")
            
            # إضافة الرقم إلى قائمة الهواتف إذا لم يكن موجوداً
            existing = get_phones()
            if phone not in existing:
                with open('phone.csv', 'a', newline='') as f:
                    csv.writer(f).writerow([phone])
            
            log_activity("ADD_ACCOUNT", f"{phone} - {me.first_name}")
    except Exception as e:
        print(f"{r}❌ Failed: {e}{rs}")
    
    input("\nPress Enter...")

async def check_accounts():
    """
    فحص حالة جميع الحسابات المسجلة
    يتحقق من الحسابات النشطة والمحظورة
    """
    banner()
    print(f"{ye}--- [Check Accounts Status] ---{rs}")
    active = []
    banned = []
    
    for p in get_phones():
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                           no_updates=True) as app:
                me = await app.get_me()
                print(f"{g}✅ {p} - Active ({me.first_name}){rs}")
                active.append(p)
        except Exception:
            print(f"{r}❌ {p} - Banned/Expired{rs}")
            banned.append(p)
    
    print(f"\n{cy}Summary: {g}{len(active)} Active{rs} | {r}{len(banned)} Banned{rs}")
    input("\nPress Enter...")

async def add_multiple_accounts():
    """
    إضافة عدة حسابات من ملف phones_to_add.txt
    """
    banner()
    print(f"{ye}--- [Add Multiple Accounts] ---{rs}")
    
    if not os.path.exists('phones_to_add.txt'):
        print(f"{r}❌ File 'phones_to_add.txt' not found!{rs}")
        print(f"{cy}💡 Create it with one phone number per line (e.g., +966123456789){rs}")
        input("\nPress Enter...")
        return
    
    with open('phones_to_add.txt', 'r', encoding='utf-8') as f:
        phones = [line.strip() for line in f if line.strip()]
    
    if not phones:
        print(f"{r}❌ No phone numbers found.{rs}")
        input("\nPress Enter...")
        return
    
    print(f"{cy}📱 Found {len(phones)} phone number(s).{rs}")
    confirm = input(f"{cy}Proceed? (y/n): {rs}").strip().lower()
    if confirm != 'y':
        return
    
    success, failed = [], []
    
    for idx, phone in enumerate(phones, 1):
        print(f"\n{cy}[{idx}/{len(phones)}] Trying {phone}...{rs}")
        session = safe_session_name(phone)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                             phone_number=phone, no_updates=True) as app:
                me = await app.get_me()
                existing = get_phones()
                if phone not in existing:
                    with open('phone.csv', 'a', newline='') as f:
                        csv.writer(f).writerow([phone])
                print(f"{g}✅ Success: {me.first_name}{rs}")
                success.append(phone)
                log_activity("MULTI_ADD", f"{phone} - Success")
        except Exception as e:
            print(f"{r}❌ Failed: {e}{rs}")
            failed.append(phone)
        await asyncio.sleep(2)
    
    print(f"\n{g}✅ Success: {len(success)} | {r}❌ Failed: {len(failed)}{rs}")
    input("\nPress Enter...")

async def remove_banned_accounts():
    """
    إزالة الحسابات المحظورة من القائمة
    يحذف ملفات الجلسات المحظورة ويحدث phone.csv
    """
    banner()
    print(f"{ye}--- [Remove Banned Accounts] ---{rs}")
    phones = get_phones()
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    print(f"{cy}Checking {len(phones)} accounts...{rs}")
    active_phones = []
    
    for p in phones:
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                           no_updates=True) as app:
                await app.get_me()
                active_phones.append(p)
                print(f"{g}✅ {p} - Active{rs}")
        except Exception:
            print(f"{r}❌ {p} - Banned (will be removed){rs}")
            session_file = f"sessions/{session}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
    
    # تحديث ملف الهواتف بالحسابات النشطة فقط
    with open('phone.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for p in active_phones:
            writer.writerow([p])
    
    print(f"\n{g}Removed {len(phones)-len(active_phones)} banned accounts.{rs}")
    log_activity("REMOVE_BANNED", f"Removed {len(phones)-len(active_phones)} accounts")
    input("\nPress Enter...")

async def mass_change_profile_pic():
    """
    تغيير صورة الملف الشخصي لجميع الحسابات
    """
    banner()
    print(f"{ye}--- [Mass Change Profile Picture] ---{rs}")
    pic_path = input(f"{cy}Image path: {rs}").strip()
    if not os.path.exists(pic_path):
        print(f"{r}Image not found!{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    delay = int(input(f"{cy}Delay between accounts (seconds): {rs}"))
    success = 0
    
    for p in phones:
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                           no_updates=True) as app:
                await app.set_profile_photo(photo=pic_path)
                print(f"{g}✅ {p} - Profile picture changed{rs}")
                success += 1
                log_activity("CHANGE_PIC", f"{p} - Success")
        except Exception as e:
            print(f"{r}❌ {p} - Failed: {e}{rs}")
        await asyncio.sleep(delay)
    
    print(f"\n{g}Success: {success}/{len(phones)}{rs}")
    input("\nPress Enter...")

async def mass_change_bio():
    """
    تغيير النبذة التعريفية (Bio) لجميع الحسابات
    """
    banner()
    print(f"{ye}--- [Mass Change Bio] ---{rs}")
    bio = input(f"{cy}New bio: {rs}").strip()
    phones = get_phones()
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    delay = int(input(f"{cy}Delay between accounts (seconds): {rs}"))
    success = 0
    
    for p in phones:
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                           no_updates=True) as app:
                await app.update_profile(bio=bio)
                print(f"{g}✅ {p} - Bio changed{rs}")
                success += 1
        except Exception as e:
            print(f"{r}❌ {p} - Failed: {e}{rs}")
        await asyncio.sleep(delay)
    
    print(f"\n{g}Success: {success}/{len(phones)}{rs}")
    input("\nPress Enter...")

async def mass_change_name():
    """
    تغيير الاسم (الأول والأخير) لجميع الحسابات
    """
    banner()
    print(f"{ye}--- [Mass Change First Name] ---{rs}")
    first_name = input(f"{cy}New first name: {rs}").strip()
    last_name = input(f"{cy}New last name (optional): {rs}").strip()
    phones = get_phones()
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    delay = int(input(f"{cy}Delay between accounts (seconds): {rs}"))
    success = 0
    
    for p in phones:
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                           no_updates=True) as app:
                await app.update_profile(
                    first_name=first_name, 
                    last_name=last_name if last_name else None
                )
                print(f"{g}✅ {p} - Name changed to {first_name}{rs}")
                success += 1
        except Exception as e:
            print(f"{r}❌ {p} - Failed: {e}{rs}")
        await asyncio.sleep(delay)
    
    print(f"\n{g}Success: {success}/{len(phones)}{rs}")
    input("\nPress Enter...")

async def export_sessions():
    """
    تصدير جميع ملفات الجلسات إلى ملف ZIP
    """
    banner()
    print(f"{ye}--- [Export Sessions] ---{rs}")
    if not os.path.exists('sessions'):
        print(f"{r}No sessions found.{rs}")
        input("\nPress Enter...")
        return
    
    backup_name = f"backups/sessions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    shutil.make_archive(backup_name.replace('.zip', ''), 'zip', 'sessions')
    print(f"{g}✅ Sessions exported to {backup_name}{rs}")
    log_activity("EXPORT_SESSIONS", backup_name)
    input("\nPress Enter...")

async def import_sessions():
    """
    استيراد ملفات الجلسات من ملف ZIP
    """
    banner()
    print(f"{ye}--- [Import Sessions] ---{rs}")
    backups = [f for f in os.listdir('backups') 
               if f.endswith('.zip') and 'sessions_backup' in f]
    if not backups:
        print(f"{r}No backup files found.{rs}")
        input("\nPress Enter...")
        return
    
    print(f"{cy}Available backups:{rs}")
    for idx, b in enumerate(backups, 1):
        print(f"  {idx}. {b}")
    
    choice = int(input(f"{cy}Select backup: {rs}")) - 1
    if 0 <= choice < len(backups):
        shutil.unpack_archive(f"backups/{backups[choice]}", 'sessions_restored')
        print(f"{g}✅ Sessions restored to sessions_restored/{rs}")
    
    input("\nPress Enter...")

async def backup_accounts():
    """
    إنشاء نسخة احتياطية كاملة (الهواتف والجلسات)
    """
    banner()
    print(f"{ye}--- [Backup Accounts] ---{rs}")
    backup_name = f"backups/accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_name, exist_ok=True)
    shutil.copy('phone.csv', f"{backup_name}/phone.csv")
    shutil.copytree('sessions', f"{backup_name}/sessions")
    print(f"{g}✅ Accounts backed up to {backup_name}{rs}")
    log_activity("BACKUP_ACCOUNTS", backup_name)
    input("\nPress Enter...")

async def restore_accounts():
    """
    استعادة النسخة الاحتياطية الكاملة
    """
    banner()
    print(f"{ye}--- [Restore Accounts] ---{rs}")
    backups = [d for d in os.listdir('backups') 
               if os.path.isdir(os.path.join('backups', d)) 
               and d.startswith('accounts_')]
    if not backups:
        print(f"{r}No account backups found.{rs}")
        input("\nPress Enter...")
        return
    
    print(f"{cy}Available backups:{rs}")
    for idx, b in enumerate(backups, 1):
        print(f"  {idx}. {b}")
    
    choice = int(input(f"{cy}Select backup: {rs}")) - 1
    if 0 <= choice < len(backups):
        shutil.copy(f"backups/{backups[choice]}/phone.csv", 'phone.csv')
        shutil.rmtree('sessions')
        shutil.copytree(f"backups/{backups[choice]}/sessions", 'sessions')
        print(f"{g}✅ Accounts restored from {backups[choice]}{rs}")
    
    input("\nPress Enter...")

# =============================================================================
# أدوات المراسلة - Messaging Tools Module
# =============================================================================

async def msg_tools_menu():
    """
    القائمة الرئيسية لأدوات المراسلة
    """
    while True:
        banner()
        print(f"{cy}--- MESSAGING TOOLS MENU ---{rs}")
        menu_option(1, "Send to Group (Loop Text)")
        menu_option(2, "Send to Group (Loop Image)")
        menu_option(3, "Send to Group (Single Text)")
        menu_option(4, "Send to Group (Single Image)")
        menu_option(5, "Send to Multiple Groups (Single Text)")
        menu_option(6, "Send to Multiple Groups (Single Image)")
        menu_option(7, "Send to User (Direct Text)")
        menu_option(8, "Send to User (Direct Image)")
        menu_option(9, "Schedule Message")
        menu_option(10, "Auto Reply Setup")
        menu_option(11, "Broadcast to All Contacts")
        menu_option(12, "Send with Delay Scheduler")
        menu_option(0, "Back to Main Menu")
        
        choice = input(f"\n{mag}🎯 Select Option: {rs}").strip()
        
        if choice == '1': 
            await messagesendergroup()
        elif choice == '2': 
            await messagesendergrouppic()
        elif choice == '3': 
            await messagesendergroupsingle()
        elif choice == '4': 
            await messagesendergrouppicsingle()
        elif choice == '5': 
            await messagesendermultigroupsingle()
        elif choice == '6': 
            await messagesendermultigroupsinglepic()
        elif choice == '7': 
            await messagesendering()
        elif choice == '8': 
            await messagesenderingpic()
        elif choice == '9': 
            await schedule_message()
        elif choice == '10': 
            await setup_auto_reply()
        elif choice == '11': 
            await broadcast_to_contacts()
        elif choice == '12': 
            await send_with_scheduler()
        elif choice == '0': 
            break

async def messagesendergroup():
    """
    إرسال رسائل متكررة (دورية) إلى مجموعة
    يستخدم الرسائل من ملف message.csv
    """
    banner()
    print(f"{ye}--- [Send to Group - Loop Text] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    num_ads = int(input(f"{cy}Messages per account: {rs}"))
    delay = int(input(f"{cy}Delay between messages: {rs}"))
    
    with open('message.csv', 'r', encoding='utf-8') as f:
        messages = [row[0] for row in csv.reader(f) if row]
    
    if not messages:
        print(f"{r}No messages in message.csv{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    
    async def worker(p):
        """عامل إرسال الرسائل لكل حساب"""
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if not chat: 
                return
            for i in range(num_ads):
                try:
                    await app.send_message(chat.id, messages[i % len(messages)])
                    print(f"{g}[{p}] Sent!{rs}")
                    await asyncio.sleep(delay)
                except FloodWait as e:
                    # الانتظار عند تجاوز الحد المسموح
                    await asyncio.sleep(e.value)
                    break
                except Exception:
                    break
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendergrouppic():
    """
    إرسال صور متكررة (دورية) إلى مجموعة
    """
    banner()
    print(f"{ye}--- [Send to Group - Loop Image] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    img = input(f"{cy}Image path: {rs}").strip()
    num_ads = int(input(f"{cy}Messages per account: {rs}"))
    delay = int(input(f"{cy}Delay between messages: {rs}"))
    
    with open('message.csv', 'r', encoding='utf-8') as f:
        messages = [row[0] for row in csv.reader(f) if row]
    
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if not chat: 
                return
            for i in range(num_ads):
                try:
                    caption = messages[i % len(messages)] if messages else ""
                    await app.send_photo(chat.id, img, caption=caption)
                    print(f"{g}[{p}] Sent!{rs}")
                    await asyncio.sleep(delay)
                except Exception:
                    break
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendergroupsingle():
    """
    إرسال رسالة نصية واحدة إلى مجموعة
    """
    banner()
    print(f"{ye}--- [Send to Group - Single Text] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    msg = input(f"{cy}Message: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if chat:
                await app.send_message(chat.id, msg)
                print(f"{g}[{p}] Sent!{rs}")
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendergrouppicsingle():
    """
    إرسال صورة واحدة إلى مجموعة
    """
    banner()
    print(f"{ye}--- [Send to Group - Single Image] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    img = input(f"{cy}Image path: {rs}").strip()
    caption = input(f"{cy}Caption (optional): {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if chat:
                await app.send_photo(chat.id, img, 
                                   caption=caption if caption else None)
                print(f"{g}[{p}] Sent!{rs}")
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendermultigroupsingle():
    """
    إرسال رسالة واحدة إلى عدة مجموعات
    المجموعات من ملف groups.csv
    """
    banner()
    print(f"{ye}--- [Send to Multiple Groups - Single Text] ---{rs}")
    with open('groups.csv', 'r', encoding='utf-8') as f:
        groups = [row[0] for row in csv.reader(f) if row]
    
    if not groups:
        print(f"{r}No groups in groups.csv{rs}")
        input("\nPress Enter...")
        return
    
    msg = input(f"{cy}Message: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            for g_link in groups:
                chat = await join_group_helper(app, g_link)
                if chat:
                    try:
                        await app.send_message(chat.id, msg)
                        print(f"{g}[{p}] Sent to {g_link}{rs}")
                        await asyncio.sleep(2)
                    except Exception:
                        continue
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendermultigroupsinglepic():
    """
    إرسال صورة واحدة إلى عدة مجموعات
    """
    banner()
    print(f"{ye}--- [Send to Multiple Groups - Single Image] ---{rs}")
    with open('groups.csv', 'r', encoding='utf-8') as f:
        groups = [row[0] for row in csv.reader(f) if row]
    
    if not groups:
        print(f"{r}No groups in groups.csv{rs}")
        input("\nPress Enter...")
        return
    
    img = input(f"{cy}Image path: {rs}").strip()
    caption = input(f"{cy}Caption: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            for g_link in groups:
                chat = await join_group_helper(app, g_link)
                if chat:
                    try:
                        await app.send_photo(chat.id, img, caption=caption)
                        print(f"{g}[{p}] Sent to {g_link}{rs}")
                        await asyncio.sleep(2)
                    except Exception:
                        continue
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesendering():
    """
    إرسال رسالة مباشرة إلى مستخدم محدد
    """
    banner()
    print(f"{ye}--- [Send to User - Direct Text] ---{rs}")
    target_user = input(f"{cy}Target Username/ID: {rs}").strip()
    msg = input(f"{cy}Message: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            try:
                await app.send_message(target_user, msg)
                print(f"{g}[{p}] Sent to {target_user}{rs}")
            except Exception:
                pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def messagesenderingpic():
    """
    إرسال صورة مباشرة إلى مستخدم محدد
    """
    banner()
    print(f"{ye}--- [Send to User - Direct Image] ---{rs}")
    target_user = input(f"{cy}Target Username/ID: {rs}").strip()
    img = input(f"{cy}Image path: {rs}").strip()
    caption = input(f"{cy}Caption: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            try:
                await app.send_photo(target_user, img, caption=caption)
                print(f"{g}[{p}] Sent to {target_user}{rs}")
            except Exception:
                pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def schedule_message():
    """
    جدولة رسالة لإرسالها في وقت محدد
    يحفظ الجدولة في ملف schedule.csv
    """
    banner()
    print(f"{ye}--- [Schedule Message] ---{rs}")
    print(f"{cy}Schedule a message to be sent later{rs}")
    target = input(f"{cy}Target (group/user): {rs}").strip()
    msg = input(f"{cy}Message: {rs}").strip()
    schedule_time = input(f"{cy}Schedule time (YYYY-MM-DD HH:MM:SS): {rs}").strip()
    
    try:
        send_time = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M:%S")
        with open('schedule.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([target, msg, send_time.isoformat(), 'pending'])
        print(f"{g}✅ Message scheduled for {send_time}{rs}")
        log_activity("SCHEDULE", f"Message to {target} at {send_time}")
    except ValueError:
        print(f"{r}Invalid date format!{rs}")
    
    input("\nPress Enter...")

async def setup_auto_reply():
    """
    إعداد الردود التلقائية بناءً على الكلمات المفتاحية
    """
    banner()
    print(f"{ye}--- [Auto Reply Setup] ---{rs}")
    print(f"{cy}Setup auto-reply for accounts{rs}")
    keyword = input(f"{cy}Trigger keyword (leave empty for all): {rs}").strip()
    reply = input(f"{cy}Reply message: {rs}").strip()
    
    with open('auto_reply.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([keyword if keyword else '*', reply])
    
    print(f"{g}✅ Auto-reply configured{rs}")
    input("\nPress Enter...")

async def broadcast_to_contacts():
    """
    إذاعة رسائل لجميع جهات الاتصال
    """
    banner()
    print(f"{ye}--- [Broadcast to Contacts] ---{rs}")
    with open('message.csv', 'r', encoding='utf-8') as f:
        messages = [row[0] for row in csv.reader(f) if row]
    
    if not messages:
        print(f"{r}No messages in message.csv{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            try:
                async for dialog in app.get_dialogs():
                    if dialog.chat.type == enums.ChatType.PRIVATE:
                        for msg in messages:
                            await app.send_message(dialog.chat.id, msg)
                            await asyncio.sleep(1)
                        print(f"{g}[{p}] Broadcasted to {dialog.chat.first_name}{rs}")
                        break
            except Exception:
                pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def send_with_scheduler():
    """
    فحص وإرسال الرسائل المجدولة التي حان وقتها
    """
    banner()
    print(f"{ye}--- [Send with Scheduler] ---{rs}")
    print(f"{cy}Check and send scheduled messages{rs}")
    
    if not os.path.exists('schedule.csv'):
        print(f"{r}No scheduled messages{rs}")
        input("\nPress Enter...")
        return
    
    with open('schedule.csv', 'r', encoding='utf-8') as f:
        schedules = list(csv.reader(f))
    
    updated = []
    now = datetime.now()
    phones = get_phones()
    
    for s in schedules:
        if len(s) >= 4 and s[3] == 'pending':
            send_time = datetime.fromisoformat(s[2])
            if now >= send_time:
                target, msg = s[0], s[1]
                for p in phones:
                    session = safe_session_name(p)
                    try:
                        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                                         no_updates=True) as app:
                            await app.send_message(target, msg)
                            print(f"{g}✅ Sent scheduled message to {target}{rs}")
                            s[3] = 'sent'
                            log_activity("SCHEDULED_SENT", f"Message to {target}")
                            break
                    except Exception:
                        continue
        updated.append(s)
    
    with open('schedule.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(updated)
    
    input("\nDone. Press Enter...")

# =============================================================================
# أدوات الجمع والإضافة - Scraping & Adding Tools Module
# =============================================================================

async def scrap_add_menu():
    """
    القائمة الرئيسية لأدوات جمع وإضافة الأعضاء
    """
    while True:
        banner()
        print(f"{cy}--- SCRAPING & ADDING TOOLS MENU ---{rs}")
        menu_option(1, "Scrape Members (Save to data.csv)")
        menu_option(2, "Add Members from data.csv (Multi-Account)")
        menu_option(3, "Add Members from Group to Group (Live)")
        menu_option(4, "Add Contacts from Group")
        menu_option(5, "Add Contact by Phone")
        menu_option(6, "Scrape Active Members Only")
        menu_option(7, "Scrape Members with Profile Photo")
        menu_option(8, "Scrape Admins Only")
        menu_option(9, "Add Members to Channel")
        menu_option(10, "Scrape Members with Keywords")
        menu_option(11, "Scrape Members by Join Date")
        menu_option(12, "Scrape Members by Last Seen")
        menu_option(0, "Back to Main Menu")
        
        choice = input(f"\n{mag}🎯 Select Option: {rs}").strip()
        
        if choice == '1': 
            await multi_ccraper()
        elif choice == '2': 
            await add_members_pro()
        elif choice == '3': 
            await add_members_from_group_to_group()
        elif choice == '4': 
            await addtocontactbygroup()
        elif choice == '5': 
            await addtocontactbyimp()
        elif choice == '6': 
            await scrape_active_members()
        elif choice == '7': 
            await scrape_with_photo()
        elif choice == '8': 
            await scrape_admins()
        elif choice == '9': 
            await add_to_channel()
        elif choice == '10': 
            await scrape_by_keywords()
        elif choice == '11': 
            await scrape_by_join_date()
        elif choice == '12': 
            await scrape_by_last_seen()
        elif choice == '0': 
            break

async def multi_ccraper():
    """
    جمع أعضاء المجموعة وحفظهم في data.csv
    يستخدم الحساب الأول في القائمة
    """
    banner()
    print(f"{ye}--- [Scrape Members] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access target group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        async for m in app.get_chat_members(chat.id):
            if m.user.username:
                members.append({
                    'user_id': m.user.id,
                    'first_name': m.user.first_name or '',
                    'last_name': m.user.last_name or '',
                    'username': m.user.username
                })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} members!{rs}")
        log_activity("SCRAPE", f"Scraped {len(members)} from {target}")
    
    input("\nDone. Press Enter...")

async def add_members_pro():
    """
    إضافة أعضاء من data.csv إلى مجموعة باستخدام عدة حسابات
    """
    banner()
    print(f"{ye}--- [Add Members from data.csv] ---{rs}")
    your_group = input(f"{cy}Your Group: {rs}").strip()
    limit = int(input(f"{cy}Limit per account: {rs}"))
    delay_min = int(input(f"{cy}Min Delay: {rs}"))
    delay_max = int(input(f"{cy}Max Delay: {rs}"))
    
    with open('data.csv', 'r', encoding='UTF-8') as f:
        members = list(csv.DictReader(f))
    
    if not members:
        print(f"{r}No members in data.csv. Run scraping first.{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    curr_idx = [0]  # متغير مشترك لتتبع الموضع الحالي
    
    async def worker(p):
        added = 0
        session = safe_session_name(p)
        try:
            async with Client(f"sessions/{session}", API_ID, API_HASH, 
                             no_updates=True) as app:
                chat = await join_group_helper(app, your_group)
                if not chat: 
                    return
                target = chat.username if chat.username else str(chat.id)
                
                while added < limit and curr_idx[0] < len(members):
                    user = members[curr_idx[0]]
                    curr_idx[0] += 1
                    try:
                        await app.add_chat_members(target, user['username'])
                        print(f"{g}[{p}] Added {user['username']}{rs}")
                        added += 1
                        await asyncio.sleep(random.randint(delay_min, delay_max))
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        break
                    except PeerFlood:
                        break
                    except ValueError:
                        continue
                    except Exception:
                        continue
        except Exception:
            pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def add_members_from_group_to_group():
    """
    نقل أعضاء من مجموعة إلى مجموعة أخرى مباشرة
    """
    banner()
    print(f"{ye}--- [Add Members from Group to Group] ---{rs}")
    source = input(f"{cy}Source Group: {rs}").strip()
    target = input(f"{cy}Target Group: {rs}").strip()
    limit = int(input(f"{cy}Limit per account: {rs}"))
    phones = get_phones()
    
    async def worker(p):
        added = 0
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            s_chat = await join_group_helper(app, source)
            t_chat = await join_group_helper(app, target)
            if not s_chat or not t_chat: 
                return
            t_target = t_chat.username if t_chat.username else str(t_chat.id)
            
            async for m in app.get_chat_members(s_chat.id):
                if added >= limit: 
                    break
                if m.user.username:
                    try:
                        await app.add_chat_members(t_target, m.user.username)
                        print(f"{g}[{p}] Added {m.user.username}{rs}")
                        added += 1
                        await asyncio.sleep(5)
                    except Exception:
                        continue
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def addtocontactbygroup():
    """
    إضافة أعضاء المجموعة كجهات اتصال
    """
    banner()
    print(f"{ye}--- [Add Contacts from Group] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if not chat: 
                return
            async for m in app.get_chat_members(chat.id):
                try:
                    await app.add_contact(user_id=m.user.id, 
                                        first_name=m.user.first_name or "User")
                    print(f"{g}[{p}] Added contact: {m.user.id}{rs}")
                    await asyncio.sleep(1)
                except:
                    pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def addtocontactbyimp():
    """
    إضافة جهة اتصال برقم هاتف محدد
    """
    banner()
    print(f"{ye}--- [Add Contact by Phone] ---{rs}")
    phone_to_add = input(f"{cy}Phone to add: {rs}").strip()
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            try:
                await app.add_contact(phone_to_add, "User")
                print(f"{g}[{p}] Added contact!{rs}")
            except:
                pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def scrape_active_members():
    """
    جمع الأعضاء النشطين فقط (ذوي حالة نشاط)
    """
    banner()
    print(f"{ye}--- [Scrape Active Members Only] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        async for m in app.get_chat_members(chat.id):
            # التحقق من وجود حالة نشاط
            if m.user.username and m.user.status and str(m.user.status) != "UserStatus.EMPTY":
                members.append({
                    'user_id': m.user.id,
                    'first_name': m.user.first_name or '',
                    'last_name': m.user.last_name or '',
                    'username': m.user.username
                })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} active members!{rs}")
    
    input("\nDone. Press Enter...")

async def scrape_with_photo():
    """
    جمع الأعضاء الذين لديهم صور ملف شخصي فقط
    """
    banner()
    print(f"{ye}--- [Scrape Members with Profile Photo] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        async for m in app.get_chat_members(chat.id):
            if m.user.username and m.user.photo:
                members.append({
                    'user_id': m.user.id,
                    'first_name': m.user.first_name or '',
                    'last_name': m.user.last_name or '',
                    'username': m.user.username
                })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} members with photos!{rs}")
    
    input("\nDone. Press Enter...")

async def scrape_admins():
    """
    جمع مسؤولي المجموعة فقط
    """
    banner()
    print(f"{ye}--- [Scrape Admins Only] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        admins = []
        # استخدام فلتر المسؤولين
        async for m in app.get_chat_members(chat.id, 
                                           filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if m.user.username:
                admins.append({
                    'user_id': m.user.id,
                    'first_name': m.user.first_name or '',
                    'last_name': m.user.last_name or '',
                    'username': m.user.username
                })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(admins)
        
        print(f"{g}✅ Scraped {len(admins)} admins!{rs}")
    
    input("\nDone. Press Enter...")

async def add_to_channel():
    """
    إضافة أعضاء إلى قناة
    """
    banner()
    print(f"{ye}--- [Add Members to Channel] ---{rs}")
    target_channel = input(f"{cy}Target Channel: {rs}").strip()
    limit = int(input(f"{cy}Limit per account: {rs}"))
    delay = int(input(f"{cy}Delay between adds: {rs}"))
    
    with open('data.csv', 'r', encoding='UTF-8') as f:
        members = list(csv.DictReader(f))
    
    if not members:
        print(f"{r}No members in data.csv{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    curr_idx = [0]
    
    async def worker(p):
        added = 0
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target_channel)
            if not chat: 
                return
            target = chat.username if chat.username else str(chat.id)
            
            while added < limit and curr_idx[0] < len(members):
                user = members[curr_idx[0]]
                curr_idx[0] += 1
                try:
                    await app.add_chat_members(target, user['username'])
                    print(f"{g}[{p}] Added {user['username']} to channel{rs}")
                    added += 1
                    await asyncio.sleep(delay)
                except Exception:
                    continue
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def scrape_by_keywords():
    """
    جمع الأعضاء بناءً على كلمات مفتاحية في أسمائهم
    """
    banner()
    print(f"{ye}--- [Scrape Members by Keywords] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    keywords = input(f"{cy}Keywords (comma separated): {rs}").strip().lower().split(',')
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        async for m in app.get_chat_members(chat.id):
            if m.user.username:
                name = (m.user.first_name or "").lower() + " " + (m.user.last_name or "").lower()
                if any(kw.strip() in name for kw in keywords):
                    members.append({
                        'user_id': m.user.id,
                        'first_name': m.user.first_name or '',
                        'last_name': m.user.last_name or '',
                        'username': m.user.username
                    })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} members matching keywords!{rs}")
    
    input("\nDone. Press Enter...")

async def scrape_by_join_date():
    """
    جمع الأعضاء الذين انضموا بعد تاريخ محدد
    """
    banner()
    print(f"{ye}--- [Scrape Members by Join Date] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    print(f"{cy}Scrape members who joined after a certain date{rs}")
    date_str = input(f"{cy}Date (YYYY-MM-DD): {rs}").strip()
    
    try:
        join_after = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"{r}Invalid date format!{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        async for m in app.get_chat_members(chat.id):
            if m.user.username and m.joined_date:
                if m.joined_date >= join_after:
                    members.append({
                        'user_id': m.user.id,
                        'first_name': m.user.first_name or '',
                        'last_name': m.user.last_name or '',
                        'username': m.user.username
                    })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} members who joined after {date_str}!{rs}")
    
    input("\nDone. Press Enter...")

async def scrape_by_last_seen():
    """
    جمع الأعضاء النشطين خلال فترة زمنية محددة
    """
    banner()
    print(f"{ye}--- [Scrape Members by Last Seen] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    print(f"{cy}Scrape members seen within last N days{rs}")
    days = int(input(f"{cy}Days: {rs}"))
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access group.{rs}")
            input("\nPress Enter...")
            return
        
        members = []
        cutoff = datetime.now() - timedelta(days=days)
        async for m in app.get_chat_members(chat.id):
            if m.user.username:
                if m.user.status and hasattr(m.user.status, 'was_online'):
                    if m.user.status.was_online and m.user.status.was_online >= cutoff:
                        members.append({
                            'user_id': m.user.id,
                            'first_name': m.user.first_name or '',
                            'last_name': m.user.last_name or '',
                            'username': m.user.username
                        })
        
        with open('data.csv', 'w', encoding='UTF-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'first_name', 
                                                   'last_name', 'username'])
            writer.writeheader()
            writer.writerows(members)
        
        print(f"{g}✅ Scraped {len(members)} members active in last {days} days!{rs}")
    
    input("\nDone. Press Enter...")

# =============================================================================
# أدوات إعادة التوجيه والقنوات - Forwarding & Channel Tools Module
# =============================================================================

async def forward_menu():
    """
    القائمة الرئيسية لأدوات إعادة التوجيه والقنوات
    """
    while True:
        banner()
        print(f"{cy}--- FORWARDING & CHANNEL TOOLS MENU ---{rs}")
        menu_option(1, "Join Multiple Groups (from groups.csv)")
        menu_option(2, "Leave All Groups")
        menu_option(3, "Delete All Messages in Group")
        menu_option(4, "Export Channel Members")
        menu_option(5, "Get Channel Stats")
        menu_option(0, "Back to Main Menu")
        
        choice = input(f"\n{mag}🎯 Select Option: {rs}").strip()
        
        if choice == '1': 
            await join_multiple_groups()
        elif choice == '2': 
            await leave_all_groups()
        elif choice == '3': 
            await delete_group_messages()
        elif choice == '4': 
            await export_channel_members()
        elif choice == '5': 
            await get_channel_stats()
        elif choice == '0': 
            break

async def join_multiple_groups():
    """
    الانضمام لعدة مجموعات من ملف groups.csv
    """
    banner()
    print(f"{ye}--- [Join Multiple Groups] ---{rs}")
    with open('groups.csv', 'r', encoding='utf-8') as f:
        groups = [row[0] for row in csv.reader(f) if row]
    
    if not groups:
        print(f"{r}No groups in groups.csv{rs}")
        input("\nPress Enter...")
        return
    
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            for g_link in groups:
                try:
                    await join_group_helper(app, g_link)
                    print(f"{g}[{p}] Joined {g_link}{rs}")
                    await asyncio.sleep(2)
                except Exception:
                    print(f"{r}[{p}] Failed to join {g_link}{rs}")
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def leave_all_groups():
    """
    مغادرة جميع المجموعات (ما عدا المحادثات المحفوظة)
    """
    banner()
    print(f"{ye}--- [Leave All Groups] ---{rs}")
    confirm = input(f"{r}WARNING: This will leave all groups except saved messages. Continue? (yes/no): {rs}").strip().lower()
    if confirm != 'yes':
        return
    
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, 
                                       enums.ChatType.SUPERGROUP]:
                    try:
                        await app.leave_chat(dialog.chat.id)
                        print(f"{g}[{p}] Left {dialog.chat.title}{rs}")
                        await asyncio.sleep(1)
                    except Exception:
                        pass
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def delete_group_messages():
    """
    حذف جميع الرسائل في مجموعة محددة
    """
    banner()
    print(f"{ye}--- [Delete All Messages in Group] ---{rs}")
    target = input(f"{cy}Target Group: {rs}").strip()
    limit = int(input(f"{cy}Messages to delete (0 for all): {rs}"))
    phones = get_phones()
    
    async def worker(p):
        session = safe_session_name(p)
        async with Client(f"sessions/{session}", API_ID, API_HASH, 
                         no_updates=True) as app:
            chat = await join_group_helper(app, target)
            if not chat: 
                return
            count = 0
            async for message in app.get_chat_history(chat.id, 
                                                       limit=limit if limit > 0 else None):
                try:
                    await message.delete()
                    count += 1
                    if count % 10 == 0:
                        print(f"{g}[{p}] Deleted {count} messages{rs}")
                except Exception:
                    continue
            print(f"{g}[{p}] Deleted total {count} messages{rs}")
    
    await asyncio.gather(*[worker(p) for p in phones])
    input("\nDone. Press Enter...")

async def export_channel_members():
    """
    تصدير أعضاء القناة إلى ملف CSV منفصل
    """
    banner()
    print(f"{ye}--- [Export Channel Members] ---{rs}")
    target = input(f"{cy}Target Channel: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access channel.{rs}")
            input("\nPress Enter...")
            return
        
        filename = f"channel_members_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', encoding='UTF-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'first_name', 'last_name', 'username'])
            async for m in app.get_chat_members(chat.id):
                writer.writerow([m.user.id, m.user.first_name or '', 
                                m.user.last_name or '', m.user.username or ''])
        
        print(f"{g}✅ Exported members to {filename}{rs}")
    
    input("\nPress Enter...")

async def get_channel_stats():
    """
    الحصول على إحصائيات القناة (عدد الأعضاء والمسؤولين)
    """
    banner()
    print(f"{ye}--- [Get Channel Stats] ---{rs}")
    target = input(f"{cy}Target Channel: {rs}").strip()
    phones = get_phones()
    
    if not phones:
        print(f"{r}No accounts found.{rs}")
        input("\nPress Enter...")
        return
    
    session = safe_session_name(phones[0])
    async with Client(f"sessions/{session}", API_ID, API_HASH, 
                     no_updates=True) as app:
        chat = await join_group_helper(app, target)
        if not chat:
            print(f"{r}Could not access channel.{rs}")
            input("\nPress Enter...")
            return
        
        member_count = 0
        admin_count = 0
        async for m in app.get_chat_members(chat.id):
            member_count += 1
            if m.status in [enums.ChatMemberStatus.ADMINISTRATOR, 
                           enums.ChatMemberStatus.OWNER]:
                admin_count += 1
        
        print(f"\n{cy}Channel Stats for {target}:{rs}")
        print(f"{g}Total Members: {member_count}{rs}")
        print(f"{g}Admins: {admin_count}{rs}")
        print(f"{g}Chat ID: {chat.id}{rs}")
        print(f"{g}Title: {chat.title}{rs}")
        log_activity("CHANNEL_STATS", f"{target}: {member_count} members")
    
    input("\nPress Enter...")

# =============================================================================
# الدالة الرئيسية - Main Entry Point
# =============================================================================

async def main():
    """
    الدالة الرئيسية - نقطة دخول البرنامج
    تهيئة الملفات وتشغيل القائمة الرئيسية
    """
    ensure_files()
    
    while True:
        banner()
        print(f"{cy}--- ULTIMATE NMDDER SUITE (v12.0.3) ---{rs}")
        menu_option(1, "Account Management")
        menu_option(2, "Messaging Tools")
        menu_option(3, "Scraping & Adding Tools")
        menu_option(4, "Forwarding & Channel Tools")
        menu_option(0, f"{r}Exit Program")
        
        choice = input(f"\n{mag}🎯 Select Main Category: {rs}").strip()
        
        if choice == '1': 
            await account_menu()
        elif choice == '2': 
            await msg_tools_menu()
        elif choice == '3': 
            await scrap_add_menu()
        elif choice == '4': 
            await forward_menu()
        elif choice == '0': 
            break
        else: 
            await asyncio.sleep(1)

# =============================================================================
# تشغيل البرنامج - Program Execution
# =============================================================================

if __name__ == "__main__":
    try:
        # إنشاء حلقة أحداث جديدة مع معالج أخطاء مخصص
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(silence_peer_error)
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        # معالجة إيقاف البرنامج بـ Ctrl+C
        sys.exit()
