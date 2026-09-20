import os
import re
import json
import calendar
from datetime import datetime

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform, get_color_from_hex

from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

# -------------------------------------------------------------------
# CONSTANTS & PALETTE (2026 Modern Design Palette)
# -------------------------------------------------------------------
COLOR_MUSTARD = get_color_from_hex("#E5A93B")
COLOR_MUSTARD_DARK = get_color_from_hex("#C78D24")
COLOR_FOREST_GREEN = get_color_from_hex("#1B4332")
COLOR_STYLISH_BLUE = get_color_from_hex("#1D3557")
COLOR_CARD_BG = get_color_from_hex("#FAFAFA")
COLOR_WHITE = get_color_from_hex("#FFFFFF")
COLOR_TEXT_MAIN = get_color_from_hex("#212529")
COLOR_TEXT_MUTED = get_color_from_hex("#6C757D")
COLOR_ACCENT_RED = get_color_from_hex("#E63946")
COLOR_ACCENT_GREEN = get_color_from_hex("#2A9D8F")
COLOR_GLASS_CARD = (1, 1, 1, 0.85)

DEFAULT_OPERATIONS_DATA = [
    {"name": "Rise - Front", "rate": 0.50},
    {"name": "Rise - Back", "rate": 0.50},
    {"name": "Belt Rip Joint", "rate": 0.20},
    {"name": "Belt Joint - Tag", "rate": 0.20},
    {"name": "Belt & Rip Joint", "rate": 0.90},
    {"name": "Front Panel Folding", "rate": 0.50},
    {"name": "Back Panel Folding", "rate": 0.50},
    {"name": "Center Panel Folding", "rate": 0.20},
    {"name": "Center Panel Closing", "rate": 0.40},
    {"name": "Full Panel Joint", "rate": 1.80},
    {"name": "Ready Belt + Panel", "rate": 1.20},
    {"name": "Single Needle", "rate": 1.00},
    {"name": "Peak", "rate": 0.30},
    {"name": "V-Joint", "rate": 0.40},
    {"name": "Trimming", "rate": 0.80},
    {"name": "Rope", "rate": 0.20}
]

DATA_FILE = "rk_garments_data.json"

# -------------------------------------------------------------------
# UI COMPONENTS (Custom Rounded Cards & Inputs)
# -------------------------------------------------------------------
class CardWidget(BoxLayout):
    def __init__(self, bg_color=COLOR_WHITE, radius=[16], border_color=None, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.border_color = border_color
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Soft Shadow Layer
            Color(0, 0, 0, 0.05)
            RoundedRectangle(pos=(self.x + 2, self.y - 2), size=self.size, radius=self.radius)
            # Main Background Layer
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            # Optional Glass/Border Layer
            if self.border_color:
                Color(*self.border_color)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius[0]), width=1.1)

class CustomButton(Button):
    def __init__(self, bg_color=COLOR_STYLISH_BLUE, radius=[12], **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bg_color = bg_color
        self.radius = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

class GlassInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)
        self.cursor_color = COLOR_FOREST_GREEN
        self.foreground_color = COLOR_TEXT_MAIN
        self.padding = [dp(14), dp(12), dp(14), dp(12)]
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            Color(0.8, 0.8, 0.8, 1)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 10), width=1)

# -------------------------------------------------------------------
# CALENDAR PICKER MODAL COMPONENT
# -------------------------------------------------------------------
class CalendarModal(Popup):
    def __init__(self, target_button, **kwargs):
        super().__init__(**kwargs)
        self.target_button = target_button
        self.title = "Select Entry Date"
        self.size_hint = (0.9, 0.65)
        self.auto_dismiss = True

        today = datetime.now()
        try:
            current_date_dt = datetime.strptime(self.target_button.text.replace("📅 Date: ", "").strip(), "%d/%m/%Y")
            self.year = current_date_dt.year
            self.month = current_date_dt.month
        except Exception:
            self.year = today.year
            self.month = today.month

        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))

        # Month/Year Navigation Bar
        nav = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_prev = CustomButton(text="<", bg_color=COLOR_STYLISH_BLUE, size_hint_x=0.2)
        btn_prev.bind(on_release=self.prev_month)
        
        self.lbl_month_year = Label(
            text=f"{calendar.month_name[self.month]} {self.year}",
            bold=True,
            font_size=sp(16),
            color=COLOR_TEXT_MAIN,
            size_hint_x=0.6
        )

        btn_next = CustomButton(text=">", bg_color=COLOR_STYLISH_BLUE, size_hint_x=0.2)
        btn_next.bind(on_release=self.next_month)

        nav.add_widget(btn_prev)
        nav.add_widget(self.lbl_month_year)
        nav.add_widget(btn_next)
        root.add_widget(nav)

        # Days of Week Bar
        week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        week_grid = GridLayout(cols=7, size_hint_y=None, height=dp(25))
        for day in week_days:
            week_grid.add_widget(Label(text=day, bold=True, font_size=sp(12), color=COLOR_TEXT_MUTED))
        root.add_widget(week_grid)

        # Calendar Dates Grid
        self.days_grid = GridLayout(cols=7, spacing=dp(4), size_hint=(1, 1))
        root.add_widget(self.days_grid)

        self.content = root
        self.populate_days()

    def populate_days(self):
        self.days_grid.clear_widgets()
        self.lbl_month_year.text = f"{calendar.month_name[self.month]} {self.year}"

        month_calendar = calendar.monthcalendar(self.year, self.month)

        for week in month_calendar:
            for day in week:
                if day == 0:
                    self.days_grid.add_widget(Widget())
                else:
                    btn_day = CustomButton(
                        text=str(day),
                        bg_color=COLOR_MUSTARD if day == datetime.now().day and self.month == datetime.now().month and self.year == datetime.now().year else COLOR_STYLISH_BLUE,
                        font_size=sp(14)
                    )
                    btn_day.bind(on_release=lambda x, d=day: self.select_date(d))
                    self.days_grid.add_widget(btn_day)

    def prev_month(self, instance):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.populate_days()

    def next_month(self, instance):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.populate_days()

    def select_date(self, day):
        selected_dt = datetime(self.year, self.month, day)
        selected_str = selected_dt.strftime("%d/%m/%Y")
        self.target_button.text = f"📅 Date: {selected_str}"
        self.dismiss()

