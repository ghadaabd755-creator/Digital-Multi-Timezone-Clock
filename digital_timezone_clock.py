#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ساعة رقمية متقدمة تعرض الوقت في مناطق زمنية مختلفة
Advanced Digital Multi-Timezone Clock
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from datetime import datetime
import pytz
from threading import Thread
import json
import os
from typing import List, Dict, Tuple
from enum import Enum
import subprocess
import platform


class TimeFormat(Enum):
    """تنسيقات الوقت المدعومة"""
    FORMAT_24H = "24h"
    FORMAT_12H = "12h"


class ClockTheme(Enum):
    """المواضيع المتاحة"""
    DARK = {
        "bg": "#1a1a2e",
        "fg": "#00d4ff",
        "accent": "#00ff88",
        "error": "#ff0055",
        "clock_bg": "#16213e",
        "clock_fg": "#00ff88",
        "button_bg": "#0f3460",
        "button_hover": "#00d4ff",
    }
    
    LIGHT = {
        "bg": "#f5f5f5",
        "fg": "#333333",
        "accent": "#00d4ff",
        "error": "#ff0055",
        "clock_bg": "#ffffff",
        "clock_fg": "#000000",
        "button_bg": "#e0e0e0",
        "button_hover": "#00d4ff",
    }
    
    NEON = {
        "bg": "#0d0221",
        "fg": "#ff006e",
        "accent": "#00f5ff",
        "error": "#ff006e",
        "clock_bg": "#0d0221",
        "clock_fg": "#00f5ff",
        "button_bg": "#3a0ca3",
        "button_hover": "#ff006e",
    }


