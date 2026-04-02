import os
import sys

def get_app_path():
    """
    Возвращает путь к каталогу, где находится исполняемый файл (или скрипт в режиме разработки).
    Используется для файлов, которые должны лежать рядом с .exe (языки, настройки).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

def get_resource_path(relative_path):
    """
    Возвращает путь к ресурсу, встроенному в .exe (для onefile) или лежащему рядом (для standalone).
    Используется для иконок, шрифтов, PNG-кнопок.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(get_app_path(), relative_path)