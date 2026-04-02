# Ares Foundation Generator +

[![Python Versions](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.5.2-green.svg)](https://www.pygame.org/)
[![NumPy](https://img.shields.io/badge/numpy-1.24+-orange.svg)](https://numpy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🇬🇧 [English](README.en.md) | 🇷🇺 [Русский](README.ru.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇹🇼 [繁體中文](README.zh-TW.md)

**Ares Foundation Generator +** 是一款桌面应用程序，用于创建和编辑游戏关卡（例如 ARES）的建筑地基。它提供正交和等轴测投影、模板叠加、撤销/重做以及导出为 INI/图像格式。

![截图占位符](screenshot.png)

## 功能

- 交互式网格编辑（左键添加，右键移除）
- 轮廓模式（按住 `Ctrl` 编辑地基轮廓）
- 根据填充单元格自动生成轮廓
- 正交和等轴测投影
- 模板图像叠加（PNG、JPG 等），支持透明度和缩放
- 撤销/重做（Ctrl+Z / Ctrl+Y）
- 将地基数据导出为 INI 文件（可直接用于 ARES）
- 将正交和等轴测视图导出为 PNG 图像
- 加载现有 INI 文件（拖放或通过按钮）
- 可调整网格大小（5x5 至 50x50）
- 配色方案和多语言支持（English, Русский, 简体中文, 繁體中文）
- 完全可调整大小的窗口，支持缩放和平移

## 环境要求

- Python 3.8+
- Pygame
- NumPy
- Tkinter（通常随 Python 一起提供）

## 安装与运行

1. 克隆仓库：
   ``` bash
   git clone https://github.com/YoVVassup/ares-foundation-generator-plus.git
   cd ares-foundation-generator-plus
   ```

2. （可选）创建并激活虚拟环境：
   ``` bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. 安装依赖：
   ``` bash
   pip install pygame numpy zstandard
   ```

4. 运行应用程序：
   ``` bash
   python main.py
   ```

## 构建可执行文件（Windows）

提供了一个 PowerShell 构建脚本 `Run.ps1`。它使用 **Nuitka** 将程序编译为独立的 `.exe` 文件。

- 安装 Nuitka：`pip install nuitka`
- 在 PowerShell 中运行 `.\Run.ps1`（可能需要调整执行策略：`Set-ExecutionPolicy RemoteSigned -Scope Process`）

输出将位于 `Ares Foundation Generator Plus` 文件夹中。

## 基本用法

- **鼠标左键** – 填充单元格
- **鼠标右键** – 清空单元格
- **Ctrl + 左/右键** – 编辑轮廓单元格
- **鼠标中键** – 平移视图
- **Ctrl + 鼠标中键** – 平移模板
- **鼠标滚轮** – 缩放网格
- **Ctrl + 鼠标滚轮** – 缩放模板
- **G** – 根据填充单元格生成轮廓
- **C** – 清空整个网格
- **L** – 加载 INI 文件
- **Ctrl+E** – 导出为 INI
- **Ctrl+Shift+S** – 保存为图像
- **F** – 使网格适应屏幕
- **P** – 切换投影
- **O** – 切换坐标显示
- **R** – 重置视图
- **Z** – 重置缩放
- **Ctrl+Z / Ctrl+Y** – 撤销 / 重做
- **F1** – 显示/隐藏帮助

## 文件结构

- `main.py` – 入口点，主循环，事件处理
- `grid.py` – 网格数据模型和轮廓生成
- `renderer.py` – 绘制正交/等轴测视图
- `ui.py` – UI 组件（按钮、滑块、对话框）
- `commands.py` – 命令模式，实现撤销/重做
- `localization.py` – 多语言支持
- `settings.py` – 持久化设置（INI）
- `constants.py` – 全局常量和配色方案
- `utils.py` – 路径辅助函数
- `language_*.ini` – 翻译文件
- `icons/` – 图标文件（SVG/PNG）
- `Unifont.ttf` – 字体文件（可选）

## 许可证

本项目采用 MIT 许可证 – 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。