import configparser
import os
from constants import LANGUAGES, COLOR_SCHEMES, MIN_GRID_SIZE, MAX_GRID_SIZE, SETTINGS_FILE, TEMPLATE_ALPHA_DEFAULT, \
    TEMPLATE_SCALE_DEFAULT, TEMPLATE_SCALE_MIN, TEMPLATE_SCALE_MAX
from utils import get_app_path


class Settings:
    def __init__(self):
        self._language = "en"
        self._color_scheme_index = 0
        self._isometric = True
        self._show_coordinates = True
        self._building_code = "TEMP"
        self._grid_width = 15
        self._grid_height = 15
        self._template_path = ""
        self._template_alpha = TEMPLATE_ALPHA_DEFAULT
        self._template_scale = TEMPLATE_SCALE_DEFAULT
        self._template_offset = [0, 0]
        self._show_template = True
        self._fix_template_scale = False

        self._observers = {}
        self.load()

    def _get_settings_path(self):
        base = get_app_path()
        return os.path.join(base, SETTINGS_FILE)

    # --- Подписка ---
    def subscribe(self, key, callback):
        """Подписаться на изменение параметра key (или 'grid' для всей сетки)."""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)

    def unsubscribe(self, key, callback):
        if key in self._observers:
            self._observers[key].remove(callback)

    def _notify(self, key):
        if key in self._observers:
            for cb in self._observers[key]:
                cb()

    # --- Свойства с уведомлениями ---
    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        if value in LANGUAGES and self._language != value:
            self._language = value
            self._notify("language")
            self.save()

    @property
    def color_scheme_index(self):
        return self._color_scheme_index

    @color_scheme_index.setter
    def color_scheme_index(self, value):
        if 0 <= value < len(COLOR_SCHEMES) and self._color_scheme_index != value:
            self._color_scheme_index = value
            self._notify("color_scheme")
            self.save()

    @property
    def isometric(self):
        return self._isometric

    @isometric.setter
    def isometric(self, value):
        if self._isometric != value:
            self._isometric = value
            self._notify("isometric")
            self.save()

    @property
    def show_coordinates(self):
        return self._show_coordinates

    @show_coordinates.setter
    def show_coordinates(self, value):
        if self._show_coordinates != value:
            self._show_coordinates = value
            self._notify("show_coordinates")
            self.save()

    @property
    def building_code(self):
        return self._building_code

    @building_code.setter
    def building_code(self, value):
        if self._building_code != value:
            self._building_code = value
            self._notify("building_code")
            self.save()

    @property
    def grid_width(self):
        return self._grid_width

    @grid_width.setter
    def grid_width(self, value):
        if MIN_GRID_SIZE <= value <= MAX_GRID_SIZE and self._grid_width != value:
            self._grid_width = value
            self._notify("grid")  # сетка изменилась
            self.save()

    @property
    def grid_height(self):
        return self._grid_height

    @grid_height.setter
    def grid_height(self, value):
        if MIN_GRID_SIZE <= value <= MAX_GRID_SIZE and self._grid_height != value:
            self._grid_height = value
            self._notify("grid")
            self.save()

    @property
    def template_path(self):
        return self._template_path

    @template_path.setter
    def template_path(self, value):
        if self._template_path != value:
            self._template_path = value
            self._notify("template")
            self.save()

    @property
    def template_alpha(self):
        return self._template_alpha

    @template_alpha.setter
    def template_alpha(self, value):
        if self._template_alpha != value:
            self._template_alpha = max(0, min(255, int(value)))
            self._notify("template")
            self.save()

    @property
    def template_scale(self):
        return self._template_scale

    @template_scale.setter
    def template_scale(self, value):
        if self._template_scale != value:
            self._template_scale = max(TEMPLATE_SCALE_MIN, min(TEMPLATE_SCALE_MAX, value))
            self._notify("template")
            self.save()

    @property
    def template_offset(self):
        return self._template_offset

    @template_offset.setter
    def template_offset(self, value):
        if self._template_offset != value:
            self._template_offset = value[:]  # копия
            self._notify("template")
            self.save()

    @property
    def show_template(self):
        return self._show_template

    @show_template.setter
    def show_template(self, value):
        if self._show_template != value:
            self._show_template = value
            self._notify("template")
            self.save()

    @property
    def fix_template_scale(self):
        return self._fix_template_scale

    @fix_template_scale.setter
    def fix_template_scale(self, value):
        if self._fix_template_scale != value:
            self._fix_template_scale = value
            self._notify("template")
            self.save()

    # --- Загрузка/сохранение ---
    def load(self):
        path = self._get_settings_path()
        if not os.path.exists(path):
            return
        try:
            config = configparser.ConfigParser()
            config.read(path)
            if 'Settings' not in config:
                return
            s = config['Settings']
            if 'language' in s:
                lang = s.get('language')
                if lang in LANGUAGES:
                    self._language = lang
            if 'color_scheme' in s:
                idx = int(s.get('color_scheme'))
                if 0 <= idx < len(COLOR_SCHEMES):
                    self._color_scheme_index = idx
            if 'isometric' in s:
                self._isometric = s.getboolean('isometric')
            if 'show_coords' in s:
                self._show_coordinates = s.getboolean('show_coords')
            if 'building_code' in s:
                self._building_code = s.get('building_code')
            if 'grid_width' in s:
                w = int(s.get('grid_width'))
                if MIN_GRID_SIZE <= w <= MAX_GRID_SIZE:
                    self._grid_width = w
            if 'grid_height' in s:
                h = int(s.get('grid_height'))
                if MIN_GRID_SIZE <= h <= MAX_GRID_SIZE:
                    self._grid_height = h
            if 'Template' in config:
                t = config['Template']
                if 'path' in t:
                    self._template_path = t.get('path')
                if 'alpha' in t:
                    self._template_alpha = int(t.get('alpha'))
                if 'scale' in t:
                    self._template_scale = float(t.get('scale'))
                if 'offset_x' in t and 'offset_y' in t:
                    self._template_offset = [float(t.get('offset_x')), float(t.get('offset_y'))]
                if 'show' in t:
                    self._show_template = t.getboolean('show')
                if 'fix_scale' in t:
                    self._fix_template_scale = t.getboolean('fix_scale')
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'language': self._language,
            'color_scheme': str(self._color_scheme_index),
            'isometric': str(self._isometric),
            'show_coords': str(self._show_coordinates),
            'building_code': self._building_code,
            'grid_width': str(self._grid_width),
            'grid_height': str(self._grid_height)
        }
        config['Template'] = {
            'path': self._template_path,
            'alpha': str(self._template_alpha),
            'scale': str(self._template_scale),
            'offset_x': str(self._template_offset[0]),
            'offset_y': str(self._template_offset[1]),
            'show': str(self._show_template),
            'fix_scale': str(self._fix_template_scale)
        }
        path = self._get_settings_path()
        try:
            with open(path, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # --- Специальное уведомление для сетки (можно вызывать вручную) ---
    def notify_grid_changed(self):
        self._notify("grid")