import numpy as np

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = np.zeros((height, width), dtype=bool)
        self.outline = np.zeros((height, width), dtype=bool)
        self.generated_outline = []

    def resize(self, new_width, new_height):
        new_cells = np.zeros((new_height, new_width), dtype=bool)
        new_outline = np.zeros((new_height, new_width), dtype=bool)
        min_h = min(self.height, new_height)
        min_w = min(self.width, new_width)
        new_cells[:min_h, :min_w] = self.cells[:min_h, :min_w]
        new_outline[:min_h, :min_w] = self.outline[:min_h, :min_w]
        self.cells = new_cells
        self.outline = new_outline
        self.width = new_width
        self.height = new_height
        self.generated_outline = []

    def set_cell(self, x, y, value, outline_mode=False):
        if 0 <= x < self.width and 0 <= y < self.height:
            if outline_mode:
                self.outline[y, x] = value
                if value:
                    self.generated_outline = []
            else:
                self.cells[y, x] = value

    def clear(self):
        self.cells.fill(False)
        self.outline.fill(False)
        self.generated_outline = []

    def generate_outline(self):
        """Генерирует контур заполненной области. Возвращает список координат (x, y) ячеек контура."""
        if np.sum(self.cells) == 0:
            return []

        h, w = self.height, self.width
        cells = self.cells

        # Поиск стартовой граничной ячейки
        start = None
        for y in range(h):
            for x in range(w):
                if cells[y, x]:
                    # Проверяем, является ли ячейка граничной (имеет пустого соседа или край)
                    for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < w and 0 <= ny < h) or not cells[ny, nx]:
                            start = (x, y)
                            break
                    if start:
                        break
            if start:
                break

        # Если не нашли граничной ячейки, значит все ячейки заполнены (сетка полностью заполнена)
        if start is None:
            # Возвращаем все ячейки на границе сетки
            outline = []
            for y in range(h):
                for x in range(w):
                    if cells[y, x] and (x == 0 or x == w - 1 or y == 0 or y == h - 1):
                        outline.append((x, y))
            return outline

        # Направления: 0=вверх, 1=вправо, 2=вниз, 3=влево
        dx = [0, 1, 0, -1]
        dy = [-1, 0, 1, 0]

        def is_filled(x, y):
            return 0 <= x < w and 0 <= y < h and cells[y, x]

        # Находим начальное направление (первое, где сосед пуст)
        start_dir = 0
        for d in range(4):
            nx, ny = start[0] + dx[d], start[1] + dy[d]
            if not is_filled(nx, ny):
                start_dir = d
                break

        outline = []
        x, y = start
        direction = start_dir
        max_iter = 4 * w * h + 10  # Защита от зацикливания
        iter_count = 0

        while True:
            iter_count += 1
            if iter_count > max_iter:
                print("Warning: outline generation exceeded max iterations, possible loop")
                break

            outline.append((x, y))

            left_dir = (direction + 3) % 4
            nx, ny = x + dx[left_dir], y + dy[left_dir]
            if is_filled(nx, ny):
                x, y = nx, ny
                direction = left_dir
            else:
                nx, ny = x + dx[direction], y + dy[direction]
                if is_filled(nx, ny):
                    x, y = nx, ny
                else:
                    right_dir = (direction + 1) % 4
                    nx, ny = x + dx[right_dir], y + dy[right_dir]
                    if is_filled(nx, ny):
                        x, y = nx, ny
                        direction = right_dir
                    else:
                        back_dir = (direction + 2) % 4
                        nx, ny = x + dx[back_dir], y + dy[back_dir]
                        if is_filled(nx, ny):
                            x, y = nx, ny
                            direction = back_dir
                        else:
                            break

            if (x, y) == start and direction == start_dir:
                break

        return outline

    def apply_generated_outline(self):
        self.generated_outline = self.generate_outline()
        self.outline.fill(False)
        for x, y in self.generated_outline:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.outline[y, x] = True

    def is_outline_closed(self):
        if np.sum(self.outline) < 2:
            return True
        if self.generated_outline:
            return True
        points = np.argwhere(self.outline)
        for y, x in points:
            neighbors = 0
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                if 0 <= x + dx < self.width and 0 <= y + dy < self.height and self.outline[y + dy, x + dx]:
                    neighbors += 1
            if neighbors < 2:
                return False
        return True

    def get_filled_cells(self):
        return np.argwhere(self.cells)

    def get_outline_cells(self):
        return np.argwhere(self.outline)