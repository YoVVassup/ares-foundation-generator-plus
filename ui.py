import pygame
import os
from pygame.locals import *
from constants import BORDER_RADIUS, TOOLTIP_DELAY, COLORS, MIN_GRID_SIZE, UI_TOP_HEIGHT
from utils import get_resource_path

# Попытка инициализации буфера обмена pygame
try:
    pygame.scrap.init()
    SCRAP_AVAILABLE = True
except:
    SCRAP_AVAILABLE = False
    print("Clipboard support not available. Paste functionality disabled.")

# -------------------- Элементы интерфейса --------------------

class TextInput:
    """Класс для поля ввода текста."""
    def __init__(self, x, y, width, height, font, default_text="", numeric=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = default_text
        self.active = False
        self.font = font
        self.cursor_timer = 0
        self.numeric = numeric

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if self.active and event.type == KEYDOWN:
            mods = pygame.key.get_mods()
            if mods & KMOD_CTRL and event.key == K_v:
                self.paste_from_clipboard()
                return False
            elif event.key == K_RETURN:
                return True
            elif event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if not self.numeric or event.unicode.isdigit():
                    self.text += event.unicode
        return False

    def paste_from_clipboard(self):
        """Вставляет текст из буфера обмена."""
        if not SCRAP_AVAILABLE:
            return
        try:
            text = pygame.scrap.get(pygame.SCRAP_TEXT)
            if text:
                if isinstance(text, bytes):
                    text = text.decode('utf-8', errors='ignore')
                if self.numeric:
                    filtered = ''.join(c for c in text if c.isdigit())
                else:
                    filtered = text
                self.text += filtered
        except Exception as e:
            print(f"Error pasting from clipboard: {e}")

    def draw(self, screen):
        color = COLORS['hover'] if self.active else COLORS['button']
        pygame.draw.rect(screen, color, self.rect, border_radius=BORDER_RADIUS)
        pygame.draw.rect(screen, COLORS['outline'], self.rect, 2, border_radius=BORDER_RADIUS)

        text_surface = self.font.render(self.text, True, COLORS['text'])
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + (self.rect.height - text_surface.get_height()) // 2))

        if self.active:
            self.cursor_timer = (self.cursor_timer + 1) % 40
            if self.cursor_timer < 20:
                cursor_x = self.rect.x + 10 + text_surface.get_width()
                pygame.draw.line(screen, COLORS['text'], (cursor_x, self.rect.y + 8),
                                 (cursor_x, self.rect.y + self.rect.height - 8), 2)

    def update_pos(self, x, y, width=None, height=None):
        self.rect.topleft = (x, y)
        if width:
            self.rect.width = width
        if height:
            self.rect.height = height


class IconButton:
    """Кнопка с иконкой (PNG или символом) и всплывающей подсказкой."""
    def __init__(self, x, y, size, icon_source, tooltip, font, action, icon_scale=0.8):
        self.rect = pygame.Rect(x, y, size, size)
        self.tooltip = tooltip
        self.font = font
        self.action = action
        self.is_hovered = False
        self.hover_counter = 0
        self.image = None
        self.icon = None  # для текстового символа

        # Загрузка изображения
        if isinstance(icon_source, str):
            # Если передан путь к SVG, заменяем расширение на .png
            if icon_source.lower().endswith('.svg'):
                png_source = icon_source[:-4] + '.png'
            else:
                png_source = icon_source

            full_path = get_resource_path(png_source)
            if os.path.exists(full_path):
                try:
                    self.image = pygame.image.load(full_path).convert_alpha()
                    # Масштабируем до нужного размера
                    target_size = int(size * icon_scale)
                    if self.image.get_width() != target_size:
                        self.image = pygame.transform.smoothscale(self.image, (target_size, target_size))
                except Exception as e:
                    print(f"Error loading image {png_source}: {e}")
                    self.icon = os.path.basename(icon_source)
            else:
                self.icon = os.path.basename(icon_source)
        else:
            self.icon = icon_source

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_hovered and not was_hovered:
                self.hover_counter = 0
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return self.action
        return None

    def draw(self, screen):
        color = COLORS['hover'] if self.is_hovered else COLORS['button']
        pygame.draw.rect(screen, color, self.rect, border_radius=BORDER_RADIUS)
        pygame.draw.rect(screen, COLORS['outline'], self.rect, 2, border_radius=BORDER_RADIUS)

        if self.image:
            img_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, img_rect)
        elif self.icon:
            icon_surf = self.font.render(self.icon, True, COLORS['text'])
            icon_rect = icon_surf.get_rect(center=self.rect.center)
            screen.blit(icon_surf, icon_rect)

    def draw_tooltip(self, screen):
        """Отрисовывает тултип с автоматической корректировкой позиции."""
        if self.is_hovered:
            self.hover_counter += 1
            if self.hover_counter > TOOLTIP_DELAY:
                tooltip_surf = self.font.render(self.tooltip, True, COLORS['tooltip_text'])
                tooltip_rect = tooltip_surf.get_rect()
                # Желаемая позиция: над кнопкой по центру
                desired_x = self.rect.centerx
                desired_y = self.rect.top - 5
                tooltip_rect.midbottom = (desired_x, desired_y)

                screen_rect = screen.get_rect()
                if tooltip_rect.left < 0:
                    tooltip_rect.left = 5
                if tooltip_rect.right > screen_rect.width:
                    tooltip_rect.right = screen_rect.width - 5
                if tooltip_rect.top < 0:
                    # Не помещается сверху — показываем снизу
                    tooltip_rect.midtop = (desired_x, self.rect.bottom + 5)
                    if tooltip_rect.bottom > screen_rect.height:
                        tooltip_rect.bottom = screen_rect.height - 5

                bg_rect = tooltip_rect.inflate(10, 4)
                pygame.draw.rect(screen, COLORS['tooltip_bg'], bg_rect, border_radius=3)
                pygame.draw.rect(screen, COLORS['outline'], bg_rect, 1, border_radius=3)
                screen.blit(tooltip_surf, tooltip_rect)
        else:
            self.hover_counter = 0

    def update_pos(self, x, y):
        self.rect.topleft = (x, y)