# -------------------------------------------------------------------
# APP DATA MANAGEMENT LAYER
# -------------------------------------------------------------------
class DataManager:
    @staticmethod
    def get_path():
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), DATA_FILE)
        return DATA_FILE

    @classmethod
    def load_data(cls):
        path = cls.get_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"staff": None, "lots": {}, "entries": []}

    @classmethod
    def save_data(cls, data):
        path = cls.get_path()
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Save failed:", e)

# -------------------------------------------------------------------
# 1. SPLASH SCREEN
# -------------------------------------------------------------------
class SplashScreen(Screen):
    def on_enter(self):
        layout = CardWidget(bg_color=COLOR_MUSTARD, orientation='vertical', padding=dp(20))
        layout.add_widget(Widget(size_hint_y=0.35))
        
        txt_welcome = Label(
            text="Welcome to",
            font_size=sp(18),
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=dp(30)
        )
        txt_brand = Label(
            text="RK GARMENTS",
            font_size=sp(36),
            bold=True,
            color=COLOR_FOREST_GREEN,
            size_hint_y=None,
            height=dp(60)
        )
        
        layout.add_widget(txt_welcome)
        layout.add_widget(txt_brand)
        layout.add_widget(Widget(size_hint_y=0.65))
        
        self.clear_widgets()
        self.add_widget(layout)
        Clock.schedule_once(self.goto_next, 2.0)

    def goto_next(self, dt):
        data = DataManager.load_data()
        self.manager.transition = SlideTransition(direction='left')
        if not data.get("staff"):
            self.manager.current = "setup"
        else:
            self.manager.current = "login"

# -------------------------------------------------------------------
# 2. FIRST-TIME STAFF SETUP
# -------------------------------------------------------------------
class StaffSetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = CardWidget(bg_color=COLOR_MUSTARD, orientation='vertical', padding=dp(24), spacing=dp(16))
        
        header = Label(
            text="Welcome to RK Garments",
            font_size=sp(24),
            bold=True,
            color=COLOR_STYLISH_BLUE,
            size_hint_y=None,
            height=dp(50)
        )
        root.add_widget(header)

        card = CardWidget(
            bg_color=COLOR_WHITE,
            radius=[20],
            orientation='vertical',
            padding=dp(20),
            spacing=dp(12),
            size_hint_y=None,
            height=dp(360)
        )

        card.add_widget(Label(text="What's your nice name?", color=COLOR_TEXT_MAIN, font_size=sp(16), size_hint_y=None, height=dp(24), halign='left'))
        self.inp_name = GlassInput(hint_text="e.g. Jhon", multiline=False, size_hint_y=None, height=dp(44))
        card.add_widget(self.inp_name)

        card.add_widget(Label(text="Set your passcode", color=COLOR_TEXT_MAIN, font_size=sp(16), size_hint_y=None, height=dp(24), halign='left'))
        self.inp_pass = GlassInput(hint_text="Enter passcode", password=True, multiline=False, input_filter='int', size_hint_y=None, height=dp(44))
        card.add_widget(self.inp_pass)

        card.add_widget(Label(text="Confirm passcode", color=COLOR_TEXT_MAIN, font_size=sp(16), size_hint_y=None, height=dp(24), halign='left'))
        self.inp_confirm = GlassInput(hint_text="Confirm passcode", password=True, multiline=False, input_filter='int', size_hint_y=None, height=dp(44))
        card.add_widget(self.inp_confirm)

        btn_save = CustomButton(text="SAVE & CONTINUE", bg_color=COLOR_FOREST_GREEN, bold=True, size_hint_y=None, height=dp(48))
        btn_save.bind(on_release=self.process_setup)
        card.add_widget(btn_save)

        root.add_widget(card)
        root.add_widget(Widget())
        self.add_widget(root)

    def process_setup(self, instance):
        name = self.inp_name.text.strip()
        passcode = self.inp_pass.text.strip()
        confirm = self.inp_confirm.text.strip()

        if not name or not passcode:
            self.show_popup("Error", "Please complete all fields.")
            return
        if passcode != confirm:
            self.show_popup("Error", "Passcodes do not match.")
            return

        data = DataManager.load_data()
        data["staff"] = {"name": name, "passcode": passcode}
        DataManager.save_data(data)

        # Success Modal Display
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(Label(text="Thanks 🙏", font_size=sp(20), bold=True))
        content.add_widget(Label(text=f"Your passcode is {passcode}", font_size=sp(16)))
        content.add_widget(Label(text="Note: Please don't miss your passcode", font_size=sp(12), color=COLOR_ACCENT_RED))
        
        btn = CustomButton(text="OK", bg_color=COLOR_STYLISH_BLUE, size_hint_y=None, height=dp(40))
        content.add_widget(btn)

        popup = Popup(title="Setup Complete", content=content, size_hint=(0.85, 0.4), auto_dismiss=False)
        btn.bind(on_release=lambda x: self.finish_setup(popup))
        popup.open()

    def finish_setup(self, popup):
        popup.dismiss()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "login"

    def show_popup(self, title, msg):
        pop = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.3))
        pop.open()

