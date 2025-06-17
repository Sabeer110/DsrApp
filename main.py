import json
import os
import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy import platform

# Note: Permissions are now requested in on_start for better practice
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
    except ImportError:
        pass

# PDF Generation Library
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# --- Basic Setup & Helpers ---
Window.clearcolor = (0.2, 0.2, 0.2, 1)
DATA_FILE, USERS_FILE, NOTES_FILE, ADMIN_USER, ADMIN_PASS = "data.json", "users.json", "notes.json", "sabeer125", "qw4hd"

def load_json(f, d):
    if not os.path.exists(f) or os.path.getsize(f) == 0: return d
    try:
        with open(f, "r") as fp: return json.load(fp)
    except (json.JSONDecodeError, FileNotFoundError): return d

def save_json(f, d):
    with open(f, "w") as fp: json.dump(d, fp, indent=4)

def verify_password(p, s): return p == s

def hash_password(p): return p

def get_download_path():
    if platform == "android":
        from android.storage import primary_external_storage_path
        path = os.path.join(primary_external_storage_path(), "Download")
        if not os.path.exists(path):
            try: os.makedirs(path)
            except OSError as e: return App.get_running_app().user_data_dir
        return path
    else: return os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

# --- Styled Widgets & Popups ---
class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.color = (1, 1, 1, 0.9); self.bind(width=self.update_text_size)
    def update_text_size(self, instance, width): self.text_size = (width, None)

class StyledButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', (0.1, 0.5, 0.8, 1)); kwargs.setdefault('background_normal', ''); kwargs.setdefault('font_size', '16sp'); kwargs.setdefault('size_hint_y', None); kwargs.setdefault('height', dp(44))
        super().__init__(**kwargs)

class StyledTextInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', (0.15, 0.15, 0.15, 1)); kwargs.setdefault('foreground_color', (1, 1, 1, 1)); kwargs.setdefault('multiline', False); kwargs.setdefault('font_size', '16sp'); kwargs.setdefault('size_hint_y', None); kwargs.setdefault('height', dp(44))
        super().__init__(**kwargs)

class DatePickerPopup(Popup):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs); self.callback = callback; self.title = "Select a Date"; self.size_hint = (0.9, 0.6)
        with self.canvas.before: Color(0.1, 0.1, 0.1, 1); self.rect = Rectangle(size=self.size, pos=self.pos); self.bind(size=self._update_rect, pos=self._update_rect)
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        spinners_layout = GridLayout(cols=3, spacing=dp(10)); today = datetime.date.today()
        self.day_spinner = Spinner(text=f'{today.day:02}', values=[f'{i:02}' for i in range(1, 32)], size_hint_y=None, height=dp(44))
        self.month_spinner = Spinner(text=f'{today.month:02}', values=[f'{i:02}' for i in range(1, 13)], size_hint_y=None, height=dp(44))
        self.year_spinner = Spinner(text=str(today.year), values=[str(y) for y in range(today.year - 10, today.year + 1)], size_hint_y=None, height=dp(44))
        spinners_layout.add_widget(self.day_spinner); spinners_layout.add_widget(self.month_spinner); spinners_layout.add_widget(self.year_spinner)
        buttons_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(44)); ok_button = StyledButton(text="OK", on_press=self.on_ok); cancel_button = StyledButton(text="Cancel", on_press=self.dismiss, background_color=(0.6, 0.2, 0.2, 1))
        buttons_layout.add_widget(ok_button); buttons_layout.add_widget(cancel_button); layout.add_widget(spinners_layout); layout.add_widget(buttons_layout); self.content = layout
    def _update_rect(self, i, v): self.rect.pos, self.rect.size = i.pos, i.size
    def on_ok(self, i): self.callback(f"{self.year_spinner.text}-{self.month_spinner.text}-{self.day_spinner.text}"); self.dismiss()

class EditDsrPopup(Popup):
    def __init__(self, entry_data, save_callback, **kwargs):
        super().__init__(**kwargs); self.title = f"Edit Entry (Bill: {entry_data.get('bill')})"; self.size_hint = (0.9, 0.8); self.original_entry = entry_data; self.save_callback = save_callback
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        grid.add_widget(StyledLabel(text="Party Name:", height=dp(44))); self.party_input = StyledTextInput(text=self.original_entry.get('party', ''), height=dp(44)); grid.add_widget(self.party_input)
        grid.add_widget(StyledLabel(text="Credit:", height=dp(44))); self.credit_input = StyledTextInput(text=str(self.original_entry.get('credit', 0)), height=dp(44)); grid.add_widget(self.credit_input)
        grid.add_widget(StyledLabel(text="Payment:", height=dp(44))); self.payment_input = StyledTextInput(text=str(self.original_entry.get('payment', 0)), height=dp(44)); grid.add_widget(self.payment_input)
        grid.add_widget(StyledLabel(text="Return:", height=dp(44))); self.return_input = StyledTextInput(text=str(self.original_entry.get('return', 0)), height=dp(44)); grid.add_widget(self.return_input)
        grid.add_widget(StyledLabel(text="Discount:", height=dp(44))); self.discount_input = StyledTextInput(text=str(self.original_entry.get('discount', 0)), height=dp(44)); grid.add_widget(self.discount_input)
        layout.add_widget(grid)
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10)); save_btn = StyledButton(text="Save Changes", on_press=self.save, background_color=(0, 0.7, 0.2, 1)); cancel_btn = StyledButton(text="Cancel", on_press=self.dismiss, background_color=(0.6, 0.2, 0.2, 1))
        buttons_layout.add_widget(save_btn); buttons_layout.add_widget(cancel_btn); layout.add_widget(buttons_layout); self.content = layout
    def save(self, instance):
        try:
            credit, payment, ret, disc = float(self.credit_input.text or 0), float(self.payment_input.text or 0), float(self.return_input.text or 0), float(self.discount_input.text or 0); balance = credit - (payment + ret + disc)
            updated_entry = self.original_entry.copy(); updated_entry.update({"party": self.party_input.text.strip(), "credit": credit, "payment": payment, "return": ret, "discount": disc, "balance": balance,})
            self.save_callback(self.original_entry, updated_entry); self.dismiss()
        except ValueError: App.get_running_app().root.get_screen('admin').show_popup("Error", "Please enter valid numbers.")

