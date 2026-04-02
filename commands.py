import numpy as np

class Command:
    """Базовый класс команды."""
    def execute(self):
        pass
    def undo(self):
        pass


class CellCommand(Command):
    """Изменение одной ячейки (обычной или контурной)."""
    def __init__(self, grid, x, y, old_value, new_value, outline_mode):
        self.grid = grid
        self.x = x
        self.y = y
        self.old_value = old_value
        self.new_value = new_value
        self.outline_mode = outline_mode

    def execute(self):
        if self.outline_mode:
            self.grid.outline[self.y, self.x] = self.new_value
        else:
            self.grid.cells[self.y, self.x] = self.new_value

    def undo(self):
        if self.outline_mode:
            self.grid.outline[self.y, self.x] = self.old_value
        else:
            self.grid.cells[self.y, self.x] = self.old_value


class MultiCommand(Command):
    """Команда, состоящая из нескольких подкоманд (например, массовое изменение)."""
    def __init__(self, commands):
        self.commands = commands

    def execute(self):
        for cmd in self.commands:
            cmd.execute()

    def undo(self):
        for cmd in reversed(self.commands):
            cmd.undo()


class GridSnapshotCommand(Command):
    """Команда, сохраняющая полное состояние сетки (для очистки, изменения размера, загрузки и т.п.)."""
    def __init__(self, grid, old_cells, old_outline, old_generated_outline, new_cells, new_outline,
                 new_generated_outline):
        self.grid = grid
        self.old_cells = old_cells.copy()
        self.old_outline = old_outline.copy()
        self.old_generated_outline = old_generated_outline[:]
        self.new_cells = new_cells.copy()
        self.new_outline = new_outline.copy()
        self.new_generated_outline = new_generated_outline[:]
        self.old_width = old_cells.shape[1]
        self.old_height = old_cells.shape[0]
        self.new_width = new_cells.shape[1]
        self.new_height = new_cells.shape[0]

    def execute(self):
        self.grid.cells = self.new_cells
        self.grid.outline = self.new_outline
        self.grid.generated_outline = self.new_generated_outline[:]
        self.grid.width = self.new_width
        self.grid.height = self.new_height

    def undo(self):
        self.grid.cells = self.old_cells
        self.grid.outline = self.old_outline
        self.grid.generated_outline = self.old_generated_outline[:]
        self.grid.width = self.old_width
        self.grid.height = self.old_height