# -------------------------------------------------------------------
# 3. LOGIN PAGE
# -------------------------------------------------------------------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = CardWidget(bg_color=COLOR_MUSTARD, orientation='vertical', padding=dp(24), spacing=dp(10))
        root.add_widget(Widget(size_hint_y=0.15))

        brand = Label(
            text="RK GARMENTS",
            font_size=sp(34),
            bold=True,
            color=COLOR_FOREST_GREEN,
            size_hint_y=None,
            height=dp(50)
        )
        root.add_widget(brand)
        root.add_widget(Widget(size_hint_y=0.05))

        card_wrapper = AnchorLayout(anchor_x='center', size_hint_y=None, height=dp(220))
        card = CardWidget(
            bg_color=COLOR_WHITE,
            radius=[20],
            orientation='vertical',
            padding=dp(20),
            spacing=dp(12),
            size_hint_x=0.9
        )

        lbl = Label(text="Enter login code", color=COLOR_TEXT_MAIN, font_size=sp(16), bold=True, size_hint_y=None, height=dp(24))
        self.inp_code = GlassInput(hint_text="Passcode", password=True, multiline=False, input_filter='int', size_hint_y=None, height=dp(44))
        
        btn_login = CustomButton(text="LOGIN", bg_color=COLOR_MUSTARD_DARK, bold=True, size_hint_y=None, height=dp(44))
        btn_login.bind(on_release=self.validate_login)

        card.add_widget(lbl)
        card.add_widget(self.inp_code)
        card.add_widget(btn_login)
        card_wrapper.add_widget(card)

        root.add_widget(card_wrapper)
        root.add_widget(Widget(size_hint_y=0.45))
        self.add_widget(root)

    def validate_login(self, instance):
        data = DataManager.load_data()
        staff = data.get("staff", {})
        entered = self.inp_code.text.strip()

        if staff and entered == staff.get("passcode"):
            self.inp_code.text = ""
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = "lots"
        else:
            pop = Popup(title="Access Denied", content=Label(text="Invalid passcode. Try again."), size_hint=(0.8, 0.25))
            pop.open()

