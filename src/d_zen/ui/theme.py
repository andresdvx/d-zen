"""Tema oscuro con acentos púrpura."""
from pathlib import Path

ARROW_URL = (Path(__file__).parent / "arrow_down.png").as_posix()

BG = "#0e0a18"
PANEL = "#171126"
PANEL_ALT = "#201734"
BORDER = "#33264f"
TEXT = "#ece7f8"
MUTED = "#9a8fb8"
ACCENT = "#8b5cf6"
ACCENT_HOVER = "#a47bff"
ACCENT_PRESSED = "#7240e0"
SUCCESS = "#34d399"
DANGER = "#f87171"

FONT_FAMILY = '"Segoe UI Variable Display", "Segoe UI", "Inter", "SF Pro Display", "Helvetica Neue", sans-serif'

STYLESHEET = f"""
* {{ font-family: {FONT_FAMILY}; font-size: 11pt; color: {TEXT}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QLabel {{ background: transparent; }}

QLabel#brand {{ font-size: 26pt; font-weight: 800; letter-spacing: 6px; color: {TEXT}; }}
QLabel#tagline {{ color: {MUTED}; font-size: 10pt; letter-spacing: 1px; }}
QLabel#section {{ color: {MUTED}; font-size: 9pt; font-weight: 700; letter-spacing: 2px; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#videoTitle {{ font-size: 13pt; font-weight: 600; }}
QLabel#thumb {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 12px; color: {MUTED}; }}
QLabel#feedback {{ color: {MUTED}; }}
QLabel#feedback[kind="error"] {{ color: {DANGER}; }}
QLabel#feedback[kind="ok"] {{ color: {SUCCESS}; }}

QFrame#card {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; }}
QFrame#card QLabel {{ background: transparent; }}
QFrame#jobItem {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#jobItem[state="running"] {{ border: 1px solid {ACCENT}; }}
QFrame#jobItem[state="error"] {{ border: 1px solid {DANGER}; }}

QLineEdit, QComboBox {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 9px 12px; selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:read-only {{ color: {MUTED}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: url("{ARROW_URL}"); width: 12px; height: 8px; margin-right: 10px; }}
QComboBox QAbstractItemView {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; selection-background-color: {ACCENT};
    outline: none; padding: 4px;
}}
QComboBox:disabled, QLineEdit:disabled {{ color: #5d5478; }}

QPushButton {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 9px 18px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #5d5478; background: {PANEL}; }}
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT}, stop:1 #c026d3);
    border: none; color: white; padding: 11px 22px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT_HOVER}, stop:1 #d946ef);
}}
QPushButton#primary:pressed {{ background: {ACCENT_PRESSED}; }}
QPushButton#primary:disabled {{ background: {PANEL_ALT}; color: #5d5478; }}
QPushButton#seg {{ border-radius: 10px; padding: 8px 26px; background: {BG}; }}
QPushButton#seg:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton#icon {{ padding: 4px 10px; min-width: 18px; border-radius: 8px; background: transparent; }}
QPushButton#icon:hover {{ background: {BORDER}; }}
QPushButton#link {{ border: none; background: transparent; color: {MUTED}; padding: 4px 8px; }}
QPushButton#link:hover {{ color: {TEXT}; }}

QProgressBar {{ background: {BG}; border: none; border-radius: 4px; max-height: 8px; min-height: 8px; text-align: center; }}
QProgressBar::chunk {{
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 #d946ef);
}}
QProgressBar[state="done"]::chunk {{ background: {SUCCESS}; }}
QProgressBar[state="error"]::chunk {{ background: {DANGER}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QMenuBar {{ background: {BG}; }}
QMenuBar::item:selected {{ background: {PANEL_ALT}; }}
QMenu {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; padding: 6px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QToolTip {{ background: {PANEL_ALT}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}
QMessageBox, QDialog {{ background: {PANEL}; }}
"""