class Timezone:
    """فئة تمثل منطقة زمنية"""
    
    def __init__(self, name: str, timezone_str: str, country: str = "", emoji: str = "🌍"):
        self.name = name
        self.timezone_str = timezone_str
        self.country = country
        self.emoji = emoji
    
    def get_current_time(self) -> datetime:
        """الحصول على الوقت الحالي في هذه المنطقة الزمنية"""
        try:
            tz = pytz.timezone(self.timezone_str)
            return datetime.now(tz)
        except:
            return datetime.now()
    
    def to_dict(self) -> Dict:
        """تحويل المنطقة الزمنية إلى قاموس"""
        return {
            "name": self.name,
            "timezone": self.timezone_str,
            "country": self.country,
            "emoji": self.emoji
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Timezone':
        """إنشاء منطقة زمنية من قاموس"""
        return Timezone(
            data.get("name", ""),
            data.get("timezone", "UTC"),
            data.get("country", ""),
            data.get("emoji", "🌍")
        )


class DigitalClock:
    """فئة الساعة الرقمية الرئيسية"""
    
    # المناطق الزمنية الافتراضية
    DEFAULT_TIMEZONES = [
        Timezone("London", "Europe/London", "🇬🇧 UK", "🌍"),
        Timezone("New York", "America/New_York", "🇺🇸 USA", "🗽"),
        Timezone("Tokyo", "Asia/Tokyo", "🇯🇵 Japan", "🗾"),
        Timezone("Dubai", "Asia/Dubai", "🇦🇪 UAE", "🏜️"),
        Timezone("Sydney", "Australia/Sydney", "🇦🇺 Australia", "🦘"),
        Timezone("Cairo", "Africa/Cairo", "🇪🇬 Egypt", "🔺"),
        Timezone("São Paulo", "America/Sao_Paulo", "🇧🇷 Brazil", "⚽"),
        Timezone("Singapore", "Asia/Singapore", "🇸🇬 Singapore", "🏙️"),
    ]
    
    def __init__(self, root: tk.Tk):
        """تهيئة الساعة الرقمية"""
        self.root = root
        self.root.title("🕐 Digital Multi-Timezone Clock")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # المتغيرات
        self.timezones: List[Timezone] = []
        self.running = True
        self.time_format = TimeFormat.FORMAT_24H
        self.theme_name = "DARK"
        self.theme = ClockTheme.DARK.value
        self.config_file = "clock_config.json"
        
        # تحميل الإعدادات المحفوظة
        self.load_config()
        
        # إعداد الواجهة
        self.setup_ui()
        
        # بدء حلقة تحديث الوقت
        self.update_clock()
        
        # معالج الإغلاق
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self) -> None:
        """إعداد واجهة المستخدم"""
        # تعيين اللون الخلفي
        self.root.configure(bg=self.theme["bg"])
        
        # إنشاء الخطوط
        title_font = tkFont.Font(family="Arial", size=18, weight="bold")
        clock_font = tkFont.Font(family="Courier New", size=28, weight="bold")
        small_font = tkFont.Font(family="Arial", size=10)
        
        # الرأس
        header_frame = tk.Frame(self.root, bg=self.theme["accent"], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🕐 DIGITAL MULTI-TIMEZONE CLOCK",
            font=title_font,
            bg=self.theme["accent"],
            fg=self.theme["bg"]
        )
        title_label.pack(pady=15)
        
        # شريط الأدوات
        toolbar_frame = tk.Frame(self.root, bg=self.theme["bg"], height=50)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
        toolbar_frame.pack_propagate(False)
        
        # زر إضافة منطقة زمنية
        add_btn = tk.Button(
            toolbar_frame,
            text="➕ Add Timezone",
            command=self.open_add_timezone_window,
            font=small_font,
            bg=self.theme["button_bg"],
            fg=self.theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # زر الإزالة
        remove_btn = tk.Button(
            toolbar_frame,
            text="🗑️ Remove Selected",
            command=self.remove_selected_timezone,
            font=small_font,
            bg=self.theme["button_bg"],
            fg=self.theme["error"],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # زر تغيير التنسيق
        format_btn = tk.Button(
            toolbar_frame,
            text="⏰ Toggle Format",
            command=self.toggle_time_format,
            font=small_font,
            bg=self.theme["button_bg"],
            fg=self.theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        format_btn.pack(side=tk.LEFT, padx=5)
        
        # زر تغيير المظهر
        theme_btn = tk.Button(
            toolbar_frame,
            text="🎨 Change Theme",
            command=self.open_theme_menu,
            font=small_font,
            bg=self.theme["button_bg"],
            fg=self.theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        theme_btn.pack(side=tk.LEFT, padx=5)
        
        # زر المساعدة
        help_btn = tk.Button(
            toolbar_frame,
            text="❓ Help",
            command=self.show_help,
            font=small_font,
            bg=self.theme["button_bg"],
            fg=self.theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        help_btn.pack(side=tk.LEFT, padx=5)
        
        # إطار الساعات
        self.clocks_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.clocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # إنشاء Canvas للساعات بتمرير سلس
        self.canvas = tk.Canvas(
            self.clocks_frame,
            bg=self.theme["bg"],
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            self.clocks_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme["bg"])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # دعم التمرير بعجلة الماوس
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # تخزين عناصر الساعات
        self.clock_labels = []
        self.clock_frames = []
        
        # عرض الساعات
        self.display_clocks()
        
        # شريط الحالة
        status_frame = tk.Frame(self.root, bg=self.theme["accent"], height=30)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text=f"Format: {self.time_format.value.upper()} | Timezones: {len(self.timezones)}",
            font=small_font,
            bg=self.theme["accent"],
            fg=self.theme["bg"]
        )
        self.status_label.pack(pady=5)
    
    def display_clocks(self) -> None:
        """عرض جميع الساعات"""
        # مسح الساعات السابقة
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.clock_labels = []
        self.clock_frames = []
        
        # إنشاء صف من الساعات
        current_row_frame = None
        column_count = 0
        clocks_per_row = 3
        
        for i, tz in enumerate(self.timezones):
            if column_count % clocks_per_row == 0:
                current_row_frame = tk.Frame(self.scrollable_frame, bg=self.theme["bg"])
                current_row_frame.pack(fill=tk.X, padx=5, pady=5)
            
            clock_frame = self.create_clock_widget(current_row_frame, tz)
            self.clock_frames.append(clock_frame)
            column_count += 1
    
    def create_clock_widget(self, parent: tk.Frame, tz: Timezone) -> tk.Frame:
        """إنشاء عنصر ساعة واحدة"""
        clock_frame = tk.Frame(
            parent,
            bg=self.theme["clock_bg"],
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=15
        )
        clock_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # اسم المنطقة الزمنية
        name_label = tk.Label(
            clock_frame,
            text=f"{tz.emoji} {tz.name}",
            font=tkFont.Font(family="Arial", size=12, weight="bold"),
            bg=self.theme["clock_bg"],
            fg=self.theme["accent"]
        )
        name_label.pack(pady=(0, 10))
        
        # الدولة
        if tz.country:
            country_label = tk.Label(
                clock_frame,
                text=tz.country,
                font=tkFont.Font(family="Arial", size=9),
                bg=self.theme["clock_bg"],
                fg=self.theme["clock_fg"]
            )
            country_label.pack(pady=(0, 5))
        
        # الوقت الكبير
        time_label = tk.Label(
            clock_frame,
            text="00:00:00",
            font=tkFont.Font(family="Courier New", size=28, weight="bold"),
            bg=self.theme["clock_bg"],
            fg=self.theme["clock_fg"],
            family="monospace"
        )
        time_label.pack(pady=10)
        
        # التاريخ
        date_label = tk.Label(
            clock_frame,
            text="",
            font=tkFont.Font(family="Arial", size=9),
            bg=self.theme["clock_bg"],
            fg=self.theme["clock_fg"]
        )
        date_label.pack(pady=(5, 0))
        
        # المنطقة الزمنية
        tz_offset_label = tk.Label(
            clock_frame,
            text="",
            font=tkFont.Font(family="Arial", size=8),
            bg=self.theme["clock_bg"],
            fg=self.theme["accent"]
        )
        tz_offset_label.pack(pady=(2, 10))
        
        # زر الحذف
        delete_btn = tk.Button(
            clock_frame,
            text="❌ Remove",
            command=lambda: self.remove_timezone(tz),
            font=tkFont.Font(family="Arial", size=8),
            bg=self.theme["error"],
            fg="white",
            relief=tk.FLAT,
            padx=5,
            pady=2
        )
        delete_btn.pack(pady=(5, 0))
        
        # تخزين المراجع
        self.clock_labels.append({
            "tz": tz,
            "time": time_label,
            "date": date_label,
            "offset": tz_offset_label,
            "frame": clock_frame
        })
        
        return clock_frame
    
    def update_clock(self) -> None:
        """تحديث الساعات"""
        if not self.running:
            return
        
        for clock in self.clock_labels:
            try:
                tz = clock["tz"]
                current_time = tz.get_current_time()
                
                # تنسيق الوقت
                if self.time_format == TimeFormat.FORMAT_12H:
                    time_str = current_time.strftime("%I:%M:%S %p")
                else:
                    time_str = current_time.strftime("%H:%M:%S")
                
                # تحديث التاريخ
                date_str = current_time.strftime("%A, %B %d, %Y")
                
                # حساب الفرق الزمني
                local_tz = datetime.now().astimezone().tzinfo
                offset = current_time.strftime("%z")
                offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                
                # تحديث العناصر
                clock["time"].config(text=time_str)
                clock["date"].config(text=date_str)
                clock["offset"].config(text=offset_formatted)
                
            except Exception as e:
                print(f"خطأ في تحديث الساعة: {e}")
        
        # تحديث شريط الحالة
        self.status_label.config(
            text=f"Format: {self.time_format.value.upper()} | Timezones: {len(self.timezones)} | Last Update: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # جدولة التحديث التالي
        self.root.after(1000, self.update_clock)
    
    def toggle_time_format(self) -> None:
        """تبديل تنسيق الوقت"""
        if self.time_format == TimeFormat.FORMAT_24H:
            self.time_format = TimeFormat.FORMAT_12H
        else:
            self.time_format = TimeFormat.FORMAT_24H
        
        self.save_config()
    
    def open_theme_menu(self) -> None:
        """فتح قائمة تغيير المظهر"""
        theme_window = tk.Toplevel(self.root)
        theme_window.title("Select Theme")
        theme_window.geometry("300x200")
        theme_window.configure(bg=self.theme["bg"])
        
        label = tk.Label(
            theme_window,
            text="Choose a Theme:",
            font=tkFont.Font(family="Arial", size=12, weight="bold"),
            bg=self.theme["bg"],
            fg=self.theme["fg"]
        )
        label.pack(pady=10)
        
        for theme_name in ["DARK", "LIGHT", "NEON"]:
            btn = tk.Button(
                theme_window,
                text=theme_name,
                command=lambda t=theme_name: self.change_theme(t),
                font=tkFont.Font(family="Arial", size=10),
                bg=self.theme["button_bg"],
                fg=self.theme["accent"],
                relief=tk.FLAT,
                padx=20,
                pady=10,
                width=20
            )
            btn.pack(pady=5)
    
    def change_theme(self, theme_name: str) -> None:
        """تغيير المظهر"""
        self.theme_name = theme_name
        self.theme = getattr(ClockTheme, theme_name).value
        self.save_config()
        
        # إعادة تشغيل الواجهة
        self.root.configure(bg=self.theme["bg"])
        
        # تحديث الألوان الموجودة
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=self.theme["bg"])
            elif isinstance(child, tk.Label):
                child.configure(bg=self.theme["bg"], fg=self.theme["fg"])
        
        # إعادة رسم الساعات
        self.display_clocks()
        
        messagebox.showinfo("Success", f"Theme changed to {theme_name}!")
    
    def open_add_timezone_window(self) -> None:
        """فتح نافذة إضافة منطقة زمنية"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Timezone")
        add_window.geometry("400x500")
        add_window.configure(bg=self.theme["bg"])
        
        # قائمة المناطق الزمنية المتاحة
        all_timezones = [
            ("London", "Europe/London", "🇬🇧"),
            ("New York", "America/New_York", "🗽"),
            ("Los Angeles", "America/Los_Angeles", "🌞"),
            ("Tokyo", "Asia/Tokyo", "🗾"),
            ("Dubai", "Asia/Dubai", "🏜️"),
            ("Sydney", "Australia/Sydney", "🦘"),
            ("Cairo", "Africa/Cairo", "🔺"),
            ("São Paulo", "America/Sao_Paulo", "⚽"),
            ("Singapore", "Asia/Singapore", "🏙️"),
            ("Hong Kong", "Asia/Hong_Kong", "🏙️"),
            ("Bangkok", "Asia/Bangkok", "🐘"),
            ("Mumbai", "Asia/Kolkata", "🐯"),
            ("Moscow", "Europe/Moscow", "🇷🇺"),
            ("Paris", "Europe/Paris", "🗼"),
            ("Berlin", "Europe/Berlin", "🍺"),
            ("Madrid", "Europe/Madrid", "🇪🇸"),
            ("Toronto", "America/Toronto", "🍁"),
            ("Mexico City", "America/Mexico_City", "🌵"),
            ("Istanbul", "Europe/Istanbul", "🕌"),
            ("Seoul", "Asia/Seoul", "🏯"),
        ]
        
        label = tk.Label(
            add_window,
            text="Select a Timezone:",
            font=tkFont.Font(family="Arial", size=12, weight="bold"),
            bg=self.theme["bg"],
            fg=self.theme["fg"]
        )
        label.pack(pady=10)
        
        # Listbox للمناطق الزمنية
        listbox_frame = tk.Frame(add_window, bg=self.theme["bg"])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            bg=self.theme["clock_bg"],
            fg=self.theme["clock_fg"],
            font=tkFont.Font(family="Arial", size=10),
            height=15
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for name, tz_str, emoji in all_timezones:
            listbox.insert(tk.END, f"{emoji} {name}")
        
        def add_selected():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                name, tz_str, emoji = all_timezones[idx]
                
                # التحقق من عدم إضافة نفس المنطقة مرتين
                if not any(t.timezone_str == tz_str for t in self.timezones):
                    new_tz = Timezone(name, tz_str, f"{emoji}", emoji)
                    self.timezones.append(new_tz)
                    self.save_config()
                    self.display_clocks()
                    add_window.destroy()
                    messagebox.showinfo("Success", f"Added {name}!")
                else:
                    messagebox.showwarning("Warning", f"{name} is already added!")
            else:
                messagebox.showwarning("Warning", "Please select a timezone!")
        
        add_btn = tk.Button(
            add_window,
            text="✅ Add Selected",
            command=add_selected,
            font=tkFont.Font(family="Arial", size=10),
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_btn.pack(pady=10)
    
    def remove_timezone(self, tz: Timezone) -> None:
        """إزالة منطقة زمنية"""
        if tz in self.timezones:
            self.timezones.remove(tz)
            self.save_config()
            self.display_clocks()
    
    def remove_selected_timezone(self) -> None:
        """إزالة المنطقة الزمنية المحددة"""
        if self.timezones:
            if messagebox.askyesno("Confirm", "Remove the last timezone?"):
                self.timezones.pop()
                self.save_config()
                self.display_clocks()
    
    def save_config(self) -> None:
        """حفظ الإعدادات في ملف"""
        config = {
            "timezones": [tz.to_dict() for tz in self.timezones],
            "time_format": self.time_format.value,
            "theme": self.theme_name
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"خطأ في حفظ الإعدادات: {e}")
    
    def load_config(self) -> None:
        """تحميل الإعدادات من ملف"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.timezones = [
                    Timezone.from_dict(tz) for tz in config.get("timezones", self.DEFAULT_TIMEZONES)
                ]
                
                time_format_str = config.get("time_format", "24h")
                self.time_format = TimeFormat.FORMAT_24H if time_format_str == "24h" else TimeFormat.FORMAT_12H
                
                self.theme_name = config.get("theme", "DARK")
                self.theme = getattr(ClockTheme, self.theme_name).value
            else:
                self.timezones = self.DEFAULT_TIMEZONES.copy()
                self.save_config()
        
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
            self.timezones = self.DEFAULT_TIMEZONES.copy()
    
    def show_help(self) -> None:
        """عرض نافذة المساعدة"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("500x400")
        help_window.configure(bg=self.theme["bg"])
        
        text_widget = tk.Text(
            help_window,
            bg=self.theme["clock_bg"],
            fg=self.theme["clock_fg"],
            font=tkFont.Font(family="Arial", size=10),
            padx=10,
            pady=10,
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_text = """
🕐 DIGITAL MULTI-TIMEZONE CLOCK - HELP

Features:
• Display time in multiple timezones simultaneously
• Add/Remove timezones as needed
• Toggle between 12-hour and 24-hour formats
• Change application theme (Dark, Light, Neon)
• View date and timezone offset for each location
• Automatic time updates every second
• Configuration saved automatically

How to Use:
1. Click "➕ Add Timezone" to add new timezones
2. Select a timezone from the list
3. Use "⏰ Toggle Format" to switch time format
4. Click "🎨 Change Theme" to change appearance
5. Use "❌ Remove" button on each clock to delete it

Tips:
• The application automatically saves your settings
• You can add up to 20+ timezones
• All times are updated in real-time
• Scroll down to see more clocks if needed

Keyboard Shortcuts:
• Use mouse wheel to scroll through timezones
• Click any timezone to view more details

Enjoy! 🌍
        """
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def on_closing(self) -> None:
        """معالج إغلاق النافذة"""
        self.running = False
        self.save_config()
        self.root.destroy()


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("   🕐 DIGITAL MULTI-TIMEZONE CLOCK")
    print("=" * 60)
    print("\n✓ Starting application...")
    
    try:
        root = tk.Tk()
        clock = DigitalClock(root)
        
        print("✓ Application loaded successfully!")
        print("\n" + "=" * 60)
        print("   Application is running... (Close window to exit)")
        print("=" * 60 + "\n")
        
        root.mainloop()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