class Toolbar:
    def __init__(self, font, icons_data):
        self.font = font
        self.buttons = []
        self.spacing = 10
        self.button_size = 36
        for icon, tooltip, action in icons_data:
            btn = IconButton(0, 0, self.button_size, icon, tooltip, self.font, action)
            self.buttons.append(btn)

    def handle_event(self, event):
        for btn in self.buttons:
            action = btn.handle_event(event)
            if action:
                return action
        return None

    def draw(self, screen):
        for btn in self.buttons:
            btn.draw(screen)

    def draw_tooltips(self, screen):
        """Отрисовывает тултипы всех кнопок панели."""
        for btn in self.buttons:
            btn.draw_tooltip(screen)

    def update_pos(self, start_x, start_y):
        x = start_x
        for btn in self.buttons:
            btn.update_pos(x, start_y)
            x += self.button_size + self.spacing


class Slider:
    """Горизонтальный ползунок для управления значением в диапазоне."""
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, font, label, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.font = font
        self.label = label
        self.callback = callback
        self.dragging = False
        self.handle_radius = height + 4
        self.update_handle_pos()

    def update_handle_pos(self):
        t = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = self.rect.x + t * self.rect.width
        self.handle_y = self.rect.centery

    def set_val(self, new_val):
        self.val = max(self.min_val, min(self.max_val, new_val))
        self.update_handle_pos()
        if self.callback:
            self.callback(self.val)

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            handle_rect = pygame.Rect(self.handle_x - self.handle_radius, self.handle_y - self.handle_radius,
                                      2 * self.handle_radius, 2 * self.handle_radius)
            if handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif self.rect.collidepoint(event.pos):
                t = (event.pos[0] - self.rect.x) / self.rect.width
                new_val = self.min_val + t * (self.max_val - self.min_val)
                self.set_val(new_val)
                self.dragging = True

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == MOUSEMOTION and self.dragging:
            t = (event.pos[0] - self.rect.x) / self.rect.width
            new_val = self.min_val + t * (self.max_val - self.min_val)
            self.set_val(new_val)

    def draw(self, screen):
        pygame.draw.rect(screen, COLORS['slider_bg'], self.rect, border_radius=BORDER_RADIUS)
        pygame.draw.circle(screen, COLORS['slider_handle'], (int(self.handle_x), int(self.handle_y)),
                           self.handle_radius)
        pygame.draw.circle(screen, COLORS['outline'], (int(self.handle_x), int(self.handle_y)), self.handle_radius, 2)

        val_text = self.font.render(f"{self.label}: {self.val:.2f}", True, COLORS['text'])
        text_rect = val_text.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
        screen.blit(val_text, text_rect)

    def update_pos(self, x, y, width=None, height=None):
        self.rect.topleft = (x, y)
        if width:
            self.rect.width = width
        if height:
            self.rect.height = height
        self.update_handle_pos()

    def set_label(self, label):
        """Обновляет текст метки слайдера."""
        self.label = label