class FilterPopup(Popup):
    def __init__(self, ledger_screen_ref, **kwargs):
        super().__init__(**kwargs); self.ledger_screen = ledger_screen_ref; self.title = "Filter Ledger Entries"; self.size_hint = (0.9, 0.7)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        date_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5)); date_layout.add_widget(StyledLabel(text="Date:", size_hint_x=0.3)); self.date_button = StyledButton(text="Filter by Date", on_press=self.open_date_picker); date_layout.add_widget(self.date_button); date_layout.add_widget(StyledButton(text="Clear", on_press=self.clear_date_filter, size_hint_x=0.3, background_color=(0.6,0.6,0.6,1))); layout.add_widget(date_layout)
        party_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5)); party_layout.add_widget(StyledLabel(text="Party:", size_hint_x=0.3)); self.party_filter_input = StyledTextInput(hint_text="Filter by Party Name"); party_layout.add_widget(self.party_filter_input); layout.add_widget(party_layout)
        bill_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5)); bill_layout.add_widget(StyledLabel(text="Bill No:", size_hint_x=0.3)); self.bill_filter_input = StyledTextInput(hint_text="Filter by Bill No"); bill_layout.add_widget(self.bill_filter_input); layout.add_widget(bill_layout)
        action_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10)); action_layout.add_widget(StyledButton(text="Apply Filters", on_press=self.apply_and_dismiss, background_color=(0, 0.7, 0.2, 1))); action_layout.add_widget(StyledButton(text="Clear All", on_press=self.clear_all_filters)); layout.add_widget(action_layout)
        self.content = layout
    def open_date_picker(self, i): DatePickerPopup(callback=self.on_date_selected).open()
    def on_date_selected(self, d): self.date_button.text = d
    def clear_date_filter(self, *a): self.date_button.text = "Filter by Date"
    def clear_all_filters(self, *a): self.clear_date_filter(); self.party_filter_input.text = ""; self.bill_filter_input.text = ""
    def apply_and_dismiss(self, *a): self.ledger_screen.apply_filters(date=self.date_button.text if "Filter" not in self.date_button.text else None, party=self.party_filter_input.text.strip(), bill=self.bill_filter_input.text.strip()); self.dismiss()

# --- Main Widgets ---
class DSRRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.orientation = 'horizontal'; self.size_hint = (None, None); self.height = dp(44); self.spacing = dp(5); self.width = dp(1100)
        self.bill_input = StyledTextInput(size_hint_x=None, width=dp(100)); self.party_input = StyledTextInput(size_hint_x=None, width=dp(250)); self.credit_input = StyledTextInput(size_hint_x=None, width=dp(120))
        self.payment_input = StyledTextInput(size_hint_x=None, width=dp(120)); self.return_input = StyledTextInput(size_hint_x=None, width=dp(120)); self.discount_input = StyledTextInput(size_hint_x=None, width=dp(120))
        self.balance_input = StyledTextInput(readonly=True, size_hint_x=None, width=dp(150))
        for widget in [self.bill_input, self.party_input, self.credit_input, self.payment_input, self.return_input, self.discount_input, self.balance_input]: self.add_widget(widget)
        self.bill_input.bind(text=self.on_bill_change)
        for w in [self.credit_input, self.payment_input, self.return_input, self.discount_input]: w.bind(text=self.update_balance)
    def on_bill_change(self, i, v):
        all_data = load_json(DATA_FILE, []); found_data = next((e for e in reversed(all_data) if isinstance(e, dict) and e.get("bill") == v.strip()), None)
        if found_data:
            self.party_input.text = found_data.get("party", "")
            self.credit_input.text = str(float(found_data.get("balance", 0))) if found_data.get("balance") is not None else ''
            self.payment_input.text, self.return_input.text, self.discount_input.text = "", "", ""
        else:
            self.party_input.text, self.credit_input.text, self.payment_input.text, self.return_input.text, self.discount_input.text = "", "", "", "", ""
        self.update_balance()
    def update_balance(self, *args):
        try:
            c, p, r, d = float(self.credit_input.text or 0), float(self.payment_input.text or 0), float(self.return_input.text or 0), float(self.discount_input.text or 0)
            self.balance_input.text = f"{c - (p + r + d):.2f}"
        except ValueError:
            self.balance_input.text = "Error"

class HeaderRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.orientation = 'horizontal'; self.size_hint = (None, None); self.height = dp(44); self.spacing = dp(5); self.width = dp(1100)
        self.add_widget(StyledLabel(text="Bill", size_hint_x=None, width=dp(100))); self.add_widget(StyledLabel(text="Party", size_hint_x=None, width=dp(250)))
        self.add_widget(StyledLabel(text="Credit", size_hint_x=None, width=dp(120))); self.add_widget(StyledLabel(text="Payment", size_hint_x=None, width=dp(120)))
        self.add_widget(StyledLabel(text="Return", size_hint_x=None, width=dp(120))); self.add_widget(StyledLabel(text="Discount", size_hint_x=None, width=dp(120)))
        self.add_widget(StyledLabel(text="Balance", size_hint_x=None, width=dp(150)))

class NoteRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.orientation = 'horizontal'; self.size_hint_y = None; self.height = dp(44); self.spacing = dp(5)
        self.description_input = StyledTextInput(hint_text="Note Description (e.g., Online, Cheque)")
        self.amount_input = StyledTextInput(hint_text="Amount", size_hint_x=0.4, input_filter='float')
        self.add_widget(self.description_input); self.add_widget(self.amount_input)

class LedgerDataRow(BoxLayout):
    def __init__(self, entry, screen_ref, **kwargs):
        super().__init__(**kwargs); self.orientation = 'horizontal'; self.size_hint = (None, None); self.height = dp(44); self.spacing = dp(5); self.width = dp(1250)
        self.add_widget(StyledLabel(text=entry.get('bill', ''), size_hint_x=None, width=dp(100))); self.add_widget(StyledLabel(text=entry.get('party', ''), size_hint_x=None, width=dp(250)))
        self.add_widget(StyledLabel(text=f"{entry.get('credit', 0):.2f}", size_hint_x=None, width=dp(120))); self.add_widget(StyledLabel(text=f"{entry.get('payment', 0):.2f}", size_hint_x=None, width=dp(120)))
        self.add_widget(StyledLabel(text=f"{entry.get('return', 0):.2f}", size_hint_x=None, width=dp(120))); self.add_widget(StyledLabel(text=f"{entry.get('discount', 0):.2f}", size_hint_x=None, width=dp(120)))
        self.add_widget(StyledLabel(text=f"{entry.get('balance', 0):.2f}", size_hint_x=None, width=dp(150)))
        self.add_widget(StyledButton(text="Edit", size_hint_x=None, width=dp(120), on_press=lambda x: screen_ref.open_edit_popup(entry)))

class BaseCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.orientation = 'vertical'; self.size_hint_y = None; self.bind(minimum_height=self.setter('height')); self.padding = dp(10); self.spacing = dp(5)
        with self.canvas.before: Color(0.25, 0.25, 0.25, 1); self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(10),]); self.bind(pos=self.update_rect, size=self.update_rect)
    def update_rect(self, i, v): self.rect.pos, self.rect.size = i.pos, i.size
    def add_info(self, key, value):
        info_row = BoxLayout(size_hint_y=None, height=dp(25)); info_row.add_widget(StyledLabel(text=f"{key}:", bold=True, size_hint_x=0.4)); info_row.add_widget(StyledLabel(text=str(value), size_hint_x=0.6, halign='left'))
        self.add_widget(info_row)

class AdminDataRow(BaseCard):
    def __init__(self, entry_data, admin_panel_ref, **kwargs):
        super().__init__(**kwargs)
        self.add_info("User", entry_data.get('user', 'N/A')); self.add_info("Date", entry_data.get('date', 'N/A'))
        self.add_info("Bill No", entry_data.get('bill', 'N/A')); self.add_info("Party", entry_data.get('party', 'N/A'))
        self.add_info("Payment", f"{entry_data.get('payment', 0):.2f}"); self.add_info("Balance", f"{entry_data.get('balance', 0):.2f}")
        actions_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        edit_btn = StyledButton(text="Edit", on_press=lambda x: admin_panel_ref.open_edit_popup(entry_data))
        delete_btn = StyledButton(text="Delete", on_press=lambda x: admin_panel_ref.confirm_action_popup( "Delete DSR Entry", "Are you sure? Enter Admin Password to delete this entry.", lambda: self.delete_entry_confirmed(entry_data, admin_panel_ref)), background_color=(0.8, 0.2, 0.2, 1))
        actions_layout.add_widget(edit_btn); actions_layout.add_widget(delete_btn); self.add_widget(actions_layout)
    def delete_entry_confirmed(self, entry_data, admin_panel_ref):
        all_data = load_json(DATA_FILE, []); updated_data = [entry for entry in all_data if entry != entry_data]; save_json(DATA_FILE, updated_data)
        admin_panel_ref.show_popup("Success", "DSR Entry deleted successfully."); admin_panel_ref.apply_filters()

