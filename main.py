import pygame
import numpy as np
import os
import configparser
from pygame.locals import *
from tkinter import Tk, filedialog, messagebox, simpledialog
import sys

from constants import *
from localization import Localization
from commands import CellCommand, GridSnapshotCommand
from grid import Grid
from renderer import Renderer
from ui import UIController, OptionDialog, ConfirmDialog
from settings import Settings
from utils import get_app_path, get_resource_path


# -------------------- NEW: Tkinter root with icon --------------------
root = Tk()
root.withdraw()
try:
    icon_path = get_resource_path("icon.ico")   # изменено
    root.iconbitmap(default=icon_path)
except Exception as e:
    print(f"Could not load tkinter icon: {e}")

class CasePreservingConfigParser(configparser.ConfigParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def optionxform(self, optionstr):
        return optionstr


class FoundationGenerator:
    def __init__(self, width, height):
        pygame.init()
        self.screen_width, self.screen_height = 1200, 800
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.RESIZABLE | pygame.DROPFILE
        )
        pygame.display.set_caption("Ares Foundation Generator +")

        # -------------------- NEW: Set pygame window icon --------------------
        try:
            icon_pygame = pygame.image.load(get_resource_path("icon.png"))  # изменено
            pygame.display.set_icon(icon_pygame)
        except Exception as e:
            print(f"Could not load pygame icon: {e}")

        self.settings = Settings()
        self.settings.grid_width = width
        self.settings.grid_height = height

        self.grid = Grid(self.settings.grid_width, self.settings.grid_height)

        self.view_offset = [0, 0]
        self.loaded_filename = ""

        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0

        self.dragging_camera = False
        self.dragging_grid = False
        self.drag_button = None
        self.drag_start_pos = (0, 0)
        self.drag_start_view = (0, 0)

        self.dragging_template = False
        self.drag_start_template_offset = [0, 0]

        self.mouse_cell = None

        self.undo_stack = []
        self.redo_stack = []
        self.in_command = False

        self.show_help = False

        self.font = load_font(16)
        self.title_font = load_font(28, bold=True)
        self.axis_font = load_font(7)
        self.iso_coord_font = load_font(7)
        self.warning_font = load_font(20, bold=True)
        self.ui_font = load_font(20)

        self.lang = Localization(self.settings.language)

        self.renderer = Renderer(self.grid, self.font, self.axis_font, self.iso_coord_font, self.warning_font)
        self.settings.subscribe("grid", self.renderer._update_iso_cache)

        self.template_image = None
        self.template_surface = None
        self.template_offset = self.settings.template_offset[:]
        self.template_scale = self.settings.template_scale
        self.template_alpha = self.settings.template_alpha
        self.show_template = self.settings.show_template

        self.unsaved_changes = False
        self.should_quit = False

        self.ui = UIController(
            font=self.font,
            ui_font=self.ui_font,
            on_apply_size=self.apply_size,
            on_generate_outline=self.generate_and_apply_outline,
            on_clear=self.clear_grid,
            on_export_ini=self.export_to_ini,
            on_save_image=self.save_as_image,
            on_load_ini=self.load_ini_file,
            on_toggle_projection=self.toggle_projection,
            on_toggle_coords=self.toggle_coords,
            on_reset_view=self.reset_view,
            on_fit_to_screen=self.fit_to_screen,
            on_reset_zoom=self.reset_zoom,
            on_undo=self.undo,
            on_redo=self.redo,
            on_zoom_changed=self.set_zoom,
            on_change_color_scheme=self.choose_color_scheme_dialog,
            on_change_language=self.choose_language_dialog,
            on_load_template=self.load_template_dialog,
            on_template_alpha_changed=self.set_template_alpha,
            on_template_scale_changed=self.set_template_scale,
            on_template_fit=self.fit_template_to_grid,
            on_template_reset=self.reset_template,
            on_toggle_template=self.toggle_template,
            on_toggle_fix_template_scale=lambda state: setattr(self.settings, 'fix_template_scale', state),
            lang=self.lang
        )
        self.ui.set_values(self.settings.building_code, self.settings.grid_width, self.settings.grid_height)
        self.ui.set_fix_scale_state(self.settings.fix_template_scale)
        self.ui.update_layout(self.screen_width, self.screen_height)

        self.settings.subscribe("language", self.on_language_changed)
        self.settings.subscribe("color_scheme", self.on_color_scheme_changed)

        self.dialog = None

        self.on_color_scheme_changed()

    # --- Обработчики событий настроек ---
    def on_language_changed(self):
        self.lang = Localization(self.settings.language)
        self.ui.update_language(self.lang)
        self.ui.set_fix_scale_state(self.settings.fix_template_scale)
        self.ui.update_layout(self.screen_width, self.screen_height)

    def on_color_scheme_changed(self):
        global COLORS
        COLORS.clear()
        COLORS.update(COLOR_SCHEMES[self.settings.color_scheme_index])

    # --- Методы для диалогов ---
    def choose_language_dialog(self):
        options = [(code, LANGUAGES[code]) for code in LANGUAGES]
        self.dialog = OptionDialog(
            title=self.lang.get("choose_language_title"),
            options=options,
            font=self.font,
            title_font=self.title_font,
            colors=COLORS,
            on_select=lambda code: setattr(self.settings, 'language', code)
        )

    def choose_color_scheme_dialog(self):
        options = [(str(i), scheme['name']) for i, scheme in enumerate(COLOR_SCHEMES)]
        self.dialog = OptionDialog(
            title=self.lang.get("choose_color_scheme_title"),
            options=options,
            font=self.font,
            title_font=self.title_font,
            colors=COLORS,
            on_select=lambda idx: setattr(self.settings, 'color_scheme_index', int(idx))
        )

    # --- Основной цикл ---
    def run(self):
        os.makedirs(EXPORT_DIR, exist_ok=True)
        clock = pygame.time.Clock()
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            clock.tick(60)
        pygame.quit()
        sys.exit()

    def _quit(self):
        return False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                if self.unsaved_changes:
                    self.should_quit = False
                    self.dialog = ConfirmDialog(
                        title=self.lang.get("unsaved_changes_title"),
                        message=self.lang.get("unsaved_changes_message"),
                        font=self.font,
                        title_font=self.title_font,
                        colors=COLORS,
                        on_yes=lambda: (self.export_to_ini(), setattr(self, 'unsaved_changes', False), setattr(self, 'should_quit', True)),
                        on_no=lambda: setattr(self, 'should_quit', True),
                        on_cancel=lambda: None,
                        lang=self.lang
                    )
                    return True
                else:
                    return False

            if event.type == VIDEORESIZE:
                self._handle_resize(event)

            if event.type == DROPFILE:
                file_path = event.file
                if file_path.lower().endswith('.ini'):
                    self.load_ini_file(file_path)
                continue

            if self.dialog:
                self.dialog.handle_event(event)
                if not self.dialog.active:
                    self.dialog = None
                    if self.should_quit:
                        return False
                continue

            self.ui.handle_events(event)
            self._handle_mouse_input(event)
            self._handle_keyboard_input(event)
        return True

    def load_ini_file(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("INI files", "*.ini"), ("All files", "*.*")])
            if not file_path:
                return

        try:
            config = CasePreservingConfigParser(
                delimiters=('=', ':'),
                comment_prefixes=('#', ';'),
                inline_comment_prefixes=('#', ';'),
                strict=False,
                empty_lines_in_values=False
            )
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)

            if not config.sections():
                messagebox.showerror(
                    self.lang.get("load_error"),
                    self.lang.get("no_sections")
                )
                return

            section = config.sections()[0]

            if not config.has_option(section, 'Foundation.X') or not config.has_option(section, 'Foundation.Y'):
                messagebox.showerror(
                    self.lang.get("load_error"),
                    self.lang.get("missing_foundation_xy")
                )
                return

            try:
                w = int(config.get(section, 'Foundation.X'))
                h = int(config.get(section, 'Foundation.Y'))
            except ValueError:
                messagebox.showerror(
                    self.lang.get("load_error"),
                    self.lang.get("invalid_foundation_xy")
                )
                return

            w = max(MIN_GRID_SIZE, min(w, MAX_GRID_SIZE))
            h = max(MIN_GRID_SIZE, min(h, MAX_GRID_SIZE))

            new_grid = Grid(w, h)
            skipped_coords = 0

            for key, value in config.items(section):
                key_lower = key.lower()
                if key_lower in ['foundation', 'foundation.x', 'foundation.y', 'foundationoutline.length']:
                    continue

                parts = [part.strip() for part in value.split(',')]
                if len(parts) != 2:
                    continue

                try:
                    x, y = map(int, parts)
                except ValueError:
                    continue

                if not (0 <= x < w and 0 <= y < h):
                    skipped_coords += 1
                    continue

                if key_lower.startswith('foundation.'):
                    new_grid.cells[y, x] = True
                elif key_lower.startswith('foundationoutline.'):
                    new_grid.outline[y, x] = True

            if skipped_coords > 0:
                messagebox.showwarning(
                    self.lang.get("load_warning"),
                    self.lang.get("coords_skipped", count=skipped_coords)
                )

            if not new_grid.is_outline_closed():
                messagebox.showwarning(
                    self.lang.get("outline_warning"),
                    self.lang.get("outline_not_closed_loaded")
                )

            old_cells = self.grid.cells.copy()
            old_outline = self.grid.outline.copy()
            old_generated = self.grid.generated_outline[:]

            self.grid = new_grid
            self.renderer.grid = new_grid
            self.settings.grid_width = w
            self.settings.grid_height = h
            self.settings.building_code = section

            new_cells = self.grid.cells.copy()
            new_outline = self.grid.outline.copy()
            new_generated = self.grid.generated_outline[:]
            cmd = GridSnapshotCommand(self.grid, old_cells, old_outline, old_generated,
                                      new_cells, new_outline, new_generated)
            self._push_command(cmd)

            self.ui.set_values(section, w, h)
            self.loaded_filename = os.path.basename(file_path)
            self.reset_view()
            self.settings.notify_grid_changed()
            self.unsaved_changes = False

        except Exception as e:
            messagebox.showerror(
                self.lang.get("load_error"),
                self.lang.get("unexpected_error", error=str(e))
            )

    def _handle_resize(self, event):
        w = max(event.w, MIN_SCREEN_WIDTH)
        h = max(event.h, MIN_SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        self.screen_width, self.screen_height = w, h
        self.ui.update_layout(w, h)

    def _handle_mouse_input(self, event):
        is_over_grid = UI_TOP_HEIGHT < pygame.mouse.get_pos()[1] < self.screen_height - UI_BOTTOM_HEIGHT

        if event.type == MOUSEMOTION:
            if is_over_grid:
                self.mouse_cell = self._get_cell_from_mouse(event.pos)
            else:
                self.mouse_cell = None

        if event.type == MOUSEWHEEL:
            mods = pygame.key.get_mods()
            # Масштабирование шаблона с Ctrl
            if mods & KMOD_CTRL and self.template_surface:
                # Масштабирование шаблона относительно курсора
                factor = 1.1 if event.y > 0 else 0.9
                mouse_x, mouse_y = pygame.mouse.get_pos()
                w_grid, h_grid = self.grid.width, self.grid.height
                cell_size = GRID_SIZE * self.zoom
                grid_pw = w_grid * cell_size
                start_x = (self.screen_width - grid_pw) // 2 + self.view_offset[0]
                start_y = UI_TOP_HEIGHT + 20 + self.view_offset[1]
                rel_x = mouse_x - start_x
                rel_y = mouse_y - start_y
                tx = (rel_x - self.template_offset[0] * self.zoom) / (self.template_scale * self.zoom)
                ty = (rel_y - self.template_offset[1] * self.zoom) / (self.template_scale * self.zoom)
                new_scale = self.template_scale * factor
                new_scale = max(TEMPLATE_SCALE_MIN, min(TEMPLATE_SCALE_MAX, new_scale))
                self.template_offset[0] = (rel_x - tx * new_scale * self.zoom) / self.zoom
                self.template_offset[1] = (rel_y - ty * new_scale * self.zoom) / self.zoom
                self.template_scale = new_scale
                self.settings.template_scale = new_scale
                self.settings.template_offset = self.template_offset[:]
                self.ui.scale_slider.set_val(new_scale)
                self.unsaved_changes = True
                return

            # Обычное масштабирование сетки
            old_zoom = self.zoom
            self.zoom += event.y * 0.1
            self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))

            if self.settings.fix_template_scale and self.template_surface:
                factor = self.zoom / old_zoom
                self.template_scale *= factor
                self.template_scale = max(TEMPLATE_SCALE_MIN, min(TEMPLATE_SCALE_MAX, self.template_scale))
                self.settings.template_scale = self.template_scale
                self.ui.scale_slider.set_val(self.template_scale)
                self.unsaved_changes = True

            if self.settings.isometric:
                mx, my = pygame.mouse.get_pos()
                iso_w = ISO_W * old_zoom
                iso_h = ISO_H * old_zoom
                center_x = self.screen_width // 2 + self.view_offset[0]
                center_y = self.screen_height // 2 - ISO_CENTER_OFFSET_Y * old_zoom + self.view_offset[1]

                rel_x = mx - center_x
                rel_y = my - center_y
                x = (rel_x / iso_w + rel_y / iso_h) / 2
                y = (rel_y / iso_h - rel_x / iso_w) / 2

                new_iso_w = ISO_W * self.zoom
                new_iso_h = ISO_H * self.zoom
                self.view_offset[0] = mx - self.screen_width // 2 - (x - y) * new_iso_w
                self.view_offset[1] = my - self.screen_height // 2 + ISO_CENTER_OFFSET_Y * self.zoom - (x + y) * new_iso_h
            else:
                mx, my = pygame.mouse.get_pos()
                w, h = self.grid.width, self.grid.height
                old_cell = GRID_SIZE * old_zoom
                new_cell = GRID_SIZE * self.zoom
                old_base_x = (self.screen_width - w * old_cell) // 2
                old_base_y = UI_TOP_HEIGHT + 20
                new_base_x = (self.screen_width - w * new_cell) // 2
                new_base_y = UI_TOP_HEIGHT + 20

                x = (mx - old_base_x - self.view_offset[0]) / old_cell
                y = (my - old_base_y - self.view_offset[1]) / old_cell

                self.view_offset[0] = mx - new_base_x - x * new_cell
                self.view_offset[1] = my - new_base_y - y * new_cell

            self.ui.zoom_slider.set_val(self.zoom)

        elif event.type == MOUSEBUTTONDOWN:
            mods = pygame.key.get_mods()
            if event.button == 2:
                if mods & KMOD_CTRL and self.template_surface:
                    self.dragging_template = True
                    self.drag_start_pos = event.pos
                    self.drag_start_template_offset = self.template_offset[:]
                else:
                    self.dragging_camera = True
                    self.drag_start_pos = event.pos
                    self.drag_start_view = self.view_offset[:]
            elif is_over_grid and (event.button == 1 or event.button == 3):
                self.dragging_grid = True
                self.drag_button = event.button
                self.handle_grid_click(event.pos, event.button)

        elif event.type == MOUSEBUTTONUP:
            self.dragging_camera = False
            self.dragging_grid = False
            self.dragging_template = False

        elif event.type == MOUSEMOTION:
            if self.dragging_camera:
                dx = event.pos[0] - self.drag_start_pos[0]
                dy = event.pos[1] - self.drag_start_pos[1]
                self.view_offset[0] = self.drag_start_view[0] + dx
                self.view_offset[1] = self.drag_start_view[1] + dy
            elif self.dragging_template:
                dx = event.pos[0] - self.drag_start_pos[0]
                dy = event.pos[1] - self.drag_start_pos[1]
                self.template_offset[0] = self.drag_start_template_offset[0] + dx / self.zoom
                self.template_offset[1] = self.drag_start_template_offset[1] + dy / self.zoom
                self.settings.template_offset = self.template_offset[:]
                self.unsaved_changes = True
            elif self.dragging_grid and is_over_grid:
                self.handle_grid_click(event.pos, self.drag_button)

    def _handle_keyboard_input(self, event):
        if event.type == KEYDOWN:
            if event.key == K_F1:
                self.toggle_help()
                return
            if event.key == K_ESCAPE and self.show_help:
                self.show_help = False
                return

            if any(ti.active for ti in self.ui.text_inputs):
                return
            mods = pygame.key.get_mods()

            # Одиночные клавиши
            if event.key == K_g:
                self.generate_and_apply_outline()
                return

            # Комбинации с Ctrl
            if mods & KMOD_CTRL:
                if event.key == K_t:
                    self.load_template_dialog()
                    return
                elif event.key == K_e:
                    self.export_to_ini()
                    return
                elif event.key == K_k:
                    self.choose_color_scheme_dialog()
                    return
                elif mods & KMOD_SHIFT:
                    if event.key == K_f:
                        self.fit_template_to_grid()
                        return
                    elif event.key == K_r:
                        self.reset_template()
                        return
                    elif event.key == K_h:
                        self.toggle_template()
                        return
                    elif event.key == K_l:
                        new_state = not self.settings.fix_template_scale
                        self.settings.fix_template_scale = new_state
                        self.ui.set_fix_scale_state(new_state)
                        return
                    elif event.key == K_s:
                        self.save_as_image()
                        return
                elif mods & KMOD_ALT and event.key == K_l:
                    self.choose_language_dialog()
                    return
                elif event.key == K_RETURN:
                    self.apply_size()
                    return

            # Обычные клавиши (без модификаторов)
            key_map = {
                K_c: self.clear_grid,
                K_l: self.load_ini_file,
                K_p: self.toggle_projection,
                K_o: self.toggle_coords,
                K_r: self.reset_view,
                K_z: self.reset_zoom,
                K_f: self.fit_to_screen,
            }
            if mods & KMOD_CTRL:
                if event.key == K_z:
                    self.undo()
                    return
                elif event.key == K_y:
                    self.redo()
                    return
            if event.key in key_map:
                key_map[event.key]()

    def toggle_help(self):
        self.show_help = not self.show_help

    def draw_help(self):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render(self.lang.get("help_title"), True, COLORS['text'])
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        self.screen.blit(title, title_rect)

        shortcuts = [
            ("LMB", self.lang.get("lmb_desc")),
            ("RMB", self.lang.get("rmb_desc")),
            ("MMB", self.lang.get("mmb_desc")),
            ("Ctrl+LMB", self.lang.get("ctrl_lmb_desc")),
            ("Ctrl+RMB", self.lang.get("ctrl_rmb_desc")),
            ("C", self.lang.get("c_desc")),
            ("L", self.lang.get("l_desc")),
            ("P", self.lang.get("p_desc")),
            ("O", self.lang.get("o_desc")),
            ("R", self.lang.get("r_desc")),
            ("Z", self.lang.get("z_desc")),
            ("F", self.lang.get("f_desc")),
            ("Ctrl+Z", self.lang.get("ctrl_z_desc")),
            ("Ctrl+Y", self.lang.get("ctrl_y_desc")),
            ("F1", self.lang.get("f1_desc")),
            ("Esc", self.lang.get("esc_desc")),
            ("Ctrl+Wheel", self.lang.get("template_zoom_desc")),
            ("Ctrl+MMB", self.lang.get("template_pan_desc")),
            ("G", self.lang.get("generate_outline_key_desc")),
            ("Ctrl+Enter", self.lang.get("apply_size_key_desc")),
            ("Ctrl+T", self.lang.get("load_template_key_desc")),
            ("Ctrl+Shift+F", self.lang.get("fit_template_key_desc")),
            ("Ctrl+Shift+R", self.lang.get("reset_template_key_desc")),
            ("Ctrl+Shift+H", self.lang.get("toggle_template_key_desc")),
            ("Ctrl+Shift+L", self.lang.get("fix_scale_key_desc")),
            ("Ctrl+E", self.lang.get("export_ini_key_desc")),
            ("Ctrl+Shift+S", self.lang.get("save_image_key_desc")),
            ("Ctrl+K", self.lang.get("color_scheme_key_desc")),
            ("Ctrl+Alt+L", self.lang.get("language_key_desc")),
        ]

        y_start = 100
        line_height = 25
        col_width = 350
        col1_x = self.screen_width // 2 - col_width - 50
        col2_x = self.screen_width // 2 + 50

        half = (len(shortcuts) + 1) // 2
        for i, (key, desc) in enumerate(shortcuts):
            col = i // half
            x = col1_x if col == 0 else col2_x
            y = y_start + (i % half) * line_height

            key_surf = self.font.render(key, True, COLORS['hover'])
            self.screen.blit(key_surf, (x, y))
            desc_surf = self.font.render(desc, True, COLORS['text'])
            self.screen.blit(desc_surf, (x + 120, y))

        footer = self.font.render(self.lang.get("help_close"), True, COLORS['text'])
        footer_rect = footer.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        self.screen.blit(footer, footer_rect)

    def _get_cell_from_mouse(self, pos):
        if self.settings.isometric:
            iso_w = ISO_W * self.zoom
            iso_h = ISO_H * self.zoom
            center_x = self.screen_width // 2 + self.view_offset[0]
            center_y = self.screen_height // 2 - ISO_CENTER_OFFSET_Y * self.zoom + self.view_offset[1]

            rel_x = pos[0] - center_x
            rel_y = pos[1] - center_y
            approx_x = (rel_x / iso_w + rel_y / iso_h) / 2
            approx_y = (rel_y / iso_h - rel_x / iso_w) / 2
            x0 = int(round(approx_x))
            y0 = int(round(approx_y))

            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx = x0 + dx
                    ny = y0 + dy
                    if 0 <= nx < self.grid.width and 0 <= ny < self.grid.height:
                        iso_x = center_x + (nx - ny) * iso_w
                        iso_y = center_y + (nx + ny) * iso_h
                        center_iso_y = iso_y + iso_h
                        norm_x = abs(pos[0] - iso_x) / iso_w
                        norm_y = abs(pos[1] - center_iso_y) / iso_h
                        if norm_x + norm_y <= 1.0:
                            return (nx, ny)
            return None
        else:
            cell_size = GRID_SIZE * self.zoom
            grid_pw = self.grid.width * cell_size
            start_x = (self.screen_width - grid_pw) // 2 + self.view_offset[0]
            start_y = UI_TOP_HEIGHT + 20 + self.view_offset[1]
            x = int((pos[0] - start_x) // cell_size)
            y = int((pos[1] - start_y) // cell_size)
            if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                return (x, y)
            return None

    def handle_grid_click(self, pos, button):
        mods = pygame.key.get_mods()
        outline_mode = mods & KMOD_CTRL

        cell = self._get_cell_from_mouse(pos)
        if cell:
            x, y = cell
            old_value = self.grid.outline[y, x] if outline_mode else self.grid.cells[y, x]
            new_value = (button == 1)
            if old_value != new_value:
                cmd = CellCommand(self.grid, x, y, old_value, new_value, outline_mode)
                self._push_command(cmd)
                cmd.execute()
                self.unsaved_changes = True
                self.settings.notify_grid_changed()

    def _push_command(self, cmd):
        if self.in_command:
            return
        self.undo_stack.append(cmd)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.in_command = True
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        self.in_command = False
        self.unsaved_changes = True
        self.settings.notify_grid_changed()

    def redo(self):
        if not self.redo_stack:
            return
        self.in_command = True
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)
        self.in_command = False
        self.unsaved_changes = True
        self.settings.notify_grid_changed()

    def apply_size(self):
        new_width = self.ui.get_width()
        new_height = self.ui.get_height()
        new_code = self.ui.get_building_code()

        if MIN_GRID_SIZE <= new_width <= MAX_GRID_SIZE and MIN_GRID_SIZE <= new_height <= MAX_GRID_SIZE:
            old_cells = self.grid.cells.copy()
            old_outline = self.grid.outline.copy()
            old_generated = self.grid.generated_outline[:]
            self.grid.resize(new_width, new_height)
            new_cells = self.grid.cells.copy()
            new_outline = self.grid.outline.copy()
            new_generated = self.grid.generated_outline[:]
            cmd = GridSnapshotCommand(self.grid, old_cells, old_outline, old_generated,
                                      new_cells, new_outline, new_generated)
            self._push_command(cmd)
            self.settings.grid_width = new_width
            self.settings.grid_height = new_height
            self.settings.building_code = new_code
            self.ui.set_values(new_code, new_width, new_height)
            self.unsaved_changes = True
        else:
            messagebox.showwarning(
                self.lang.get("invalid_size"),
                self.lang.get("size_range", min=MIN_GRID_SIZE, max=MAX_GRID_SIZE)
            )

    def clear_grid(self):
        old_cells = self.grid.cells.copy()
        old_outline = self.grid.outline.copy()
        old_generated = self.grid.generated_outline[:]
        self.grid.clear()
        new_cells = self.grid.cells.copy()
        new_outline = self.grid.outline.copy()
        new_generated = self.grid.generated_outline[:]
        cmd = GridSnapshotCommand(self.grid, old_cells, old_outline, old_generated,
                                  new_cells, new_outline, new_generated)
        self._push_command(cmd)
        self.unsaved_changes = True
        self.settings.notify_grid_changed()

    def generate_and_apply_outline(self):
        old_cells = self.grid.cells.copy()
        old_outline = self.grid.outline.copy()
        old_generated = self.grid.generated_outline[:]
        self.grid.apply_generated_outline()
        new_cells = self.grid.cells.copy()
        new_outline = self.grid.outline.copy()
        new_generated = self.grid.generated_outline[:]
        cmd = GridSnapshotCommand(self.grid, old_cells, old_outline, old_generated,
                                  new_cells, new_outline, new_generated)
        self._push_command(cmd)
        self.unsaved_changes = True
        self.settings.notify_grid_changed()

    def toggle_projection(self):
        self.settings.isometric = not self.settings.isometric
        self.reset_view()

    def toggle_coords(self):
        self.settings.show_coordinates = not self.settings.show_coordinates

    def reset_view(self):
        self.view_offset = [0, 0]
        self.zoom = 1.0
        self.ui.zoom_slider.set_val(self.zoom)

    def reset_zoom(self):
        self.zoom = 1.0
        self.ui.zoom_slider.set_val(self.zoom)

    def set_zoom(self, new_zoom):
        self.zoom = new_zoom

    def fit_to_screen(self):
        if self.settings.isometric:
            if self.renderer.iso_bounding_box is None:
                self.renderer._update_iso_cache()
            min_x, max_x, min_y, max_y = self.renderer.iso_bounding_box
            width = max_x - min_x
            height = max_y - min_y
            margin = 50
            available_w = self.screen_width - 2 * margin
            available_h = self.screen_height - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT - 2 * margin
            zoom_x = available_w / width if width > 0 else 1
            zoom_y = available_h / height if height > 0 else 1
            self.zoom = min(zoom_x, zoom_y, self.max_zoom)
            self.zoom = max(self.zoom, self.min_zoom)
            self.view_offset = [0, 0]
        else:
            w, h = self.grid.width, self.grid.height
            cell_size = GRID_SIZE
            grid_w = w * cell_size
            grid_h = h * cell_size
            margin = 50
            available_w = self.screen_width - 2 * margin
            available_h = self.screen_height - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT - 2 * margin
            zoom_x = available_w / grid_w if grid_w > 0 else 1
            zoom_y = available_h / grid_h if grid_h > 0 else 1
            self.zoom = min(zoom_x, zoom_y, self.max_zoom)
            self.zoom = max(self.zoom, self.min_zoom)
            self.view_offset = [0, 0]
        self.ui.zoom_slider.set_val(self.zoom)

    def _ensure_export_dir(self):
        if not os.path.exists(EXPORT_DIR):
            try:
                os.makedirs(EXPORT_DIR)
            except Exception as e:
                messagebox.showerror(
                    self.lang.get("directory_error"),
                    self.lang.get("cannot_create_export_dir", error=str(e))
                )
                return False
        return True

    def export_to_ini(self):
        if not self.grid.is_outline_closed():
            messagebox.showwarning(
                self.lang.get("outline_warning"),
                self.lang.get("outline_not_closed")
            )
            return

        if not self._ensure_export_dir():
            return

        config = CasePreservingConfigParser()
        code = self.ui.get_building_code()
        config[code] = {
            'Foundation': 'Custom',
            'Foundation.X': str(self.grid.width),
            'Foundation.Y': str(self.grid.height)
        }
        for i, (y, x) in enumerate(self.grid.get_filled_cells()):
            config[code][f'Foundation.{i}'] = f'{x},{y}'

        outline = self.grid.get_outline_cells()
        if len(outline) > 0:
            config[code]['FoundationOutline.Length'] = str(len(outline))
            for i, (y, x) in enumerate(outline):
                config[code][f'FoundationOutline.{i}'] = f'{x},{y}'

        filepath = os.path.join(EXPORT_DIR, f"{code}_foundation.ini")
        try:
            with open(filepath, 'w') as f:
                config.write(f)
            messagebox.showinfo(
                self.lang.get("export_successful"),
                self.lang.get("exported_to", path=os.path.abspath(filepath))
            )
            self.unsaved_changes = False
        except Exception as e:
            messagebox.showerror(
                self.lang.get("export_error"),
                self.lang.get("could_not_save", error=str(e))
            )

    def save_as_image(self):
        if not self._ensure_export_dir():
            return

        surf_ortho = self.renderer.render_orthogonal_surface()
        surf_iso = self.renderer.render_isometric_surface()

        base = f"{self.ui.get_building_code()}_foundation"
        path_ortho = os.path.join(EXPORT_DIR, f"{base}_orthogonal.png")
        path_iso = os.path.join(EXPORT_DIR, f"{base}_isometric.png")

        try:
            pygame.image.save(surf_ortho, path_ortho)
            pygame.image.save(surf_iso, path_iso)
            messagebox.showinfo(
                self.lang.get("images_saved"),
                f"{self.lang.get('orthogonal')}: {os.path.abspath(path_ortho)}\n{self.lang.get('isometric')}: {os.path.abspath(path_iso)}"
            )
        except Exception as e:
            messagebox.showerror(
                self.lang.get("export_error"),
                self.lang.get("could_not_save", error=str(e))
            )

    # --- Методы для шаблона ---
    def load_template_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            self.template_image = pygame.image.load(file_path).convert_alpha()
            self.template_surface = self.template_image.copy()
            self.template_filename = os.path.basename(file_path)
            self.template_alpha = self.settings.template_alpha
            self.template_scale = self.settings.template_scale
            self.template_offset = self.settings.template_offset[:]
            self.show_template = self.settings.show_template
            self.ui.alpha_slider.set_val(self.template_alpha)
            self.ui.scale_slider.set_val(self.template_scale)
            self.settings.template_path = file_path
            self.unsaved_changes = True
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    def set_template_alpha(self, value):
        self.template_alpha = max(0, min(255, int(value)))
        self.settings.template_alpha = self.template_alpha
        self.unsaved_changes = True

    def set_template_scale(self, value):
        self.template_scale = max(TEMPLATE_SCALE_MIN, min(TEMPLATE_SCALE_MAX, value))
        self.settings.template_scale = self.template_scale
        self.unsaved_changes = True

    def fit_template_to_grid(self):
        if self.template_surface is None:
            return
        grid_px_width = self.grid.width * GRID_SIZE
        grid_px_height = self.grid.height * GRID_SIZE
        img_w, img_h = self.template_surface.get_size()
        scale_w = grid_px_width / img_w
        scale_h = grid_px_height / img_h
        self.template_scale = min(scale_w, scale_h)
        self.template_offset[0] = (grid_px_width - img_w * self.template_scale) / 2
        self.template_offset[1] = (grid_px_height - img_h * self.template_scale) / 2
        self.settings.template_scale = self.template_scale
        self.settings.template_offset = self.template_offset[:]
        self.ui.scale_slider.set_val(self.template_scale)
        self.unsaved_changes = True

    def reset_template(self):
        self.template_scale = TEMPLATE_SCALE_DEFAULT
        self.template_offset = [0, 0]
        self.template_alpha = TEMPLATE_ALPHA_DEFAULT
        self.settings.template_scale = self.template_scale
        self.settings.template_offset = self.template_offset[:]
        self.settings.template_alpha = self.template_alpha
        self.ui.scale_slider.set_val(self.template_scale)
        self.ui.alpha_slider.set_val(self.template_alpha)
        self.unsaved_changes = True

    def toggle_template(self, state=None):
        if state is not None:
            self.show_template = state
        else:
            self.show_template = not self.show_template
        self.settings.show_template = self.show_template
        self.unsaved_changes = True

    def draw(self):
        self.screen.fill(COLORS['background'])

        if self.show_template and self.template_surface:
            self.renderer.draw_template(
                self.screen,
                self.template_surface,
                self.template_offset,
                self.template_scale,
                self.template_alpha,
                self.view_offset,
                self.zoom
            )

        if self.settings.isometric:
            self.renderer.draw_isometric(self.screen, self.view_offset, self.settings.show_coordinates, self.zoom)
        else:
            self.renderer.draw_orthogonal(self.screen, self.view_offset, self.settings.show_coordinates, self.zoom)
            self.renderer.draw_axes(self.screen, self.view_offset, self.settings.show_coordinates, self.zoom)

        if not self.grid.is_outline_closed():
            text = self.warning_font.render(self.lang.get("warning_not_closed"), True, COLORS['warning'])
            bg = text.get_rect(center=(self.screen_width // 2, UI_TOP_HEIGHT))
            bg.inflate_ip(20, 10)
            pygame.draw.rect(self.screen, (40, 40, 50), bg, border_radius=10)
            pygame.draw.rect(self.screen, COLORS['warning'], bg, 2, border_radius=10)
            self.screen.blit(text, text.get_rect(center=bg.center))

        title = self.title_font.render("Ares Foundation Generator +", True, COLORS['text'])
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 5))

        self.ui.draw(self.screen)

        filled, outline_len, bb_width, bb_height, aspect = self._get_stats()
        stats_text = f"{self.lang.get('filled')}: {filled} | {self.lang.get('outline')}: {outline_len} | {self.lang.get('bbox')}: {bb_width}x{bb_height} | {self.lang.get('aspect')}: {aspect:.2f}"
        self.screen.blit(self.font.render(stats_text, True, COLORS['text']), (20, self.screen_height - 65))

        proj = self.lang.get("isometric") if self.settings.isometric else self.lang.get("orthogonal")
        coords_state = self.lang.get("coords") + " " + (self.lang.get("on") if self.settings.show_coordinates else self.lang.get("off"))
        mouse_info = f" | {self.lang.get('mouse')}: {self.mouse_cell[0]},{self.mouse_cell[1]}" if self.mouse_cell else ""
        outline_mode = f" | [{self.lang.get('outline_mode')}]" if pygame.key.get_mods() & KMOD_CTRL else ""
        undo_count = len(self.undo_stack)
        redo_count = len(self.redo_stack)
        status = f"{self.lang.get('projection')}: [{proj}] | {coords_state} | {self.lang.get('ctrl_z_desc')}: {undo_count} | {self.lang.get('ctrl_y_desc')}: {redo_count} | {self.lang.get('loaded')}: '{self.loaded_filename}'{mouse_info}{outline_mode}"
        self.screen.blit(self.font.render(status, True, COLORS['text']), (20, self.screen_height - 45))

        controls = self.lang.get("controls")
        self.screen.blit(self.font.render(controls, True, COLORS['text']), (20, self.screen_height - 25))

        if self.show_help:
            self.draw_help()

        if self.dialog:
            self.dialog.draw(self.screen)

        pygame.display.flip()

    def _get_stats(self):
        filled = np.sum(self.grid.cells)
        outline_len = np.sum(self.grid.outline)
        if filled > 0:
            rows, cols = np.where(self.grid.cells)
            min_row, max_row = np.min(rows), np.max(rows)
            min_col, max_col = np.min(cols), np.max(cols)
            bb_height = max_row - min_row + 1
            bb_width = max_col - min_col + 1
            aspect = bb_width / bb_height if bb_height > 0 else 1.0
        else:
            bb_width = bb_height = 0
            aspect = 0.0
        return filled, outline_len, bb_width, bb_height, aspect


if __name__ == "__main__":
    app = FoundationGenerator(width=15, height=15)
    app.run()