# -------------------------------------------------------------------
# 4. LOT MANAGEMENT PAGE
# -------------------------------------------------------------------
class LotManagementScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout_built = False

    def on_pre_enter(self):
        self.refresh_ui()

    def refresh_ui(self):
        self.clear_widgets()
        data = DataManager.load_data()
        staff_name = data.get("staff", {}).get("name", "Staff")

        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        # App Header with Integrated Logout Button
        header = CardWidget(bg_color=COLOR_FOREST_GREEN, radius=[12], size_hint_y=None, height=dp(64), padding=dp(10))
        header_box = BoxLayout(orientation='horizontal')
        
        header_box.add_widget(Label(text="RK GARMENTS", font_size=sp(18), bold=True, color=COLOR_WHITE, halign='left'))
        
        right_info = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_x=None)
        right_info.bind(minimum_width=right_info.setter('width'))
        
        staff_lbl = Label(text=f"👤 {staff_name}", font_size=sp(13), color=COLOR_MUSTARD, size_hint_x=None)
        staff_lbl.bind(texture_size=staff_lbl.setter('size'))
        
        btn_logout = CustomButton(text="LOGOUT", bg_color=COLOR_ACCENT_RED, font_size=sp(11), bold=True, size_hint=(None, None), size=(dp(70), dp(34)))
        btn_logout.bind(on_release=self.process_logout)
        
        right_info.add_widget(staff_lbl)
        right_info.add_widget(btn_logout)
        
        header_box.add_widget(right_info)
        header.add_widget(header_box)
        root.add_widget(header)

        # Lot Listing
        scroll = ScrollView(size_hint=(1, 1))
        self.lot_grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.lot_grid.bind(minimum_height=self.lot_grid.setter('height'))

        lots = data.get("lots", {})
        if not lots:
            empty_lbl = Label(text="No active lots found.\nCreate or Import a Lot below.", color=COLOR_TEXT_MUTED, font_size=sp(14), size_hint_y=None, height=dp(100), halign='center')
            self.lot_grid.add_widget(empty_lbl)
        else:
            for lot_name, ops in lots.items():
                card = CardWidget(bg_color=COLOR_CARD_BG, radius=[14], size_hint_y=None, height=dp(70), padding=dp(12), border_color=(0.8, 0.8, 0.8, 1))
                box = BoxLayout(orientation='horizontal')
                
                info = BoxLayout(orientation='vertical')
                info.add_widget(Label(text=lot_name, font_size=sp(18), bold=True, color=COLOR_TEXT_MAIN, halign='left'))
                info.add_widget(Label(text=f"{len(ops)} Operations registered", font_size=sp(12), color=COLOR_TEXT_MUTED, halign='left'))
                
                btn_open = CustomButton(text="OPEN", bg_color=COLOR_STYLISH_BLUE, size_hint=(None, 1), width=dp(80))
                btn_open.bind(on_release=lambda x, name=lot_name: self.open_lot(name))

                box.add_widget(info)
                box.add_widget(btn_open)
                card.add_widget(box)
                self.lot_grid.add_widget(card)

        scroll.add_widget(self.lot_grid)
        root.add_widget(scroll)

        # Bottom Exact Concept Buttons
        bottom_nav = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(150))
        
        btn_add = CustomButton(text="＋ ADD NEW LOT", bg_color=COLOR_FOREST_GREEN, bold=True, size_hint_y=None, height=dp(44))
        btn_add.bind(on_release=self.add_new_lot_dialog)

        btn_default = CustomButton(text="⚙ DEFAULT OPERATIONS", bg_color=COLOR_STYLISH_BLUE, bold=True, size_hint_y=None, height=dp(44))
        btn_default.bind(on_release=self.default_operations_dialog)

        btn_import = CustomButton(text="📥 IMPORT OPERATIONS", bg_color=COLOR_MUSTARD_DARK, bold=True, size_hint_y=None, height=dp(44))
        btn_import.bind(on_release=self.import_operations_dialog)

        bottom_nav.add_widget(btn_add)
        bottom_nav.add_widget(btn_default)
        bottom_nav.add_widget(btn_import)
        root.add_widget(bottom_nav)

        self.add_widget(root)

    def process_logout(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'login'

    def open_lot(self, lot_name):
        ops_screen = self.manager.get_screen('operations')
        ops_screen.set_lot(lot_name)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'operations'

    def add_new_lot_dialog(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        inp = GlassInput(hint_text="e.g. Black 006I", multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(Label(text="Enter New Lot Name:"))
        content.add_widget(inp)

        btn = CustomButton(text="CREATE LOT", bg_color=COLOR_FOREST_GREEN, size_hint_y=None, height=dp(40))
        content.add_widget(btn)

        popup = Popup(title="Add New Lot", content=content, size_hint=(0.85, 0.35))

        def create_lot(x):
            lot_name = inp.text.strip()
            if lot_name:
                data = DataManager.load_data()
                if lot_name not in data["lots"]:
                    data["lots"][lot_name] = []
                    DataManager.save_data(data)
                popup.dismiss()
                self.refresh_ui()

        btn.bind(on_release=create_lot)
        popup.open()

    def default_operations_dialog(self, instance):
        data = DataManager.load_data()
        lots = list(data.get("lots", {}).keys())

        if not lots:
            Popup(title="Error", content=Label(text="No lots exist. Create a lot first."), size_hint=(0.8, 0.25)).open()
            return

        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="Select Lot to apply Default Operations:"))
        
        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(title="Default Operations", content=content, size_hint=(0.85, 0.6))

        for l_name in lots:
            b = CustomButton(text=l_name, bg_color=COLOR_STYLISH_BLUE, size_hint_y=None, height=dp(40))
            b.bind(on_release=lambda x, name=l_name: self.apply_default_ops(name, popup))
            grid.add_widget(b)

        scroll.add_widget(grid)
        content.add_widget(scroll)
        popup.open()

    def apply_default_ops(self, lot_name, popup):
        data = DataManager.load_data()
        data["lots"][lot_name] = DEFAULT_OPERATIONS_DATA.copy()
        DataManager.save_data(data)
        popup.dismiss()
        self.refresh_ui()

    def import_operations_dialog(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="Enter Lot Name for Import:"))
        inp_name = GlassInput(hint_text="e.g. Black 006I", multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(inp_name)
        
        btn_next = CustomButton(text="NEXT", bg_color=COLOR_FOREST_GREEN, size_hint_y=None, height=dp(40))
        content.add_widget(btn_next)

        pop1 = Popup(title="Import Operations - Step 1", content=content, size_hint=(0.85, 0.35))

        def proceed_to_editor(x):
            lot_name = inp_name.text.strip()
            if not lot_name:
                return
            pop1.dismiss()
            self.open_import_editor(lot_name)

        btn_next.bind(on_release=proceed_to_editor)
        pop1.open()

    def open_import_editor(self, lot_name):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text=f"Paste WhatsApp Text for '{lot_name}':", size_hint_y=None, height=dp(20)))

        editor = TextInput(
            hint_text="1. Rise Front - 0.5\n2. Rise Back - 0.5\nBelt : 1.0",
            multiline=True,
            size_hint=(1, 1)
        )
        content.add_widget(editor)

        btn_save = CustomButton(text="IMPORT & SAVE", bg_color=COLOR_FOREST_GREEN, size_hint_y=None, height=dp(44))
        content.add_widget(btn_save)

        pop2 = Popup(title=f"Import Editor: {lot_name}", content=content, size_hint=(0.9, 0.75))

        def parse_and_save(x):
            text = editor.text
            parsed_ops = []
            
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                clean_line = re.sub(r'^\d+[\.\)\s]+', '', line).strip()
                match = re.search(r'^(.*?)\s*[\-:]\s*(\d+(?:\.\d+)?)$', clean_line)
                if match:
                    op_name = match.group(1).strip()
                    try:
                        op_rate = float(match.group(2))
                        if op_name:
                            parsed_ops.append({"name": op_name, "rate": op_rate})
                    except ValueError:
                        continue

            if parsed_ops:
                data = DataManager.load_data()
                data["lots"][lot_name] = parsed_ops
                DataManager.save_data(data)
                pop2.dismiss()
                self.refresh_ui()
            else:
                Popup(title="Import Failed", content=Label(text="No valid operations parsed. Check format."), size_hint=(0.8, 0.25)).open()

        btn_save.bind(on_release=parse_and_save)
        pop2.open()