# --- Screen Classes ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        container = BoxLayout()
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(15), size_hint=(0.9, None), height=dp(450), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with layout.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self.rect = RoundedRectangle(size=layout.size, pos=layout.pos, radius=[dp(15),])
            layout.bind(pos=self.update_rect, size=self.update_rect)
        
        title = StyledLabel(text="DSR Application", font_size='28sp', size_hint_y=None, height=dp(50), halign='center', bold=True)
        self.username_input = StyledTextInput(hint_text="Username")
        self.password_input = StyledTextInput(hint_text="Password", password=True)
        login_btn = StyledButton(text="Login", on_press=self.login)
        signup_btn = StyledButton(text="Sign Up", on_press=self.signup)
        admin_btn = StyledButton(text="Admin Panel", on_press=self.go_to_admin, background_color=(0.5, 0.5, 0.5, 1))
        
        layout.add_widget(title)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        layout.add_widget(signup_btn)
        layout.add_widget(admin_btn)
        container.add_widget(layout)
        self.add_widget(container)

    def update_rect(self, i, v): self.rect.pos, self.rect.size = i.pos, i.size
    
    def login(self, instance):
        user, pwd = self.username_input.text.strip(), self.password_input.text.strip()
        users = load_json(USERS_FILE, {})
        if user == ADMIN_USER:
            self.show_popup("Action Not Allowed", "Please use the 'Admin Panel' button for admin login.")
            return
        if user in users and verify_password(pwd, users.get(user)):
            self.manager.app.username, self.manager.app.is_admin = user, False
            self.manager.current = "main"
            self.password_input.text = ""
        else:
            self.show_popup("Login Failed", "Incorrect username or password.")
            self.password_input.text = ""

    def go_to_admin(self, instance):
        user, pwd = self.username_input.text.strip(), self.password_input.text.strip()
        # **FIXED**: Check against the hardcoded ADMIN_PASS, not the JSON file.
        if user == ADMIN_USER and verify_password(pwd, ADMIN_PASS):
            self.manager.app.username, self.manager.app.is_admin = user, True
            self.manager.current = "admin"
            self.password_input.text = ""
        else:
            self.show_popup("Access Denied", "Incorrect Admin credentials.")
            self.password_input.text = ""

    def signup(self, instance):
        user, pwd = self.username_input.text.strip(), self.password_input.text.strip()
        if not user or not pwd:
            self.show_popup("Error", "Username and Password cannot be empty.")
            return
        if user == ADMIN_USER:
            self.show_popup("Error", f"'{ADMIN_USER}' is a reserved username.")
            return
        users = load_json(USERS_FILE, {})
        if user in users:
            self.show_popup("Error", "User already exists.")
            return
        users[user] = hash_password(pwd)
        save_json(USERS_FILE, users)
        self.show_popup("Success", "Signup successful. You can now login.")
        self.username_input.text, self.password_input.text = "", ""

    def show_popup(self, title, msg):
        Popup(title=title, content=StyledLabel(text=msg, halign='center', valign='middle'), size_hint=(0.8, None), height=dp(150)).open()

