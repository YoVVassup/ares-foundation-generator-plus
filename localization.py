import os
import configparser
from constants import LANGUAGES
from utils import get_app_path

class Localization:
    def __init__(self, language="en"):
        self.languages = {}
        self.load_all_languages()
        self.language = language if language in self.languages else "en"

    def load_all_languages(self):
        base = get_app_path()   # папка с .exe
        for lang_code in LANGUAGES:
            filename = os.path.join(base, f"language_{lang_code}.ini")
            strings = {}
            if os.path.exists(filename):
                config = configparser.ConfigParser()
                config.read(filename, encoding='utf-8')
                if 'Strings' in config:
                    for key, value in config['Strings'].items():
                        strings[key] = value
            else:
                strings = self.get_default_strings()
            self.languages[lang_code] = strings
        if "en" not in self.languages:
            self.languages["en"] = self.get_default_strings()

    def get_default_strings(self):
        return {
            "building_code": "Building Code:",
            "grid_size": "Grid Size:",
            "apply_size": "Apply Size",
            "generate_outline": "Generate Outline",
            "clear": "Clear (C)",
            "export_ini": "Export INI (Ctrl+E)",
            "save_image": "Save Image (Ctrl+Shift+S)",
            "load_ini": "Load INI (L)",
            "undo": "Undo (Ctrl+Z)",
            "redo": "Redo (Ctrl+Y)",
            "fit_to_screen": "Fit to Screen (F)",
            "toggle_projection": "Toggle Projection (P)",
            "toggle_coords": "Toggle Coords (O)",
            "reset_view": "Reset View (R)",
            "choose_color_scheme": "Choose Color Scheme (Ctrl+K)",
            "choose_language": "Choose Language (Ctrl+Alt+L)",
            "zoom": "Zoom",
            "projection": "Projection",
            "coords": "Coords",
            "loaded": "Loaded",
            "mouse": "Mouse",
            "outline_mode": "OUTLINE MODE",
            "controls": "Hotkeys: F1",
            "warning_not_closed": "WARNING: Foundation outline is not closed!",
            "invalid_size": "Invalid Size",
            "size_range": "Grid size must be between {min}x{min} and {max}x{max}.",
            "outline_warning": "Outline Warning",
            "outline_not_closed": "Foundation outline is not closed!",
            "export_successful": "Export Successful",
            "exported_to": "Exported to:\n{path}",
            "export_error": "Export Error",
            "could_not_save": "Could not save file:\n{error}",
            "load_error": "Load Error",
            "no_sections": "No sections found in INI file.",
            "missing_foundation_xy": "INI file missing Foundation.X or Foundation.Y.",
            "invalid_foundation_xy": "Foundation.X or Foundation.Y are not valid integers.",
            "load_warning": "Load Warning",
            "coords_skipped": "{count} coordinates were outside the grid and have been skipped.",
            "outline_not_closed_loaded": "The loaded outline is not closed. You may need to adjust it manually.",
            "unexpected_error": "Unexpected error while loading file:\n{error}",
            "directory_error": "Directory Error",
            "cannot_create_export_dir": "Cannot create export directory:\n{error}",
            "images_saved": "Images Saved",
            "orthogonal": "Orthogonal",
            "isometric": "Isometric",
            "choose_color_scheme_title": "Choose Color Scheme",
            "choose_language_title": "Choose Language",
            "filled": "Filled",
            "outline": "Outline",
            "bbox": "BBox",
            "aspect": "Aspect",
            "on": "ON",
            "off": "OFF",
            "help_title": "Keyboard Shortcuts",
            "help_close": "Press Esc or F1 to close",
            "lmb_desc": "Add cell",
            "rmb_desc": "Remove cell",
            "mmb_desc": "Pan view",
            "ctrl_lmb_desc": "Add outline cell",
            "ctrl_rmb_desc": "Remove outline cell",
            "c_desc": "Clear grid",
            "l_desc": "Load INI",
            "p_desc": "Toggle projection",
            "o_desc": "Toggle coordinates",
            "r_desc": "Reset view",
            "z_desc": "Reset zoom",
            "f_desc": "Fit to screen",
            "ctrl_z_desc": "Undo",
            "ctrl_y_desc": "Redo",
            "f1_desc": "Show this help",
            "esc_desc": "Close help",
            "load_template": "Load Template (Ctrl+T)",
            "template_alpha": "Opacity",
            "template_scale": "Scale",
            "template_fit": "Fit to Grid",
            "template_reset": "Reset Template",
            "template_hide": "Hide Template",
            "template_show": "Show Template",
            "fix_template_scale_on": "Fix Template Scale ON",
            "fix_template_scale_off": "Fix Template Scale OFF",
            "unsaved_changes_title": "Unsaved Changes",
            "unsaved_changes_message": "You have unsaved changes. Do you want to save before exiting?",
            "yes": "Yes",
            "no": "No",
            "cancel": "Cancel",
            "template_zoom_desc": "Zoom template (Ctrl+Wheel)",
            "template_pan_desc": "Pan template (Ctrl+MMB)",
            "generate_outline_key_desc": "Generate outline (G)",
            "apply_size_key_desc": "Apply size (Ctrl+Enter)",
            "load_template_key_desc": "Load template (Ctrl+T)",
            "fit_template_key_desc": "Fit template to grid (Ctrl+Shift+F)",
            "reset_template_key_desc": "Reset template (Ctrl+Shift+R)",
            "toggle_template_key_desc": "Toggle template visibility (Ctrl+Shift+H)",
            "fix_scale_key_desc": "Toggle fix template scale (Ctrl+Shift+L)",
            "export_ini_key_desc": "Export INI (Ctrl+E)",
            "save_image_key_desc": "Save image (Ctrl+Shift+S)",
            "color_scheme_key_desc": "Choose color scheme",
            "language_key_desc": "Choose language",
        }

    def get(self, key, **kwargs):
        strings = self.languages.get(self.language, self.languages["en"])
        text = strings.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except:
                pass
        return text

    def get_language_names(self):
        return LANGUAGES