# -------------------------------------------------------------------
# 5. OPERATION PAGE
# -------------------------------------------------------------------
class OperationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_lot = None

    def set_lot(self, lot_name):
        self.current_lot = lot_name
        self.refresh_ui()

    def refresh_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        # Top Bar
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        btn_back = CustomButton(text="← BACK", bg_color=COLOR_STYLISH_BLUE, size_hint=(None, 1), width=dp(80))
        btn_back.bind(on_release=self.go_back)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text=f"LOT: {self.current_lot}", font_size=sp(18), bold=True, color=COLOR_FOREST_GREEN))
        root.add_widget(top_bar)

        # Operations Listing
        data = DataManager.load_data()
        ops = data.get("lots", {}).get(self.current_lot, [])

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        colors = [
            (0.92, 0.95, 0.98, 1),
            (0.95, 0.92, 0.98, 1),
            (0.92, 0.98, 0.95, 1),
            (0.98, 0.95, 0.92, 1)
        ]

        if not ops:
            empty_box = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160), padding=dp(10))
            empty_lbl = Label(text="No operations registered for this lot.", color=COLOR_TEXT_MUTED, font_size=sp(14), size_hint_y=None, height=dp(30), halign='center')
            
            btn_import_here = CustomButton(text="📥 IMPORT OPERATIONS", bg_color=COLOR_MUSTARD_DARK, bold=True, size_hint_y=None, height=dp(44))
            btn_import_here.bind(on_release=self.import_direct)

            empty_box.add_widget(empty_lbl)
            empty_box.add_widget(btn_import_here)
            grid.add_widget(empty_box)
        else:
            for idx, op in enumerate(ops, start=1):
                bg_col = colors[idx % len(colors)]
                card = CardWidget(bg_color=bg_col, radius=[12], size_hint_y=None, height=dp(60), padding=dp(10))
                
                box = BoxLayout(orientation='horizontal')
                idx_lbl = Label(text=f"{idx:02d}", size_hint_x=None, width=dp(36), bold=True, color=COLOR_STYLISH_BLUE)
                
                name_lbl = Label(
                    text=op["name"],
                    font_size=sp(15),
                    bold=True,
                    color=COLOR_TEXT_MAIN,
                    halign='left',
                    valign='middle'
                )
                name_lbl.bind(size=name_lbl.setter('text_size'))

                rate_lbl = Label(
                    text=f"₹{op['rate']:.2f}",
                    size_hint_x=None,
                    width=dp(80),
                    bold=True,
                    color=COLOR_FOREST_GREEN,
                    halign='right'
                )

                box.add_widget(idx_lbl)
                box.add_widget(name_lbl)
                box.add_widget(rate_lbl)
                card.add_widget(box)

                card.bind(on_touch_down=lambda instance, touch, o=op: self.on_card_touch(instance, touch, o))
                grid.add_widget(card)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        # Bottom Bar
        bottom_bar = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(48))
        btn_salary = CustomButton(text="💰 TOTAL SALARY", bg_color=COLOR_FOREST_GREEN, bold=True)
        btn_salary.bind(on_release=self.open_salary_report)
        bottom_bar.add_widget(btn_salary)

        root.add_widget(bottom_bar)
        self.add_widget(root)

    def import_direct(self, instance):
        lots_screen = self.manager.get_screen('lots')
        lots_screen.open_import_editor(self.current_lot)

    def on_card_touch(self, instance, touch, op_data):
        if instance.collide_point(*touch.pos):
            prod_screen = self.manager.get_screen('production_entry')
            prod_screen.setup_entry(self.current_lot, op_data)
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'production_entry'

    def go_back(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'lots'

    def open_salary_report(self, instance):
        sal_screen = self.manager.get_screen('salary_report')
        sal_screen.load_report(self.current_lot)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'salary_report'

# -------------------------------------------------------------------
# 6 & 7. PRODUCTION ENTRY & REPEATED ACCUMULATION
# -------------------------------------------------------------------
class ProductionEntryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lot_name = None
        self.op_data = None
        self.build_ui()

    def build_ui(self):
        self.root_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # Top Header
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        btn_back = CustomButton(text="← CANCEL", bg_color=COLOR_TEXT_MUTED, size_hint=(None, 1), width=dp(90))
        btn_back.bind(on_release=self.go_back)
        top_bar.add_widget(btn_back)
        self.root_layout.add_widget(top_bar)

        # Main Entry Card
        card = CardWidget(bg_color=COLOR_WHITE, radius=[16], orientation='vertical', padding=dp(16), spacing=dp(12))

        self.lbl_op_name = Label(text="", font_size=sp(18), bold=True, color=COLOR_FOREST_GREEN, size_hint_y=None, height=dp(30))
        self.lbl_rate = Label(text="", font_size=sp(16), color=COLOR_TEXT_MUTED, size_hint_y=None, height=dp(24))
        
        # Interactive Date Selector Button
        self.btn_date = CustomButton(text="", bg_color=COLOR_STYLISH_BLUE, font_size=sp(14), bold=True, size_hint_y=None, height=dp(40))
        self.btn_date.bind(on_release=self.open_calendar)

        card.add_widget(self.lbl_op_name)
        card.add_widget(self.lbl_rate)
        card.add_widget(self.btn_date)

        card.add_widget(Label(text="Quantity:", color=COLOR_TEXT_MAIN, size_hint_y=None, height=dp(20), halign='left'))
        
        # Quantity Text Input with Explicit Dark Text & Cursor
        self.inp_qty = GlassInput(hint_text="Enter quantity", input_filter='int', multiline=False, size_hint_y=None, height=dp(48))
        self.inp_qty.foreground_color = COLOR_TEXT_MAIN
        self.inp_qty.cursor_color = COLOR_FOREST_GREEN
        card.add_widget(self.inp_qty)

        card.add_widget(Label(text="Remarks (Optional):", color=COLOR_TEXT_MAIN, size_hint_y=None, height=dp(20), halign='left'))
        self.inp_remarks = GlassInput(hint_text="e.g. Urgent batch", multiline=False, size_hint_y=None, height=dp(48))
        card.add_widget(self.inp_remarks)

        card.add_widget(Widget())

        self.btn_save = CustomButton(text="SAVE", bg_color=COLOR_STYLISH_BLUE, bold=True, size_hint_y=None, height=dp(50))
        self.btn_save.bind(on_release=self.save_entry)
        card.add_widget(self.btn_save)

        self.root_layout.add_widget(card)
        self.add_widget(self.root_layout)

    def open_calendar(self, instance):
        CalendarModal(target_button=self.btn_date).open()

    def setup_entry(self, lot_name, op_data):
        self.lot_name = lot_name
        self.op_data = op_data
        
        self.lbl_op_name.text = op_data["name"]
        self.lbl_rate.text = f"Rate: ₹{op_data['rate']:.2f}"
        
        today_str = datetime.now().strftime("%d/%m/%Y")
        self.btn_date.text = f"📅 Date: {today_str}"

        self.inp_qty.text = ""
        self.inp_remarks.text = ""
        
        self.btn_save.text = "SAVE"
        self.btn_save.bg_color = COLOR_STYLISH_BLUE
        self.btn_save.update_canvas()

        Clock.schedule_once(self.focus_qty, 0.2)

    def focus_qty(self, dt):
        self.inp_qty.focus = True

    def save_entry(self, instance):
        qty_str = self.inp_qty.text.strip()
        if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
            Popup(title="Invalid Quantity", content=Label(text="Please enter a valid positive number."), size_hint=(0.8, 0.25)).open()
            return

        added_qty = int(qty_str)
        remarks = self.inp_remarks.text.strip()
        
        selected_date_str = self.btn_date.text.replace("📅 Date: ", "").strip()
        try:
            dt_obj = datetime.strptime(selected_date_str, "%d/%m/%Y")
            report_date = dt_obj.strftime("%d/%m")
        except Exception:
            selected_date_str = datetime.now().strftime("%d/%m/%Y")
            report_date = datetime.now().strftime("%d/%m")

        data = DataManager.load_data()
        entries = data.get("entries", [])
        staff_name = data.get("staff", {}).get("name", "Unknown")

        # REPEATED ENTRY ACCUMULATION LOGIC
        existing_entry = None
        for entry in entries:
            if (entry.get("staff") == staff_name and
                entry.get("lot") == self.lot_name and
                entry.get("op_name") == self.op_data["name"] and
                entry.get("full_date") == selected_date_str):
                existing_entry = entry
                break

        if existing_entry:
            existing_entry["qty"] += added_qty
            existing_entry["amount"] = existing_entry["qty"] * existing_entry["rate"]
            if remarks:
                prev_rem = existing_entry.get("remarks", "")
                existing_entry["remarks"] = f"{prev_rem}; {remarks}" if prev_rem else remarks
        else:
            new_entry = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "staff": staff_name,
                "lot": self.lot_name,
                "op_name": self.op_data["name"],
                "rate": self.op_data["rate"],
                "qty": added_qty,
                "amount": added_qty * self.op_data["rate"],
                "full_date": selected_date_str,
                "report_date": report_date,
                "remarks": remarks
            }
            entries.append(new_entry)

        data["entries"] = entries
        DataManager.save_data(data)

        self.btn_save.text = "✓ SAVED"
        self.btn_save.bg_color = COLOR_ACCENT_GREEN
        self.btn_save.update_canvas()

        Clock.schedule_once(self.return_to_ops, 0.8)

    def return_to_ops(self, dt):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'operations'

    def go_back(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'operations'

# -------------------------------------------------------------------
# 8 & 9. SALARY REPORT & DELETE
# -------------------------------------------------------------------
class SalaryReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_lot = None

    def load_report(self, lot_name):
        self.current_lot = lot_name
        self.refresh_ui()

    def refresh_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))

        # Top Bar
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        btn_back = CustomButton(text="← BACK", bg_color=COLOR_STYLISH_BLUE, size_hint=(None, 1), width=dp(80))
        btn_back.bind(on_release=self.go_back)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text=f"SALARY REPORT: {self.current_lot}", font_size=sp(16), bold=True, color=COLOR_FOREST_GREEN))
        root.add_widget(top_bar)

        # Table Header
        header_card = CardWidget(bg_color=COLOR_STYLISH_BLUE, radius=[8], size_hint_y=None, height=dp(36), padding=dp(4))
        tbl_header = BoxLayout(orientation='horizontal')
        tbl_header.add_widget(Label(text="Date", size_hint_x=0.15, bold=True, color=COLOR_WHITE, font_size=sp(12)))
        tbl_header.add_widget(Label(text="Operation", size_hint_x=0.40, bold=True, color=COLOR_WHITE, font_size=sp(12), halign='left'))
        tbl_header.add_widget(Label(text="Rate", size_hint_x=0.12, bold=True, color=COLOR_WHITE, font_size=sp(12)))
        tbl_header.add_widget(Label(text="Qty", size_hint_x=0.10, bold=True, color=COLOR_WHITE, font_size=sp(12)))
        tbl_header.add_widget(Label(text="Amount", size_hint_x=0.15, bold=True, color=COLOR_WHITE, font_size=sp(12)))
        tbl_header.add_widget(Label(text="", size_hint_x=0.08))
        header_card.add_widget(tbl_header)
        root.add_widget(header_card)

        # Scrollable Salary Table
        data = DataManager.load_data()
        entries = [e for e in data.get("entries", []) if e.get("lot") == self.current_lot]

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        grand_total = 0.0

        if not entries:
            grid.add_widget(Label(text="No salary entries recorded yet.", color=COLOR_TEXT_MUTED, size_hint_y=None, height=dp(60)))
        else:
            for item in entries:
                grand_total += item["amount"]
                row_card = CardWidget(bg_color=COLOR_WHITE, radius=[6], size_hint_y=None, height=dp(44), padding=dp(2), border_color=(0.9, 0.9, 0.9, 1))
                row = BoxLayout(orientation='horizontal')

                date_lbl = Label(text=item["report_date"], size_hint_x=0.15, font_size=sp(11), color=COLOR_TEXT_MAIN)
                
                op_lbl = Label(text=item["op_name"], size_hint_x=0.40, font_size=sp(11), color=COLOR_TEXT_MAIN, halign='left', valign='middle')
                op_lbl.bind(size=op_lbl.setter('text_size'))

                rate_lbl = Label(text=f"₹{item['rate']:.2f}", size_hint_x=0.12, font_size=sp(11), color=COLOR_TEXT_MAIN)
                qty_lbl = Label(text=str(item["qty"]), size_hint_x=0.10, font_size=sp(11), bold=True, color=COLOR_TEXT_MAIN)
                amt_lbl = Label(text=f"₹{item['amount']:.2f}", size_hint_x=0.15, font_size=sp(11), bold=True, color=COLOR_FOREST_GREEN)

                btn_del = CustomButton(text="🗑", bg_color=COLOR_ACCENT_RED, size_hint_x=0.08, radius=[6])
                btn_del.bind(on_release=lambda x, entry=item: self.confirm_delete(entry))

                row.add_widget(date_lbl)
                row.add_widget(op_lbl)
                row.add_widget(rate_lbl)
                row.add_widget(qty_lbl)
                row.add_widget(amt_lbl)
                row.add_widget(btn_del)

                row_card.add_widget(row)
                grid.add_widget(row_card)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        # Grand Total Dashboard Panel
        total_card = CardWidget(bg_color=COLOR_MUSTARD, radius=[12], size_hint_y=None, height=dp(60), padding=dp(12))
        total_box = BoxLayout(orientation='horizontal')
        total_box.add_widget(Label(text="GRAND TOTAL", font_size=sp(16), bold=True, color=COLOR_STYLISH_BLUE, halign='left'))
        total_box.add_widget(Label(text=f"₹ {grand_total:,.2f}", font_size=sp(22), bold=True, color=COLOR_FOREST_GREEN, halign='right'))
        total_card.add_widget(total_box)

        root.add_widget(total_card)
        self.add_widget(root)

    def confirm_delete(self, entry):
        content = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text="Are you sure?", font_size=sp(18), bold=True, color=COLOR_ACCENT_RED))
        
        info = f"Date: {entry['report_date']}\nOp: {entry['op_name']}\nQty: {entry['qty']}  |  Amt: ₹{entry['amount']:.2f}"
        content.add_widget(Label(text=info, font_size=sp(13), color=COLOR_TEXT_MAIN, halign='center'))

        btn_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        btn_cancel = CustomButton(text="CANCEL", bg_color=COLOR_TEXT_MUTED)
        btn_delete = CustomButton(text="DELETE", bg_color=COLOR_ACCENT_RED, bold=True)

        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_delete)
        content.add_widget(btn_box)

        popup = Popup(title="Delete Entry", content=content, size_hint=(0.85, 0.4))
        btn_cancel.bind(on_release=popup.dismiss)
        btn_delete.bind(on_release=lambda x: self.execute_delete(entry["id"], popup))
        popup.open()

    def execute_delete(self, entry_id, popup):
        popup.dismiss()
        data = DataManager.load_data()
        data["entries"] = [e for e in data.get("entries", []) if e.get("id") != entry_id]
        DataManager.save_data(data)
        self.refresh_ui()

    def go_back(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'operations'

# -------------------------------------------------------------------
# MAIN APPLICATION CONTROLLER & BUILDOZER COMPATIBILITY
# -------------------------------------------------------------------
class RKGarmentsApp(App):
    def build(self):
        self.title = "RK Garments Salary Management"
        Window.clearcolor = (0.96, 0.96, 0.96, 1)

        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(StaffSetupScreen(name='setup'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(LotManagementScreen(name='lots'))
        sm.add_widget(OperationScreen(name='operations'))
        sm.add_widget(ProductionEntryScreen(name='production_entry'))
        sm.add_widget(SalaryReportScreen(name='salary_report'))

        Window.bind(on_keyboard=self.on_hardware_back)
        return sm

    def on_hardware_back(self, window, key, *args):
        if key == 27:
            sm = self.root
            current = sm.current
            if current == 'salary_report':
                sm.transition = SlideTransition(direction='right')
                sm.current = 'operations'
                return True
            elif current == 'production_entry':
                sm.transition = SlideTransition(direction='right')
                sm.current = 'operations'
                return True
            elif current == 'operations':
                sm.transition = SlideTransition(direction='right')
                sm.current = 'lots'
                return True
            elif current == 'lots':
                return False
        return False

if __name__ == '__main__':
    RKGarmentsApp().run()
