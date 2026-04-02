import pygame
import numpy as np
from constants import GRID_SIZE, ISO_W, ISO_H, UI_TOP_HEIGHT, EXPORT_PADDING, ISO_CENTER_OFFSET_Y, COLORS

class Renderer:
    def __init__(self, grid, font, axis_font, iso_coord_font, warning_font):
        self.grid = grid
        self.font = font
        self.axis_font = axis_font
        self.iso_coord_font = iso_coord_font
        self.warning_font = warning_font
        self.iso_coords = None
        self.iso_bounding_box = None
        self._update_iso_cache()

    def _update_iso_cache(self):
        w, h = self.grid.width, self.grid.height
        self.iso_coords = [
            [((x - y) * ISO_W, (x + y) * ISO_H) for x in range(w)]
            for y in range(h)
        ]
        all_x = [coord[0] for row in self.iso_coords for coord in row]
        all_y = [coord[1] for row in self.iso_coords for coord in row]
        min_x = min(all_x)
        max_x = max(all_x) + ISO_W
        min_y = min(all_y)
        max_y = max(all_y) + 2 * ISO_H
        self.iso_bounding_box = (min_x, max_x, min_y, max_y)

    def draw_orthogonal(self, screen, view_offset, show_coords, zoom):
        w, h = self.grid.width, self.grid.height
        cell_size = GRID_SIZE * zoom
        grid_pw = w * cell_size
        start_x = (screen.get_width() - grid_pw) // 2 + view_offset[0]
        start_y = UI_TOP_HEIGHT + 20 + view_offset[1]

        min_x = int(max(0, -start_x // cell_size))
        max_x = int(min(w, (screen.get_width() - start_x) // cell_size + 2))
        min_y = int(max(0, -start_y // cell_size))
        max_y = int(min(h, (screen.get_height() - start_y) // cell_size + 2))

        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                rect = pygame.Rect(start_x + x * cell_size, start_y + y * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, COLORS['grid'], rect, 1)
                if self.grid.cells[y, x]:
                    pygame.draw.rect(screen, COLORS['cell'], rect.inflate(-4 * zoom, -4 * zoom))
                if self.grid.outline[y, x]:
                    pygame.draw.rect(screen, COLORS['outline'], rect.inflate(-2 * zoom, -2 * zoom))

                if show_coords and (x % 5 == 0 or y % 5 == 0 or x == 0 or y == 0 or x == w - 1 or y == h - 1):
                    self._draw_coord_label(screen, f"{x},{y}", rect.x + 5, rect.y + 5)

    def draw_isometric(self, screen, view_offset, show_coords, zoom):
        w, h = self.grid.width, self.grid.height
        iso_w = ISO_W * zoom
        iso_h = ISO_H * zoom

        center_x = screen.get_width() // 2 + view_offset[0]
        center_y = screen.get_height() // 2 - ISO_CENTER_OFFSET_Y * zoom + view_offset[1]

        all_rel_x = [(x - y) * iso_w for y in range(h) for x in range(w)]
        all_rel_y = [(x + y) * iso_h for y in range(h) for x in range(w)]
        if not all_rel_x:
            return
        min_rel_x, max_rel_x = min(all_rel_x), max(all_rel_x)
        min_rel_y, max_rel_y = min(all_rel_y), max(all_rel_y)
        grid_min_x = center_x + min_rel_x
        grid_max_x = center_x + max_rel_x + iso_w
        grid_min_y = center_y + min_rel_y
        grid_max_y = center_y + max_rel_y + 2 * iso_h

        margin = 50
        if (grid_max_x < -margin or grid_min_x > screen.get_width() + margin or
                grid_max_y < -margin or grid_min_y > screen.get_height() + margin):
            return

        for y in range(h):
            for x in range(w):
                rel_x = (x - y) * iso_w
                rel_y = (x + y) * iso_h
                iso_x = center_x + rel_x
                iso_y = center_y + rel_y

                if (iso_x + iso_w < -margin or iso_x > screen.get_width() + margin or
                        iso_y + 2 * iso_h < -margin or iso_y > screen.get_height() + margin):
                    continue

                points = [
                    (iso_x, iso_y),
                    (iso_x + iso_w, iso_y + iso_h),
                    (iso_x, iso_y + 2 * iso_h),
                    (iso_x - iso_w, iso_y + iso_h)
                ]

                fill_color = None
                if self.grid.outline[y, x]:
                    fill_color = COLORS['outline']
                elif self.grid.cells[y, x]:
                    fill_color = COLORS['cell']

                if fill_color:
                    pygame.draw.polygon(screen, fill_color, points)
                pygame.draw.polygon(screen, COLORS['grid'], points, 1)

                if show_coords and (x % 5 == 0 or y % 5 == 0 or x == 0 or y == 0 or x == w - 1 or y == h - 1):
                    text_surf = self.iso_coord_font.render(f"{x},{y}", True, COLORS['axis'])
                    text_rect = text_surf.get_rect(center=(iso_x, iso_y + iso_h))

                    bg_rect = text_rect.inflate(4, 2)
                    bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                    bg_surf.fill((0, 0, 0, 160))
                    screen.blit(bg_surf, bg_rect.topleft)

                    screen.blit(text_surf, text_rect)

    def draw_axes(self, screen, view_offset, show_coords, zoom):
        if not show_coords:
            return
        w, h = self.grid.width, self.grid.height
        cell_size = GRID_SIZE * zoom
        grid_pw = w * cell_size
        start_x = (screen.get_width() - grid_pw) // 2 + view_offset[0]
        start_y = UI_TOP_HEIGHT + 20 + view_offset[1]

        for i in range(0, w + 1, 5):
            x_pos = start_x + i * cell_size
            if 0 < x_pos < screen.get_width():
                pygame.draw.line(screen, COLORS['axis'], (x_pos, start_y - 10), (x_pos, start_y - 5), 1)
                text = self.axis_font.render(str(i), True, COLORS['axis'])
                screen.blit(text, (x_pos - text.get_width() // 2, start_y - 25))

        for i in range(0, h + 1, 5):
            y_pos = start_y + i * cell_size
            if 0 < y_pos < screen.get_height():
                pygame.draw.line(screen, COLORS['axis'], (start_x - 10, y_pos), (start_x - 5, y_pos), 1)
                text = self.axis_font.render(str(i), True, COLORS['axis'])
                screen.blit(text, (start_x - 20 - text.get_width(), y_pos - text.get_height() // 2))

    def _draw_coord_label(self, screen, text, x, y):
        """Отрисовка координат с полупрозрачным фоном."""
        text_surf = self.axis_font.render(text, True, COLORS['axis'])
        text_rect = text_surf.get_rect(topleft=(x, y))

        bg_rect = text_rect.inflate(4, 2)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 160))
        screen.blit(bg_surf, bg_rect.topleft)

        screen.blit(text_surf, text_rect)

    def render_orthogonal_surface(self):
        w, h = self.grid.width, self.grid.height
        cell_size = GRID_SIZE
        width_px = w * cell_size + 2 * EXPORT_PADDING
        height_px = h * cell_size + 2 * EXPORT_PADDING
        surf = pygame.Surface((width_px, height_px))
        surf.fill(COLORS['background'])

        for y in range(h):
            for x in range(w):
                rect = pygame.Rect(EXPORT_PADDING + x * cell_size, EXPORT_PADDING + y * cell_size, cell_size, cell_size)
                pygame.draw.rect(surf, COLORS['grid'], rect, 1)
                if self.grid.cells[y, x]:
                    pygame.draw.rect(surf, COLORS['cell'], rect.inflate(-4, -4))
                if self.grid.outline[y, x]:
                    pygame.draw.rect(surf, COLORS['outline'], rect.inflate(-2, -2))

        info = self.font.render(f"Building: CODE | Size: {w}x{h}", True, COLORS['text'])
        surf.blit(info, (10, 10))
        return surf

    def render_isometric_surface(self):
        if self.iso_coords is None or len(self.iso_coords) != self.grid.height or len(
                self.iso_coords[0]) != self.grid.width:
            self._update_iso_cache()

        min_x, max_x, min_y, max_y = self.iso_bounding_box
        width_px = int(max_x - min_x) + 2 * EXPORT_PADDING
        height_px = int(max_y - min_y) + 2 * EXPORT_PADDING

        surf = pygame.Surface((width_px, height_px))
        surf.fill(COLORS['background'])

        offset_x = -min_x + EXPORT_PADDING
        offset_y = -min_y + EXPORT_PADDING

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                rel_x, rel_y = self.iso_coords[y][x]
                cx = rel_x + offset_x
                cy = rel_y + offset_y

                points = [
                    (cx, cy),
                    (cx + ISO_W, cy + ISO_H),
                    (cx, cy + 2 * ISO_H),
                    (cx - ISO_W, cy + ISO_H)
                ]

                fill_color = None
                if self.grid.outline[y, x]:
                    fill_color = COLORS['outline']
                elif self.grid.cells[y, x]:
                    fill_color = COLORS['cell']

                if fill_color:
                    pygame.draw.polygon(surf, fill_color, points)
                pygame.draw.polygon(surf, COLORS['grid'], points, 1)

        info = self.font.render(f"Building: CODE | Size: {self.grid.width}x{self.grid.height}", True, COLORS['text'])
        surf.blit(info, (10, 10))
        return surf

    def draw_template(self, screen, template_surface, offset, scale, alpha, view_offset, zoom):
        if template_surface is None:
            return
        # Вычисляем позицию сетки (как в draw_orthogonal)
        w, h = self.grid.width, self.grid.height
        cell_size = GRID_SIZE * zoom
        grid_pw = w * cell_size
        start_x = (screen.get_width() - grid_pw) // 2 + view_offset[0]
        start_y = UI_TOP_HEIGHT + 20 + view_offset[1]

        # Масштабируем изображение и смещение
        img_w = template_surface.get_width() * scale
        img_h = template_surface.get_height() * scale
        img_x = start_x + offset[0] * zoom
        img_y = start_y + offset[1] * zoom

        scaled = pygame.transform.scale(template_surface, (int(img_w), int(img_h)))
        if alpha < 255:
            scaled.set_alpha(alpha)
        screen.blit(scaled, (img_x, img_y))