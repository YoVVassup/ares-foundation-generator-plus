import pygame
import os
from utils import get_resource_path

# -------------------- Константы --------------------
MIN_SCREEN_WIDTH = 1200
MIN_SCREEN_HEIGHT = 600
GRID_SIZE = 24
UI_TOP_HEIGHT = 120
UI_BOTTOM_HEIGHT = 150

ISO_W = GRID_SIZE / 1.5
ISO_H = GRID_SIZE / 3

MIN_GRID_SIZE = 5
MAX_GRID_SIZE = 50

EXPORT_PADDING = 50
ISO_CENTER_OFFSET_Y = 50
BORDER_RADIUS = 5
TOOLTIP_DELAY = 30

TEMPLATE_ALPHA_MIN = 0
TEMPLATE_ALPHA_MAX = 255
TEMPLATE_ALPHA_DEFAULT = 128
TEMPLATE_SCALE_MIN = 0.1
TEMPLATE_SCALE_MAX = 5.0
TEMPLATE_SCALE_DEFAULT = 1.0

EXPORT_DIR = "foundations_export"
SETTINGS_FILE = "settings.ini"

# Доступные языки
LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "zh_cn": "简体中文",
    "zh_tw": "繁體中文"
}

# Цветовые схемы
COLOR_SCHEMES = [
    {   # Default Dark
        'name': 'Default Dark',
        'background': (30, 34, 42), 'grid': (70, 80, 100), 'cell': (96, 166, 224),
        'outline': (230, 173, 67), 'button': (82, 143, 193), 'text': (230, 230, 230),
        'hover': (110, 190, 255), 'axis': (255, 255, 200), 'warning': (220, 60, 60),
        'tooltip_bg': (50, 50, 60), 'tooltip_text': (255, 255, 200),
        'slider_bg': (60, 60, 70), 'slider_handle': (150, 150, 160),
    },
    {   # Slate Gray
        'name': 'Slate Gray',
        'background': (35, 35, 40), 'grid': (80, 80, 90), 'cell': (70, 130, 180),
        'outline': (200, 140, 60), 'button': (60, 60, 70), 'text': (220, 220, 220),
        'hover': (100, 160, 210), 'axis': (240, 240, 180), 'warning': (200, 50, 50),
        'tooltip_bg': (45, 45, 50), 'tooltip_text': (210, 210, 210),
        'slider_bg': (55, 55, 65), 'slider_handle': (130, 130, 140),
    },
    {   # Green Hacker
        'name': 'Green Hacker',
        'background': (0, 20, 0), 'grid': (0, 80, 0), 'cell': (0, 180, 0),
        'outline': (255, 165, 0), 'button': (0, 60, 0), 'text': (0, 200, 0),
        'hover': (0, 255, 0), 'axis': (255, 255, 200), 'warning': (255, 0, 0),
        'tooltip_bg': (0, 40, 0), 'tooltip_text': (0, 255, 0),
        'slider_bg': (0, 60, 0), 'slider_handle': (0, 150, 0),
    },
    {   # Warm Sunset
        'name': 'Warm Sunset',
        'background': (60, 30, 30), 'grid': (120, 60, 60), 'cell': (255, 120, 80),
        'outline': (255, 200, 0), 'button': (100, 50, 50), 'text': (255, 220, 180),
        'hover': (255, 150, 100), 'axis': (255, 255, 200), 'warning': (255, 50, 50),
        'tooltip_bg': (80, 40, 40), 'tooltip_text': (255, 200, 150),
        'slider_bg': (100, 50, 50), 'slider_handle': (150, 80, 60),
    },
    {   # Deep Ocean
        'name': 'Deep Ocean',
        'background': (10, 20, 50), 'grid': (30, 60, 100), 'cell': (100, 200, 255),
        'outline': (255, 105, 180), 'button': (20, 40, 80), 'text': (200, 220, 255),
        'hover': (150, 200, 255), 'axis': (255, 255, 200), 'warning': (255, 100, 100),
        'tooltip_bg': (20, 30, 60), 'tooltip_text': (200, 220, 255),
        'slider_bg': (30, 40, 80), 'slider_handle': (80, 120, 180),
    }
]

# Текущая цветовая схема (изначально 0)
COLORS = COLOR_SCHEMES[0].copy()

def load_font(size, bold=False):
    """Загружает шрифт (сначала Unifont.ttf, затем системный)."""
    font_path = get_resource_path("Unifont.ttf")   # изменено
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except:
            pass
    return pygame.font.SysFont('arial', size, bold=bold)