class Button:
    """Простая кнопка с текстом, используется в диалогах."""
    def __init__(self, rect, text, font, normal_color, hover_color, text_color, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.callback = callback
        self.hovered = False

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.callback()
            return True
        return False

    def draw(self, screen):
        color = self.hover_color if self.hovered else self.normal_color
        pygame.draw.rect(screen, color, self.rect, border_radius=BORDER_RADIUS)
        pygame.draw.rect(screen, COLORS['outline'], self.rect, 2, border_radius=BORDER_RADIUS)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class ToggleButton:
    """Кнопка с двумя состояниями (вкл/выкл) с иконками PNG."""
    def __init__(self, x, y, size, icon_on, icon_off, tooltip_on, tooltip_off, font, action, initial_state=False, icon_scale=0.8):
        self.rect = pygame.Rect(x, y, size, size)
        self.font = font
        self.action = action
        self.state = initial_state
        self.is_hovered = False
        self.hover_counter = 0
        self.icon_on = icon_on
        self.icon_off = icon_off
        self.tooltip_on = tooltip_on
        self.tooltip_off = tooltip_off
        self.image_on = None
        self.image_off = None
        self.icon_scale = icon_scale

        def load_image(icon_path):
            if isinstance(icon_path, str):
                # Преобразуем .svg в .png, если нужно
                if icon_path.lower().endswith('.svg'):
                    png_path = icon_path[:-4] + '.png'
                else:
                    png_path = icon_path
                full_path = get_resource_path(png_path)
                if os.path.exists(full_path):
                    try:
                        img = pygame.image.load(full_path).convert_alpha()
                        target_size = int(size * icon_scale)
                        if img.get_width() != target_size:
                            img = pygame.transform.smoothscale(img, (target_size, target_size))
                        return img
                    except Exception as e:
                        print(f"Error loading image {png_path}: {e}")
            return None

        self.image_on = load_image(icon_on)
        self.image_off = load_image(icon_off) if icon_off else None

        # Если изображения не загрузились, используем текстовые метки
        if self.image_on is None and isinstance(icon_on, str):
            self.icon_on = os.path.basename(icon_on)
        else:
            self.icon_on = None

        if self.image_off is None and isinstance(icon_off, str):
            self.icon_off = os.path.basename(icon_off)
        else:
            self.icon_off = None

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_hovered and not was_hovered:
                self.hover_counter = 0
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.state = not self.state
            return self.action(self.state)  # передаём состояние
        return None

    def draw(self, screen):
        color = COLORS['hover'] if self.is_hovered else COLORS['button']
        pygame.draw.rect(screen, color, self.rect, border_radius=BORDER_RADIUS)
        pygame.draw.rect(screen, COLORS['outline'], self.rect, 2, border_radius=BORDER_RADIUS)

        if self.state:
            if self.image_on:
                img_rect = self.image_on.get_rect(center=self.rect.center)
                screen.blit(self.image_on, img_rect)
            elif self.icon_on:
                icon_surf = self.font.render(self.icon_on, True, COLORS['text'])
                icon_rect = icon_surf.get_rect(center=self.rect.center)
                screen.blit(icon_surf, icon_rect)
        else:
            if self.image_off:
                img_rect = self.image_off.get_rect(center=self.rect.center)
                screen.blit(self.image_off, img_rect)
            elif self.icon_off:
                icon_surf = self.font.render(self.icon_off, True, COLORS['text'])
                icon_rect = icon_surf.get_rect(center=self.rect.center)
                screen.blit(icon_surf, icon_rect)

    def draw_tooltip(self, screen):
        """Отрисовывает тултип с учётом состояния кнопки и автоматической корректировкой позиции."""
        if self.is_hovered:
            self.hover_counter += 1
            if self.hover_counter > TOOLTIP_DELAY:
                tooltip = self.tooltip_on if self.state else self.tooltip_off
                tooltip_surf = self.font.render(tooltip, True, COLORS['tooltip_text'])
                tooltip_rect = tooltip_surf.get_rect()
                # Желаемая позиция: над кнопкой по центру
                desired_x = self.rect.centerx
                desired_y = self.rect.top - 5
                tooltip_rect.midbottom = (desired_x, desired_y)

                screen_rect = screen.get_rect()
                if tooltip_rect.left < 0:
                    tooltip_rect.left = 5
                if tooltip_rect.right > screen_rect.width:
                    tooltip_rect.right = screen_rect.width - 5
                if tooltip_rect.top < 0:
                    # Не помещается сверху — показываем снизу
                    tooltip_rect.midtop = (desired_x, self.rect.bottom + 5)
                    if tooltip_rect.bottom > screen_rect.height:
                        tooltip_rect.bottom = screen_rect.height - 5

                bg_rect = tooltip_rect.inflate(10, 4)
                pygame.draw.rect(screen, COLORS['tooltip_bg'], bg_rect, border_radius=3)
                pygame.draw.rect(screen, COLORS['outline'], bg_rect, 1, border_radius=3)
                screen.blit(tooltip_surf, tooltip_rect)
        else:
            self.hover_counter = 0

    def update_pos(self, x, y):
        self.rect.topleft = (x, y)

    def set_state(self, state):
        self.state = state


class OptionDialog:
    """Модальное окно выбора из списка опций."""
    def __init__(self, title, options, font, title_font, colors, on_select):
        """
        options: список кортежей (value, display_text)
        on_select: callback, принимающий выбранное value
        """
        self.title = title
        self.options = options
        self.font = font
        self.title_font = title_font
        self.colors = colors
        self.on_select = on_select
        self.active = True
        self.selected = None

        self.button_height = 40
        self.padding = 20
        self.spacing = 10
        self.min_width = 300
        self.max_width = 500

        text_widths = [title_font.size(title)[0]] + [font.size(opt[1])[0] for opt in options]
        content_width = max(text_widths) + 2 * self.padding
        self.window_width = max(self.min_width, min(content_width, self.max_width))

        title_height = title_font.get_height() + self.padding
        buttons_height = len(options) * (self.button_height + self.spacing) - self.spacing
        self.window_height = title_height + buttons_height + 3 * self.padding

        screen = pygame.display.get_surface()
        self.window_rect = pygame.Rect(
            (screen.get_width() - self.window_width) // 2,
            (screen.get_height() - self.window_height) // 2,
            self.window_width,
            self.window_height
        )

        self.buttons = []
        y = self.window_rect.y + title_height + self.padding
        for value, text in options:
            btn_rect = pygame.Rect(
                self.window_rect.x + self.padding,
                y,
                self.window_width - 2 * self.padding,
                self.button_height
            )
            btn = Button(
                btn_rect, text, font,
                normal_color=self.colors['button'],
                hover_color=self.colors['hover'],
                text_color=self.colors['text'],
                callback=lambda v=value: self.select(v)
            )
            self.buttons.append(btn)
            y += self.button_height + self.spacing

    def select(self, value):
        self.selected = value
        self.on_select(value)
        self.active = False

    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            self.active = False
            return True

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if not self.window_rect.collidepoint(event.pos):
                self.active = False
                return True

        for btn in self.buttons:
            if btn.handle_event(event):
                return True

        return False

    def draw(self, screen):
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, self.colors['background'], self.window_rect, border_radius=10)
        pygame.draw.rect(screen, self.colors['outline'], self.window_rect, 3, border_radius=10)

        title_surf = self.title_font.render(self.title, True, self.colors['text'])
        title_rect = title_surf.get_rect(center=(self.window_rect.centerx, self.window_rect.y + self.padding + self.title_font.get_height()//2))
        screen.blit(title_surf, title_rect)

        for btn in self.buttons:
            btn.draw(screen)


class ConfirmDialog:
    """Модальное окно подтверждения с тремя кнопками: Yes, No, Cancel."""
    def __init__(self, title, message, font, title_font, colors, on_yes, on_no, on_cancel, lang):
        """
        title: заголовок окна
        message: текст сообщения
        on_yes, on_no, on_cancel: callback'и
        lang: объект Localization для получения текста кнопок
        """
        self.title = title
        self.message = message
        self.font = font
        self.title_font = title_font
        self.colors = colors
        self.on_yes = on_yes
        self.on_no = on_no
        self.on_cancel = on_cancel
        self.lang = lang
        self.active = True

        self.button_height = 40
        self.button_width = 100
        self.padding = 20
        self.spacing = 10

        screen = pygame.display.get_surface()
        msg_lines = message.split('\n')
        max_line_width = max(title_font.size(title)[0], max(font.size(line)[0] for line in msg_lines))
        # Ширина левой группы (2 кнопки + промежуток)
        left_group_width = 2 * self.button_width + self.spacing
        # Ширина правой кнопки
        right_button_width = self.button_width
        # Минимальная ширина окна: либо под текст, либо под кнопки + отступы
        self.window_width = max(
            max_line_width + 2 * self.padding,
            left_group_width + right_button_width + 3 * self.padding  # padding слева, между группами, справа
        )
        self.window_height = (title_font.get_height() + self.padding +
                              len(msg_lines) * font.get_height() + self.padding +
                              self.button_height + 2 * self.padding)

        self.window_rect = pygame.Rect(
            (screen.get_width() - self.window_width) // 2,
            (screen.get_height() - self.window_height) // 2,
            self.window_width,
            self.window_height
        )

        button_y = self.window_rect.bottom - self.button_height - self.padding

        # Левая группа: Yes и No
        x_left = self.window_rect.x + self.padding
        btn_yes_rect = pygame.Rect(
            x_left,
            button_y,
            self.button_width,
            self.button_height
        )
        btn_no_rect = pygame.Rect(
            btn_yes_rect.right + self.spacing,
            button_y,
            self.button_width,
            self.button_height
        )

        # Правая кнопка: Cancel
        x_right = self.window_rect.right - self.padding - self.button_width
        btn_cancel_rect = pygame.Rect(
            x_right,
            button_y,
            self.button_width,
            self.button_height
        )

        self.yes_button = Button(
            btn_yes_rect, lang.get("yes"), font,
            normal_color=colors['button'],
            hover_color=colors['hover'],
            text_color=colors['text'],
            callback=lambda: self.select('yes')
        )
        self.no_button = Button(
            btn_no_rect, lang.get("no"), font,
            normal_color=colors['button'],
            hover_color=colors['hover'],
            text_color=colors['text'],
            callback=lambda: self.select('no')
        )
        self.cancel_button = Button(
            btn_cancel_rect, lang.get("cancel"), font,
            normal_color=colors['button'],
            hover_color=colors['hover'],
            text_color=colors['text'],
            callback=lambda: self.select('cancel')
        )

        self.buttons = [self.yes_button, self.no_button, self.cancel_button]

    def select(self, choice):
        if choice == 'yes':
            self.on_yes()
        elif choice == 'no':
            self.on_no()
        elif choice == 'cancel':
            self.on_cancel()
        self.active = False

    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            self.select('cancel')
            return True

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if not self.window_rect.collidepoint(event.pos):
                self.select('cancel')
                return True

        for btn in self.buttons:
            if btn.handle_event(event):
                return True

        return False

    def draw(self, screen):
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, self.colors['background'], self.window_rect, border_radius=10)
        pygame.draw.rect(screen, self.colors['outline'], self.window_rect, 3, border_radius=10)

        title_surf = self.title_font.render(self.title, True, self.colors['text'])
        title_rect = title_surf.get_rect(center=(self.window_rect.centerx, self.window_rect.y + self.padding + self.title_font.get_height()//2))
        screen.blit(title_surf, title_rect)

        y = title_rect.bottom + self.padding
        for line in self.message.split('\n'):
            line_surf = self.font.render(line, True, self.colors['text'])
            line_rect = line_surf.get_rect(center=(self.window_rect.centerx, y))
            screen.blit(line_surf, line_rect)
            y += self.font.get_height()

        for btn in self.buttons:
            btn.draw(screen)


class UIController:
    def __init__(self, font, ui_font, on_apply_size, on_generate_outline, on_clear,
                 on_export_ini, on_save_image, on_load_ini, on_toggle_projection,
                 on_toggle_coords, on_reset_view, on_fit_to_screen,
                 on_undo, on_redo, on_zoom_changed, on_change_color_scheme,
                 on_change_language, on_load_template, on_template_alpha_changed,
                 on_template_scale_changed, on_template_fit, on_template_reset,
                 on_toggle_template, on_toggle_fix_template_scale,
                 on_reset_zoom,  # новый параметр
                 lang):
        self.font = font
        self.ui_font = ui_font
        self.on_apply_size = on_apply_size
        self.on_generate_outline = on_generate_outline
        self.on_clear = on_clear
        self.on_export_ini = on_export_ini
        self.on_save_image = on_save_image
        self.on_load_ini = on_load_ini
        self.on_toggle_projection = on_toggle_projection
        self.on_toggle_coords = on_toggle_coords
        self.on_reset_view = on_reset_view
        self.on_fit_to_screen = on_fit_to_screen
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_zoom_changed = on_zoom_changed
        self.on_change_color_scheme = on_change_color_scheme
        self.on_change_language = on_change_language
        self.on_load_template = on_load_template
        self.on_template_alpha_changed = on_template_alpha_changed
        self.on_template_scale_changed = on_template_scale_changed
        self.on_template_fit = on_template_fit
        self.on_template_reset = on_template_reset
        self.on_toggle_template = on_toggle_template
        self.on_toggle_fix_template_scale = on_toggle_fix_template_scale
        self.on_reset_zoom = on_reset_zoom
        self.lang = lang

        # Словарь действий
        self.action_map = {
            "apply_size": self.on_apply_size,
            "generate_outline": self.on_generate_outline,
            "clear": self.on_clear,
            "export_ini": self.on_export_ini,
            "save_image": self.on_save_image,
            "load_ini": self.on_load_ini,
            "toggle_projection": self.on_toggle_projection,
            "toggle_coords": self.on_toggle_coords,
            "reset_view": self.on_reset_view,
            "fit_to_screen": self.on_fit_to_screen,
            "undo": self.on_undo,
            "redo": self.on_redo,
            "change_color_scheme": self.on_change_color_scheme,
            "change_language": self.on_change_language,
            "load_template": self.on_load_template,
            "template_fit": self.on_template_fit,
            "template_reset": self.on_template_reset,
            "toggle_template": self.on_toggle_template,
            "reset_zoom": self.on_reset_zoom,
        }

        self.building_code_input = TextInput(20, 60, 200, 36, ui_font, "TEMP")
        self.width_input = TextInput(230, 60, 60, 36, ui_font, "15", numeric=True)
        self.height_input = TextInput(290, 60, 60, 36, ui_font, "15", numeric=True)
        self.text_inputs = [self.building_code_input, self.width_input, self.height_input]

        size_icons = [
            ("icons/apply_size.svg", lang.get("apply_size"), "apply_size"),
            ("icons/generate_outline.svg", lang.get("generate_outline"), "generate_outline"),
        ]
        self.size_toolbar = Toolbar(font, size_icons)

        # Кнопки шаблона (используем ToggleButton для показа/скрытия)
        template_icons = [
            ("icons/load_template.svg", lang.get("load_template"), "load_template"),
            ("icons/fit_template.svg", lang.get("template_fit"), "template_fit"),
            ("icons/reset_template.svg", lang.get("template_reset"), "template_reset"),
        ]
        self.template_toolbar = Toolbar(font, template_icons)

        # Отдельная кнопка для переключения видимости шаблона (ToggleButton)
        self.toggle_template_button = ToggleButton(
            0, 0, 36,
            "icons/toggle_template.svg", "icons/toggle_template.svg",
            lang.get("template_hide"), lang.get("template_show"),
            font,
            self.on_toggle_template,
            initial_state=False,
            icon_scale=0.8
        )

        # Слайдеры прозрачности и масштаба
        self.alpha_slider = Slider(0, 0, 150, 10, 0, 255, 128, font, lang.get("template_alpha"),
                                   self.on_template_alpha_changed)
        self.scale_slider = Slider(0, 0, 150, 10, 0.1, 5.0, 1.0, font, lang.get("template_scale"),
                                   self.on_template_scale_changed)

        # ToggleButton для фиксации масштаба шаблона
        self.fix_scale_button = ToggleButton(
            0, 0, 36,
            "icons/link.svg", "icons/unlink.svg",
            lang.get("fix_template_scale_on"), lang.get("fix_template_scale_off"),
            font,
            self.on_toggle_fix_template_scale,
            initial_state=False,
            icon_scale=0.8
        )

        bottom_icons = [
            ("icons/clear.svg", lang.get("clear"), "clear"),
            ("icons/export_ini.svg", lang.get("export_ini"), "export_ini"),
            ("icons/save_image.svg", lang.get("save_image"), "save_image"),
            ("icons/load_ini.svg", lang.get("load_ini"), "load_ini"),
            ("icons/undo.svg", lang.get("undo"), "undo"),
            ("icons/redo.svg", lang.get("redo"), "redo"),
            ("icons/fit_to_screen.svg", lang.get("fit_to_screen"), "fit_to_screen"),
            ("icons/reset_zoom.svg", lang.get("z_desc"), "reset_zoom"),
            ("icons/toggle_projection.svg", lang.get("toggle_projection"), "toggle_projection"),
            ("icons/toggle_coords.svg", lang.get("toggle_coords"), "toggle_coords"),
            ("icons/reset_view.svg", lang.get("reset_view"), "reset_view"),
            ("icons/color_scheme.svg", lang.get("choose_color_scheme"), "change_color_scheme"),
            ("icons/language.svg", lang.get("choose_language"), "change_language"),
        ]
        self.toolbar = Toolbar(font, bottom_icons)

        self.zoom_slider = Slider(0, 0, 150, 10, 0.5, 3.0, 1.0, font, lang.get("zoom"), self.on_zoom_changed)

    def update_layout(self, screen_width, screen_height):
        self.building_code_input.update_pos(20, 60, 200)
        self.width_input.update_pos(230, 60, 60)
        self.height_input.update_pos(290, 60, 60)

        size_toolbar_x = 360
        size_toolbar_y = 60
        self.size_toolbar.update_pos(size_toolbar_x, size_toolbar_y)

        bottom_toolbar_y = screen_height - 106
        bottom_toolbar_x = 20
        self.toolbar.update_pos(bottom_toolbar_x, bottom_toolbar_y)

        slider_x = screen_width - 300
        slider_y = screen_height - 75
        self.zoom_slider.update_pos(slider_x, slider_y, 180, 12)

        # Размещаем элементы шаблона справа сверху
        template_x = screen_width - 330
        template_y = UI_TOP_HEIGHT - 60
        self.template_toolbar.update_pos(template_x, template_y)
        self.toggle_template_button.update_pos(template_x + 3 * 36 + 30, template_y)  # после трёх кнопок
        self.fix_scale_button.update_pos(template_x + 4 * 36 + 40, template_y)
        self.alpha_slider.update_pos(template_x, template_y + 56, 150, 10)
        self.scale_slider.update_pos(template_x, template_y + 90, 150, 10)

    def handle_events(self, event):
        for text_input in self.text_inputs:
            if text_input.handle_event(event):
                self.on_apply_size()

        action = self.size_toolbar.handle_event(event)
        if action and action in self.action_map:
            self.action_map[action]()

        action = self.toolbar.handle_event(event)
        if action and action in self.action_map:
            self.action_map[action]()

        self.zoom_slider.handle_event(event)

        action = self.template_toolbar.handle_event(event)
        if action in self.action_map:
            self.action_map[action]()

        # ToggleButton сам вызывает колбэк с состоянием
        self.toggle_template_button.handle_event(event)
        self.fix_scale_button.handle_event(event)

        self.alpha_slider.handle_event(event)
        self.scale_slider.handle_event(event)

    def draw(self, screen):
        for text_input in self.text_inputs:
            text_input.draw(screen)

        self.size_toolbar.draw(screen)
        self.toolbar.draw(screen)
        self.zoom_slider.draw(screen)

        screen.blit(self.font.render(self.lang.get("building_code"), True, COLORS['text']), (20, 40))
        screen.blit(self.font.render(self.lang.get("grid_size"), True, COLORS['text']), (230, 40))

        self.template_toolbar.draw(screen)
        self.toggle_template_button.draw(screen)
        self.fix_scale_button.draw(screen)
        self.alpha_slider.draw(screen)
        self.scale_slider.draw(screen)

        # Отрисовываем тултипы поверх всех элементов
        self.size_toolbar.draw_tooltips(screen)
        self.toolbar.draw_tooltips(screen)
        self.template_toolbar.draw_tooltips(screen)
        self.toggle_template_button.draw_tooltip(screen)
        self.fix_scale_button.draw_tooltip(screen)

    def set_fix_scale_state(self, state):
        self.fix_scale_button.set_state(state)

    def set_template_visibility_state(self, state):
        self.toggle_template_button.set_state(state)

    def get_building_code(self):
        return self.building_code_input.text

    def get_width(self):
        try:
            return int(self.width_input.text) if self.width_input.text else MIN_GRID_SIZE
        except ValueError:
            return MIN_GRID_SIZE

    def get_height(self):
        try:
            return int(self.height_input.text) if self.height_input.text else MIN_GRID_SIZE
        except ValueError:
            return MIN_GRID_SIZE

    def set_values(self, code, width, height):
        self.building_code_input.text = code
        self.width_input.text = str(width)
        self.height_input.text = str(height)

    def update_language(self, lang):
        """Обновляет все текстовые элементы интерфейса при смене языка."""
        self.lang = lang

        # Пересоздаём тулбары с новыми строками из lang
        size_icons = [
            ("icons/apply_size.svg", lang.get("apply_size"), "apply_size"),
            ("icons/generate_outline.svg", lang.get("generate_outline"), "generate_outline"),
        ]
        self.size_toolbar = Toolbar(self.font, size_icons)

        template_icons = [
            ("icons/load_template.svg", lang.get("load_template"), "load_template"),
            ("icons/fit_template.svg", lang.get("template_fit"), "template_fit"),
            ("icons/reset_template.svg", lang.get("template_reset"), "template_reset"),
        ]
        self.template_toolbar = Toolbar(self.font, template_icons)

        bottom_icons = [
            ("icons/clear.svg", lang.get("clear"), "clear"),
            ("icons/export_ini.svg", lang.get("export_ini"), "export_ini"),
            ("icons/save_image.svg", lang.get("save_image"), "save_image"),
            ("icons/load_ini.svg", lang.get("load_ini"), "load_ini"),
            ("icons/undo.svg", lang.get("undo"), "undo"),
            ("icons/redo.svg", lang.get("redo"), "redo"),
            ("icons/fit_to_screen.svg", lang.get("fit_to_screen"), "fit_to_screen"),
            ("icons/reset_zoom.svg", lang.get("z_desc"), "reset_zoom"),
            ("icons/toggle_projection.svg", lang.get("toggle_projection"), "toggle_projection"),
            ("icons/toggle_coords.svg", lang.get("toggle_coords"), "toggle_coords"),
            ("icons/reset_view.svg", lang.get("reset_view"), "reset_view"),
            ("icons/color_scheme.svg", lang.get("choose_color_scheme"), "change_color_scheme"),
            ("icons/language.svg", lang.get("choose_language"), "change_language"),
        ]
        self.toolbar = Toolbar(self.font, bottom_icons)

        # Сохраняем текущее состояние и позиции кнопок
        current_fix_state = self.fix_scale_button.state
        current_fix_x, current_fix_y = self.fix_scale_button.rect.topleft
        current_toggle_state = self.toggle_template_button.state
        current_toggle_x, current_toggle_y = self.toggle_template_button.rect.topleft

        # Пересоздаём ToggleButton'ы с новыми подсказками
        self.toggle_template_button = ToggleButton(
            current_toggle_x, current_toggle_y, 36,
            "icons/toggle_template.svg", "icons/toggle_template.svg",
            lang.get("template_hide"), lang.get("template_show"),
            self.font,
            self.on_toggle_template,
            initial_state=current_toggle_state,
            icon_scale=0.8
        )

        self.fix_scale_button = ToggleButton(
            current_fix_x, current_fix_y, 36,
            "icons/link.svg", "icons/unlink.svg",
            lang.get("fix_template_scale_on"), lang.get("fix_template_scale_off"),
            self.font,
            self.on_toggle_fix_template_scale,
            initial_state=current_fix_state,
            icon_scale=0.8
        )

        # Обновляем подписи слайдеров
        self.alpha_slider.set_label(lang.get("template_alpha"))
        self.scale_slider.set_label(lang.get("template_scale"))
        self.zoom_slider.set_label(lang.get("zoom"))