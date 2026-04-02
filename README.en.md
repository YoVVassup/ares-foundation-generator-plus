# Ares Foundation Generator +

[![Python Versions](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.5.2-green.svg)](https://www.pygame.org/)
[![NumPy](https://img.shields.io/badge/numpy-1.24+-orange.svg)](https://numpy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🇬🇧 [English](README.en.md) | 🇷🇺 [Русский](README.ru.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇹🇼 [繁體中文](README.zh-TW.md)

**Ares Foundation Generator +** is a desktop application for creating and editing building foundations for game levels (e.g., ARES). It provides both orthogonal and isometric projections, template overlay, undo/redo, and export to INI/image formats.

![Screenshot placeholder](screenshot.png)

## Features

- Interactive grid editing (left click to add, right click to remove)
- Outline mode (hold `Ctrl` to edit the foundation outline)
- Automatic outline generation from filled cells
- Orthogonal and isometric projections
- Template image overlay (PNG, JPG, etc.) with opacity and scaling
- Undo/Redo (Ctrl+Z / Ctrl+Y)
- Export foundation data to INI file (ready for ARES)
- Export orthogonal and isometric views as PNG images
- Load existing INI files (drag & drop or via button)
- Adjustable grid size (5x5 to 50x50)
- Color schemes and multi-language support (English, Русский, 简体中文, 繁體中文)
- Fully resizable window with zoom and pan

## Requirements

- Python 3.8+
- Pygame
- NumPy
- Tkinter (usually included with Python)

## Installation and Running

1. Clone the repository:
   ``` bash
   git clone https://github.com/YoVVassup/ares-foundation-generator-plus.git
   cd ares-foundation-generator-plus
   ```

2. (Optional) Create and activate a virtual environment:
   ``` bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ``` bash
   pip install pygame numpy zstandard
   ```

4. Run the application:
   ``` bash
   python main.py
   ```

## Building Executable (Windows)

A PowerShell build script `Run.ps1` is provided. It uses **Nuitka** to compile the program into a standalone `.exe` file.

- Install Nuitka: `pip install nuitka`
- Run `.\Run.ps1` in PowerShell (may require execution policy adjustment: `Set-ExecutionPolicy RemoteSigned -Scope Process`)

The output will be in the `Ares Foundation Generator Plus` folder.

## Basic Usage

- **Left Mouse Button** – fill a cell
- **Right Mouse Button** – empty a cell
- **Ctrl + Left/Right** – edit outline cells
- **Middle Mouse Button** – pan view
- **Ctrl + Middle Mouse** – pan template
- **Mouse Wheel** – zoom grid
- **Ctrl + Mouse Wheel** – zoom template
- **G** – generate outline from filled cells
- **C** – clear entire grid
- **L** – load INI file
- **Ctrl+E** – export to INI
- **Ctrl+Shift+S** – save as images
- **F** – fit grid to screen
- **P** – toggle projection
- **O** – toggle coordinates display
- **R** – reset view
- **Z** – reset zoom
- **Ctrl+Z / Ctrl+Y** – undo / redo
- **F1** – show/hide help

## File Structure

- `main.py` – entry point, main loop, event handling
- `grid.py` – grid data model and outline generation
- `renderer.py` – drawing orthogonal/isometric views
- `ui.py` – UI components (buttons, sliders, dialogs)
- `commands.py` – command pattern for undo/redo
- `localization.py` – multi-language support
- `settings.py` – persistent settings (INI)
- `constants.py` – global constants and color schemes
- `utils.py` – helper functions for paths
- `language_*.ini` – translation files
- `icons/` – icon files (SVG/PNG)
- `Unifont.ttf` – font file (optional)

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.