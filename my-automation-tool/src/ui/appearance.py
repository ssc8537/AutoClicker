"""可恢复的主题与界面布局设置。"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from src.utils.app_paths import config_root


CLASSIC_THEME = "classic_pink"
SAKURA_THEME = "sakura_garden"
CLASSIC_LAYOUT = "classic_tabs"
GALLERY_LAYOUT = "gallery_sidebar"

THEME_OPTIONS = (
    ("经典粉红", CLASSIC_THEME),
    ("樱空花园", SAKURA_THEME),
)
LAYOUT_OPTIONS = (
    ("经典顶部标签", CLASSIC_LAYOUT),
    ("画册侧边导航", GALLERY_LAYOUT),
)


@dataclass(frozen=True)
class AppearanceSettings:
    theme: str = CLASSIC_THEME
    layout: str = CLASSIC_LAYOUT


class AppearanceSettingsStore:
    """与 OSD、提示音共用 settings.json，并原子合并保存。"""

    def __init__(self, path: Path | None = None):
        self.path = path or (config_root() / "settings.json")

    def load(self) -> AppearanceSettings:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            loaded = {}
        if not isinstance(loaded, dict):
            loaded = {}
        theme = loaded.get("ui_theme", CLASSIC_THEME)
        layout = loaded.get("ui_layout", CLASSIC_LAYOUT)
        if theme not in {value for _, value in THEME_OPTIONS}:
            theme = CLASSIC_THEME
        if layout not in {value for _, value in LAYOUT_OPTIONS}:
            layout = CLASSIC_LAYOUT
        return AppearanceSettings(theme=theme, layout=layout)

    def save(self, settings: AppearanceSettings) -> None:
        data: dict[str, object] = {}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
        data["ui_theme"] = settings.theme
        data["ui_layout"] = settings.layout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", dir=self.path.parent, text=True
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(data, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
            os.replace(temporary_name, self.path)
        finally:
            if temporary_name is not None and Path(temporary_name).exists():
                Path(temporary_name).unlink(missing_ok=True)


CLASSIC_STYLESHEET = """
    QMainWindow, QWidget { background: #FCF7FA; color: #6E4055; font-family: "Microsoft YaHei UI", "Microsoft YaHei"; font-size: 12px; }
    QWidget#app_surface { border: 1px solid #D9A56C; border-radius: 2px; }
    QWidget#window_title_bar { background: #F8F0F4; border: 1px solid #E1C7A3; border-bottom: 1px solid #D9A56C; }
    QLabel#window_title_label { color: #6E4055; font-size: 15px; font-weight: 600; letter-spacing: 0.3px; }
    QToolButton#window_hide_button, QToolButton#window_minimize_button, QToolButton#window_close_button { background: #FCF7FA; border: 1px solid #D8D0D6; border-radius: 13px; color: #6E4055; font-weight: 600; }
    QToolButton#window_close_button { color: #9B536F; border-color: #C984A1; }
    QToolButton#window_hide_button:hover, QToolButton#window_minimize_button:hover { background: #F1E2E9; border-color: #C984A1; }
    QToolButton#window_close_button:hover { background: #C984A1; color: #FFFFFF; }
    QWidget#vertical_resize_handle, QWidget[objectName^="window_resize_"] { background: #F8F0F4; }
    QTabWidget::pane { background: #FCF7FA; border: 1px solid #E1C7A3; border-top: none; }
    QTabBar::tab { background: #F5EAF0; min-width: 150px; height: 40px; padding: 0; color: #6E4055; font-size: 16px; font-weight: 600; border-right: 1px solid #E4D9DF; }
    QTabBar::tab:hover { background: #F0E0E8; color: #6E4055; }
    QTabBar::tab:selected { background: #FCF7FA; color: #9B536F; border-top: 2px solid #C984A1; }
    QWidget#side_panel { background: #F8F0F4; border: 1px solid #E1C7A3; border-radius: 10px; }
    QLabel#gallery_avatar { background: transparent; border: none; }
    QLabel#gallery_title { background: transparent; color: #9B536F; font-size: 13px; font-weight: 700; }
    QListWidget#side_navigation { background: transparent; border: none; padding: 2px; outline: none; }
    QListWidget#side_navigation::item { color: #6E4055; min-height: 44px; border-radius: 7px; padding: 0; font-size: 14px; font-weight: 600; }
    QListWidget#side_navigation::item:hover { background: #F1E2E9; }
    QListWidget#side_navigation::item:selected { background: #EAF7FD; color: #9B536F; border-left: 3px solid #C984A1; }
    QGroupBox { background: #FFFFFF; border: 1px solid #E1C7A3; border-radius: 6px; margin-top: 11px; padding: 11px 8px 8px; font-weight: 600; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #6E4055; background: #FFFFFF; }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #FFFFFF; border: 1px solid #D8D0D6; border-radius: 4px; padding: 4px; min-height: 22px; selection-background-color: #C984A1; selection-color: #FFFFFF; }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #C984A1; background: #FFFDFE; }
    QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 20px; background: #F8F0F4; border-left: 1px solid #D8D0D6; border-bottom: 1px solid #D8D0D6; }
    QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 20px; background: #F8F0F4; border-left: 1px solid #D8D0D6; }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover { background: #EFDDE6; }
    QComboBox::drop-down { border: none; width: 20px; } QComboBox QAbstractItemView { background: #FFFFFF; border: 1px solid #D8D0D6; selection-background-color: #F1E2E9; selection-color: #6E4055; }
    QTableWidget { background: #FFFFFF; alternate-background-color: #FCF7FA; border: 1px solid #D8D0D6; gridline-color: #EEE5E9; selection-background-color: #EAF7FD; }
    QTableWidget::item:hover, QTableWidget::item:selected { background: #EAF7FD; }
    QHeaderView::section { background: #F8F0F4; border: none; border-bottom: 1px solid #D8D0D6; padding: 6px; color: #6E4055; font-weight: 600; }
    QPushButton { background: #FAF3F6; border: 1px solid #C984A1; border-radius: 4px; min-height: 26px; padding: 4px 10px; color: #6E4055; font-weight: 600; }
    QPushButton:hover:!disabled { background: #EFDDE6; border-color: #9B536F; } QPushButton:pressed:!disabled { background: #D9A9BD; color: #FFFFFF; }
    QPushButton:disabled, QCheckBox:disabled, QComboBox:disabled, QLineEdit:disabled { color: #9A858F; background: #F3EDF0; border-color: #E1D8DD; }
    QScrollArea { border: none; background: #FCF7FA; } QScrollBar:vertical { background: #F3EDF0; width: 8px; margin: 2px; } QScrollBar::handle:vertical { background: #CDB7C1; border-radius: 4px; min-height: 24px; } QScrollBar::handle:vertical:hover { background: #C984A1; }
"""


SAKURA_STYLESHEET = """
    QMainWindow, QWidget { background: #F7FBFF; color: #465468; font-family: "Microsoft YaHei UI", "Microsoft YaHei"; font-size: 13px; }
    QWidget#app_surface { border: 1px solid #B9DDE9; border-radius: 10px; }
    QWidget#window_title_bar { background: #FDF7FA; border: 1px solid #EBC9D5; border-bottom: 1px solid #B9DDE9; }
    QLabel#window_title_label { color: #536477; font-size: 16px; font-weight: 700; letter-spacing: 0.5px; }
    QToolButton#window_hide_button, QToolButton#window_minimize_button, QToolButton#window_close_button { background: #FFFFFF; border: 1px solid #D5E7EE; border-radius: 13px; color: #607286; font-weight: 700; }
    QToolButton#window_close_button { color: #B8657D; border-color: #F0B4C5; }
    QToolButton#window_hide_button:hover, QToolButton#window_minimize_button:hover { background: #E9F7FC; border-color: #8CCFE8; }
    QToolButton#window_close_button:hover { background: #F3A8BE; color: #FFFFFF; }
    QWidget#vertical_resize_handle, QWidget[objectName^="window_resize_"] { background: #F1F9FC; }
    QTabWidget::pane { background: #F7FBFF; border: 1px solid #D5E7EE; border-top: none; }
    QTabBar::tab { background: #EFF8FB; min-width: 150px; height: 42px; padding: 0; color: #607286; font-size: 16px; font-weight: 700; border-right: 1px solid #D5E7EE; }
    QTabBar::tab:hover { background: #E4F5FB; color: #465468; }
    QTabBar::tab:selected { background: #FFFFFF; color: #B75F7A; border-top: 3px solid #F3A8BE; }
    QWidget#side_panel { background: #FDF7FA; border: 1px solid #EBC9D5; border-radius: 12px; }
    QLabel#gallery_avatar { background: transparent; border: none; }
    QLabel#gallery_title { background: transparent; color: #A84F6D; font-size: 13px; font-weight: 700; }
    QListWidget#side_navigation { background: transparent; border: none; padding: 2px; outline: none; }
    QListWidget#side_navigation::item { color: #607286; min-height: 46px; border-radius: 9px; padding: 0; font-size: 14px; font-weight: 700; }
    QListWidget#side_navigation::item:hover { background: #EAF7FB; }
    QListWidget#side_navigation::item:selected { background: #DFF4FF; color: #A84F6D; border-left: 4px solid #F3A8BE; }
    QGroupBox { background: #FFFFFF; border: 1px solid #D5E7EE; border-radius: 11px; margin-top: 13px; padding: 14px 11px 11px; font-weight: 700; }
    QGroupBox::title { subcontrol-origin: margin; left: 13px; padding: 0 7px; color: #536477; background: #FFFFFF; }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #FFFFFF; border: 1px solid #CFE1E8; border-radius: 8px; padding: 6px 8px; min-height: 24px; selection-background-color: #BDE9F7; selection-color: #465468; }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 2px solid #8CCFE8; background: #FFFFFF; }
    QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 22px; background: #EEF8FB; border-left: 1px solid #D5E7EE; border-bottom: 1px solid #D5E7EE; }
    QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; background: #FDF5F8; border-left: 1px solid #E9D7DE; }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover { background: #DDF3F9; }
    QComboBox::drop-down { border: none; width: 24px; } QComboBox QAbstractItemView { background: #FFFFFF; border: 1px solid #D5E7EE; selection-background-color: #DFF4FF; selection-color: #465468; }
    QTableWidget { background: #FFFFFF; alternate-background-color: #FAFDFF; border: 1px solid #D5E7EE; border-radius: 8px; gridline-color: #E8F1F4; selection-background-color: #DFF4FF; }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:hover, QTableWidget::item:selected { background: #DFF4FF; }
    QHeaderView::section { background: #EEF8FB; border: none; border-bottom: 1px solid #CFE1E8; padding: 8px; color: #536477; font-weight: 700; }
    QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #FFF5F8, stop:1 #F1FAFC); border: 1px solid #E5B8C7; border-radius: 8px; min-height: 30px; padding: 5px 13px; color: #536477; font-weight: 700; }
    QPushButton:hover:!disabled { background: #E4F5FB; border-color: #8CCFE8; } QPushButton:pressed:!disabled { background: #BDE9F7; color: #465468; }
    QPushButton:disabled, QCheckBox:disabled, QComboBox:disabled, QLineEdit:disabled { color: #96A4B1; background: #F1F5F7; border-color: #DFE8EC; }
    QLabel#appearance_description { color: #718096; background: #F1FAFC; border: 1px solid #D7EDF4; border-radius: 8px; padding: 9px; }
    QScrollArea { border: none; background: #F7FBFF; } QScrollBar:vertical { background: #EDF6F9; width: 9px; margin: 2px; } QScrollBar::handle:vertical { background: #A8DEC5; border-radius: 4px; min-height: 26px; } QScrollBar::handle:vertical:hover { background: #8CCFE8; }
"""


def stylesheet_for(theme: str) -> str:
    return SAKURA_STYLESHEET if theme == SAKURA_THEME else CLASSIC_STYLESHEET
