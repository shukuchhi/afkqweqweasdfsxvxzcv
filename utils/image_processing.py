import cv2
import os
import numpy as np

def find_template(screenshot_path, template_path, threshold=0.7):
    # Получаем только имя файла из полного пути (например, '1game_3.png')
    file_name = os.path.basename(template_path)
    
    # Список файлов, для которых нужен высокий порог
    high_threshold_files = ["gamebot2win.png", "interface_3.png", "1game_3.png"]

    if file_name in high_threshold_files:
        threshold = 0.8
        print(f"High threshold (0.8) applied for {file_name}")

    # Дальше твой код...
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if screenshot is None:
        raise Exception(f"Could not load screenshot: {screenshot_path}")
    if template is None:
        raise Exception(f"Could not load template: {template_path}")
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    print(f"Template matching confidence for {template_path}: {max_val}")
    return max_val >= threshold