class AdminPanel(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_date = None
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        filter_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        filter_box.bind(minimum_height=filter_box.setter('height'))
        filter_box.add_widget(StyledLabel(text="Admin Panel", font_size='20sp', size_hint_y=None, height=dp(40), halign='center'))
        
        user_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        user_layout.add_widget(StyledLabel(text="User:", size_hint_x=0.2))
        self.user_spinner = Spinner(text='All Users', values=['All Users'], size_hint_y=None, height=dp(44), size_hint_x=0.8)
        user_layout.add_widget(self.user_spinner)
        filter_box.add_widget(user_layout)
        
        action_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        action_layout.add_widget(StyledButton(text="Filter Users", on_press=self.apply_filters, background_color=(0, 0.7, 0.2, 1)))
        action_layout.add_widget(StyledButton(text="Manage Users", on_press=self.go_to_user_management, background_color=(0.8, 0.5, 0.1, 1)))
        filter_box.add_widget(action_layout)
        
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        
        layout.add_widget(filter_box)
        layout.add_widget(self.scroll)
        layout.add_widget(StyledButton(text="Back to Login", on_press=lambda x: setattr(self.manager, 'current', 'login')))
        self.add_widget(layout)

    def on_pre_enter(self, *args):
        users = list(load_json(USERS_FILE, {}).keys())
        # Filter out the admin user from the dropdown list for clarity
        self.user_spinner.values = ['All Users'] + [u for u in users if u != ADMIN_USER]
        self.user_spinner.text = 'All Users'
        self.apply_filters()

    def apply_filters(self, *args):
        self.grid.clear_widgets()
        all_data = load_json(DATA_FILE, [])
        filtered_data = [e for e in all_data if isinstance(e, dict)]
        if self.user_spinner.text != 'All Users':
            filtered_data = [e for e in filtered_data if e.get('user') == self.user_spinner.text]
        
        filtered_data.sort(key=lambda x: (x.get('date', ''), x.get('user', '')), reverse=True)
        
        if not filtered_data:
            self.grid.add_widget(StyledLabel(text="No entries found for this user.", size_hint_y=None, height=dp(40), halign='center'))
        else:
            for entry in filtered_data:
                self.grid.add_widget(AdminDataRow(entry_data=entry, admin_panel_ref=self))

    def show_popup(self, title, msg):
        Popup(title=title, content=StyledLabel(text=msg, halign='center', valign='middle'), size_hint=(0.8, None), height=dp(150)).open()

    def confirm_action_popup(self, title, message, success_callback):
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        box.add_widget(StyledLabel(text=message, halign='center'))
        password_input = StyledTextInput(password=True, multiline=False, hint_text="Admin Password")
        box.add_widget(password_input)
        
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        confirm_button = StyledButton(text="Confirm", background_color=(0, 0.7, 0.2, 1))
        cancel_button = StyledButton(text="Cancel", background_color=(0.6, 0.2, 0.2, 1))
        buttons_layout.add_widget(confirm_button)
        buttons_layout.add_widget(cancel_button)
        box.add_widget(buttons_layout)
        
        popup = Popup(title=title, content=box, size_hint=(0.9, None), height=dp(250), auto_dismiss=False)
        
        def on_confirm(instance):
            entered_password = password_input.text.strip()
            # **FIXED**: Verify against the hardcoded ADMIN_PASS constant.
            if verify_password(entered_password, ADMIN_PASS):
                success_callback()
                popup.dismiss()
            else:
                self.show_popup("Error", "Incorrect admin password.")
        
        confirm_button.bind(on_release=on_confirm)
        cancel_button.bind(on_release=popup.dismiss)
        popup.open()

    def go_to_user_management(self, instance):
        self.manager.current = 'user_management'

    def open_edit_popup(self, entry_data):
        popup = EditDsrPopup(entry_data=entry_data, save_callback=self.save_edited_entry_with_confirmation)
        popup.open()

    def save_edited_entry_with_confirmation(self, original_entry, updated_entry):
        def perform_save():
            all_data = load_json(DATA_FILE, [])
            try:
                # Find the index of the original entry and replace it
                index = all_data.index(original_entry)
                all_data[index] = updated_entry
                save_json(DATA_FILE, all_data)
                self.show_popup("Success", "Entry updated successfully.")
                self.apply_filters()
            except ValueError:
                self.show_popup("Error", "Could not find the original entry to update.")
        
        self.confirm_action_popup("Confirm Edit", "Enter Admin Password to save changes.", perform_save)

class UserManagementPanel(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        layout.add_widget(StyledLabel(text="Manage Users", font_size='24sp', size_hint_y=None, height=dp(50), halign='center'))
        
        header = GridLayout(cols=2, size_hint_y=None, height=dp(30), spacing=dp(2))
        header.add_widget(StyledLabel(text="Username", bold=True, size_hint_x=0.5, halign='left'))
        header.add_widget(StyledLabel(text="Actions", bold=True, size_hint_x=0.5, halign='left'))
        layout.add_widget(header)
        
        self.scroll = ScrollView()
        self.user_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.user_grid.bind(minimum_height=self.user_grid.setter('height'))
        self.scroll.add_widget(self.user_grid)
        layout.add_widget(self.scroll)
        
        layout.add_widget(StyledButton(text="Back to Admin Panel", on_press=lambda x: setattr(self.manager, 'current', 'admin'), background_color=(0.5,0.5,0.5,1)))
        self.add_widget(layout)

    def on_pre_enter(self, *args): self.refresh_user_list()

    def refresh_user_list(self):
        self.user_grid.clear_widgets()
        users = load_json(USERS_FILE, {})
        user_list = [u for u in sorted(users.keys()) if u != ADMIN_USER]
        for username in user_list:
            self.user_grid.add_widget(UserRow(username, self))

    def show_popup(self, title, msg):
        # Delegate to the admin panel's popup for consistency
        self.manager.get_screen('admin').show_popup(title, msg)

    def confirm_action_popup(self, title, message, callback):
        # Delegate to the admin panel's confirmation popup
        self.manager.get_screen('admin').confirm_action_popup(title, message, callback)

class UserRow(GridLayout):
    def __init__(self, username, user_management_panel_ref, **kwargs):
        super().__init__(**kwargs)
        self.cols, self.size_hint_y, self.height, self.spacing = 2, None, dp(44), dp(2)
        self.username, self.panel = username, user_management_panel_ref
        self.add_widget(StyledLabel(text=username, size_hint_x=0.5, halign='left'))
        actions_layout = BoxLayout(size_hint_x=0.5, spacing=dp(5))
        delete_btn = StyledButton(text="Delete", on_press=self.delete_user, background_color=(0.8, 0.2, 0.2, 1))
        actions_layout.add_widget(delete_btn)
        self.add_widget(actions_layout)

    def delete_user(self, instance):
        def confirmed_callback():
            users = load_json(USERS_FILE, {})
            if self.username in users:
                del users[self.username]
            save_json(USERS_FILE, users)
            self.panel.show_popup("Success", f"User '{self.username}' deleted.")
            self.panel.refresh_user_list()
        
        self.panel.confirm_action_popup("Confirm Deletion", f"Delete user '{self.username}'?", confirmed_callback)
        
class MainScreen(Screen):
    def on_pre_enter(self, *args):
        if not self.children:
            self.setup_ui()
        self.load_data_for_date(self.date_input.text)

    def setup_ui(self):
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        top.add_widget(StyledLabel(text=f"Welcome: {app.username}", size_hint_x=0.6))
        self.date_input = StyledTextInput(text=str(datetime.date.today()), readonly=True, size_hint_x=0.3)
        date_select_btn = StyledButton(text="...", size_hint_x=0.1, on_press=self.open_date_picker)
        top.add_widget(self.date_input)
        top.add_widget(date_select_btn)
        layout.add_widget(top)
        
        main_scroll = ScrollView(size_hint=(1, 1), scroll_type=['bars', 'content'], bar_width=dp(10))
        main_content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        main_content.bind(minimum_height=main_content.setter('height'))

        # DSR Section
        dsr_section = BoxLayout(orientation='vertical', size_hint_y=None)
        dsr_section.bind(minimum_height=dsr_section.setter('height'))
        dsr_section.add_widget(HeaderRow())
        dsr_scrollview = ScrollView(size_hint=(1, None), scroll_type=['bars', 'content'], bar_width=dp(10), height=dp(250)) # Increased height a bit
        self.grid = GridLayout(cols=1, spacing=dp(5), size_hint=(None, None), width=dp(1100))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        dsr_scrollview.add_widget(self.grid)
        dsr_section.add_widget(dsr_scrollview)
        main_content.add_widget(dsr_section)
        
        self.rows = []
        self.total_label = StyledLabel(text="Total Payment: 0.00", size_hint_y=None, height=dp(30), font_size='16sp', halign='right')
        main_content.add_widget(self.total_label)
        
        # Notes Section
        main_content.add_widget(StyledLabel(text="Notes / Other Collections", font_size='18sp', size_hint_y=None, height=dp(40)))
        notes_scroll = ScrollView(size_hint=(1, None), height=dp(150))
        self.notes_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.notes_grid.bind(minimum_height=self.notes_grid.setter('height'))
        notes_scroll.add_widget(self.notes_grid)
        main_content.add_widget(notes_scroll)
        self.notes = []

        main_scroll.add_widget(main_content)
        layout.add_widget(main_scroll)

        footer = BoxLayout(orientation='vertical', size_hint_y=None)
        footer.bind(minimum_height=footer.setter('height'))
        self.prepared_by_label = StyledLabel(halign='center', italic=True, size_hint_y=None, height=dp(30))
        
        self.btns_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        self.btns_layout.bind(minimum_height=self.btns_layout.setter('height'))
        self.btns_layout.add_widget(StyledButton(text="Add Row", on_press=lambda x: self.add_row()))
        self.btns_layout.add_widget(StyledButton(text="Add Note", on_press=lambda x: self.add_note_row()))
        self.btns_layout.add_widget(StyledButton(text="Save & PDF", on_press=self.save_and_generate_pdf, background_color=(0, 0.7, 0.2, 1)))
        self.btns_layout.add_widget(StyledButton(text="View Ledger", on_press=lambda x: setattr(self.manager, 'current', 'user_ledger'), background_color=(0.8, 0.5, 0.1, 1)))
        
        footer.add_widget(self.prepared_by_label)
        footer.add_widget(self.btns_layout)
        footer.add_widget(StyledButton(text="Logout", on_press=self.logout, background_color=(0.8, 0, 0, 1)))
        layout.add_widget(footer)
        self.add_widget(layout)
        Window.bind(on_resize=self.on_window_resize)
        self.on_window_resize(Window, Window.width, Window.height)

    def on_window_resize(self, window, width, height):
        if hasattr(self, 'btns_layout'):
            # Landscape mode (width > height) gets more columns for buttons
            if width > height:
                self.btns_layout.cols = 4 # All 4 buttons in one row
            else: # Portrait mode
                self.btns_layout.cols = 2 # 2x2 grid for buttons
                
    def load_data_for_date(self, selected_date):
        self.clear_screen()
        app = App.get_running_app()
        self.prepared_by_label.text = f"DSR Report prepared by {app.username}"
        all_data = load_json(DATA_FILE, [])
        user_data_for_date = [e for e in all_data if isinstance(e, dict) and e.get('user') == app.username and e.get('date') == selected_date]
        if user_data_for_date:
            for entry in user_data_for_date:
                self.add_row(data=entry)
        else:
            self.add_row()
            
        all_notes = load_json(NOTES_FILE, {})
        notes_key = f"{app.username}_{selected_date}"
        user_notes_for_date = all_notes.get(notes_key, [])
        if user_notes_for_date:
            for note in user_notes_for_date:
                self.add_note_row(data=note)
        else:
            self.add_note_row()

    def add_row(self, data=None):
        row = DSRRow()
        if data:
            row.bill_input.text = data.get('bill', '')
            row.party_input.text = data.get('party', '')
            row.credit_input.text = str(float(data.get('credit', 0)))
            row.payment_input.text = str(float(data.get('payment', 0)))
            row.return_input.text = str(float(data.get('return', 0)))
            row.discount_input.text = str(float(data.get('discount', 0)))
            row.update_balance()
        self.grid.add_widget(row)
        self.rows.append(row)
        # Bind payment input to update the total label
        row.payment_input.bind(text=self.calculate_total)
        self.calculate_total()

    def add_note_row(self, data=None):
        note_row = NoteRow()
        if data:
            # **FIXED**: Using 'description' key consistently.
            note_row.description_input.text = data.get('description', '')
            note_row.amount_input.text = str(data.get('amount', ''))
        self.notes_grid.add_widget(note_row)
        self.notes.append(note_row)
    
    def save_and_generate_pdf(self, instance):
        app, entry_date = App.get_running_app(), self.date_input.text.strip()
        new_entries, new_notes = [], []
        
        for row in self.rows:
            if bill := row.bill_input.text.strip():
                try:
                    new_entries.append({
                        "user": app.username, "date": entry_date, "bill": bill,
                        "party": row.party_input.text.strip(),
                        "credit": float(row.credit_input.text or 0),
                        "payment": float(row.payment_input.text or 0),
                        "return": float(row.return_input.text or 0),
                        "discount": float(row.discount_input.text or 0),
                        "balance": float(row.balance_input.text or 0)
                    })
                except ValueError:
                    self.show_popup("Save Error", f"Row for bill {bill} has an invalid number.")
                    return
        
        for note_row in self.notes:
            if desc := note_row.description_input.text.strip():
                try:
                    # **FIXED**: Saving with 'description' key.
                    new_notes.append({'description': desc, 'amount': float(note_row.amount_input.text or 0)})
                except ValueError:
                    self.show_popup("Save Error", f"Note '{desc}' has an invalid amount.")
                    return
        
        all_data = load_json(DATA_FILE, [])
        other_data = [e for e in all_data if not (isinstance(e,dict) and e.get('user') == app.username and e.get('date') == entry_date)]
        save_json(DATA_FILE, other_data + new_entries)
        
        all_notes = load_json(NOTES_FILE, {})
        all_notes[f"{app.username}_{entry_date}"] = new_notes
        save_json(NOTES_FILE, all_notes)
        
        self.generate_pdf(new_entries, new_notes, app.username, entry_date)
        # No need to reload data, as PDF generation is the final step for the user.
        # self.load_data_for_date(entry_date)

    def generate_pdf(self, entries, notes, username, date):
        path = get_download_path()
        filename = os.path.join(path, f"DSR_{username}_{date}.pdf")
        try:
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4
            margin = 1.5 * cm
            top_margin = height - margin
            line_height = 0.6 * cm
            y = top_margin
            
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2.0, y, f"DAILY SALES REPORT - {date}")
            y -= line_height * 2
            
            x_pos = {"bill": margin, "party": margin + 2.5*cm, "credit": margin + 7.5*cm, "payment": margin + 10*cm, "return": margin + 12.5*cm, "discount": margin + 15*cm, "balance": margin + 17.5*cm}
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_pos["bill"], y, "Bill No")
            c.drawString(x_pos["party"], y, "Party Name")
            c.drawRightString(x_pos["credit"] + 1.5*cm, y, "Credit") # Adjust for right alignment
            c.drawRightString(x_pos["payment"] + 1.5*cm, y, "Payment")
            c.drawRightString(x_pos["return"] + 1.5*cm, y, "Return")
            c.drawRightString(x_pos["discount"] + 1.5*cm, y, "Discount")
            c.drawRightString(x_pos["balance"] + 1.5*cm, y, "Balance")
            
            y -= line_height * 0.25
            c.line(margin, y, width - margin, y)
            y -= line_height
            
            c.setFont("Helvetica", 9)
            totals = {'payment': 0, 'return': 0, 'discount': 0}
            
            for entry in entries:
                if y < margin + 2*cm:
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = top_margin
                
                c.drawString(x_pos["bill"], y, entry.get('bill', ''))
                c.drawString(x_pos["party"], y, entry.get('party', ''))
                c.drawRightString(x_pos["credit"] + 1.5*cm, y, f"{entry.get('credit', 0):.2f}")
                c.drawRightString(x_pos["payment"] + 1.5*cm, y, f"{entry.get('payment', 0):.2f}")
                c.drawRightString(x_pos["return"] + 1.5*cm, y, f"{entry.get('return', 0):.2f}")
                c.drawRightString(x_pos["discount"] + 1.5*cm, y, f"{entry.get('discount', 0):.2f}")
                c.drawRightString(x_pos["balance"] + 1.5*cm, y, f"{entry.get('balance', 0):.2f}")
                
                for key in totals:
                    totals[key] += entry.get(key, 0)
                y -= line_height
            
            y -= line_height * 0.25
            c.line(margin, y, width - margin, y)
            y -= line_height
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_pos["party"], y, "Totals:")
            c.drawRightString(x_pos["payment"] + 1.5*cm, y, f"{totals['payment']:.2f}")
            c.drawRightString(x_pos["return"] + 1.5*cm, y, f"{totals['return']:.2f}")
            c.drawRightString(x_pos["discount"] + 1.5*cm, y, f"{totals['discount']:.2f}")
            
            total_notes_amount = 0
            if notes:
                y -= line_height * 2
                c.setFont("Helvetica-Bold", 12)
                c.drawString(margin, y, "Other Collections / Notes:")
                y -= line_height
                c.setFont("Helvetica", 10)
                for note in notes:
                    # **FIXED**: Using 'description' key.
                    c.drawString(margin + 0.5*cm, y, f"- {note.get('description', '')}:")
                    amount = note.get('amount', 0)
                    c.drawRightString(x_pos["payment"] + 1.5*cm, y, f"{amount:.2f}")
                    total_notes_amount += amount
                    y -= line_height
            
            y -= line_height
            c.line(margin, y, width - margin, y)
            y -= line_height
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(x_pos["payment"] + 1.5*cm, y, f"Grand Total: {totals['payment'] + total_notes_amount:.2f}")
            
            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(width/2.0, margin / 2, f"Report Prepared By: {username}")
            c.save()
            self.show_info_popup(f"PDF saved successfully to:\n{filename}")
        except Exception as e:
            self.show_popup("PDF Error", f"Could not generate PDF: {e}")

    def show_info_popup(self, message):
        Popup(title="Success", content=StyledLabel(text=message, halign='center'), size_hint=(0.9, None), height=dp(250)).open()

    def clear_screen(self):
        if hasattr(self, 'grid'):
            self.grid.clear_widgets()
            self.notes_grid.clear_widgets()
            self.rows.clear()
            self.notes.clear()
        self.calculate_total()
        
    def open_date_picker(self, i): DatePickerPopup(callback=self.on_date_selected).open()
    def on_date_selected(self, d): self.date_input.text = d; self.load_data_for_date(d)
    
    def calculate_total(self, *a):
        total = sum(float(r.payment_input.text or 0) for r in self.rows if r.payment_input.text.strip())
        self.total_label.text = f"Total Payment: {total:.2f}"

    def show_popup(self, t, m):
        Popup(title=t, content=StyledLabel(text=m, halign='center', valign='middle'), size_hint=(0.9, None), height=dp(200)).open()

    def logout(self, i):
        self.manager.app.username, self.manager.app.is_admin = "", False
        self.manager.current = 'login'
        self.show_popup("Logged Out", "You have been successfully logged out.")

class UserLedgerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_filters = {}
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        layout.add_widget(StyledLabel(text="My Ledger / History", font_size='20sp', size_hint_y=None, height=dp(40), halign='center'))
        layout.add_widget(StyledButton(text="Filter Ledger", on_press=self.open_filter_popup, background_color=(0.1, 0.7, 0.6, 1)))
        
        ledger_header = HeaderRow()
        ledger_header.width = dp(1250)
        ledger_header.add_widget(StyledLabel(text="Edit Action", size_hint_x=None, width=dp(120)))
        layout.add_widget(ledger_header)
        
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True, bar_width=dp(10))
        self.grid = GridLayout(cols=1, spacing=dp(10), size_hint=(None, None), width=dp(1250))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll_view.add_widget(self.grid)
        layout.add_widget(scroll_view)
        
        layout.add_widget(StyledButton(text="Back to Daily Entry", on_press=lambda x: setattr(self.manager, 'current', 'main'), background_color=(0.5,0.5,0.5,1)))
        self.add_widget(layout)
        
    def on_pre_enter(self, *a): self.apply_filters()
    def open_filter_popup(self, *a): FilterPopup(ledger_screen_ref=self).open()
    
    def apply_filters(self, date=None, party=None, bill=None):
        self._last_filters = {'date': date, 'party': party, 'bill': bill}
        self.grid.clear_widgets()
        app = App.get_running_app()
        current_user = app.username
        all_data = load_json(DATA_FILE, [])
        user_data = [e for e in all_data if isinstance(e, dict) and e.get('user') == current_user]
        
        if date: user_data = [e for e in user_data if e.get('date') == date]
        if party: user_data = [e for e in user_data if party.lower() in e.get('party', '').lower()]
        if bill: user_data = [e for e in user_data if bill == e.get('bill', '')]
        
        user_data.sort(key=lambda x: (x.get('date', ''), x.get('bill','')), reverse=True)
        
        if not user_data:
            self.grid.add_widget(StyledLabel(text="No entries found for these filters.", height=dp(50), size_hint=(None, None), width=dp(1150)))
        else:
            for entry in user_data:
                self.grid.add_widget(LedgerDataRow(entry, self))

    def open_edit_popup(self, d):
        popup = EditDsrPopup(entry_data=d, save_callback=self.save_edited_entry)
        popup.open()

    def save_edited_entry(self, o, u):
        all_data = load_json(DATA_FILE, [])
        try:
            index = all_data.index(o)
            all_data[index] = u
            save_json(DATA_FILE, all_data)
            # Use the consistent popup method from AdminPanel
            self.manager.get_screen('admin').show_popup("Success", "Entry updated successfully.")
            self.apply_filters(**self._last_filters)
        except ValueError:
            self.manager.get_screen('admin').show_popup("Error", "Could not find original entry.")
        
# --- App Class ---
class BusinessApp(App):
    def build(self):
        self.username, self.is_admin = "", False
        self.sm = ScreenManager()
        self.sm.app = self  # Make app instance accessible from screens
        
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(AdminPanel(name="admin"))
        self.sm.add_widget(UserManagementPanel(name="user_management"))
        self.sm.add_widget(UserLedgerScreen(name="user_ledger"))
        
        return self.sm

    def on_start(self):
        # Request permissions on start
        if platform == 'android':
            try:
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except Exception as e:
                print(f"Could not request permissions: {e}")
        
        # Ensure the admin user exists in the user file
        users_data = load_json(USERS_FILE, {})
        if ADMIN_USER not in users_data:
            users_data[ADMIN_USER] = hash_password(ADMIN_PASS)
            save_json(USERS_FILE, users_data)
            print(f"Default admin user '{ADMIN_USER}' created/verified in {USERS_FILE}.")

if __name__ == '__main__':
    BusinessApp().run()
# Triggering GitHub Action
