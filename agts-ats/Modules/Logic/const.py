# X - ВЫСОТА, горизонталь, направлен вправо
# Y - ШИРИНА, вертикаль, направлен вверх
# направление по умолчанию - по X
# Повороты: по часовой - отрицательный, против часовой - положительный

# Нотация для прямоугольников (любых): ЛН ПН ПВ ЛВ (с левого нижнего по кругу против часовой стрелки)

# Все размеры в мм (либо безразмерные)

# Поле 9х9 клеток
FIELD_WIDTH_CELLS = 9
FIELD_HEIGHT_CELLS = 9

# Размер ячейки поля в пикселях (400 мм)
FIELD_CELL_SIZE = 400

# Масштаб для отображения в окне (1 пиксель = 5 мм)
FIELD_TO_WINDOW_SCALE = 0.2

# Отступы поля от края окна в пикселях (для центрирования)
FIELD_OFFSET_X = round(FIELD_CELL_SIZE * FIELD_TO_WINDOW_SCALE)
FIELD_OFFSET_Y = round(FIELD_CELL_SIZE * FIELD_TO_WINDOW_SCALE)

# Размер окна в пикселях (с учётом отступов)
WINDOW_WIDTH = round(FIELD_CELL_SIZE * FIELD_WIDTH_CELLS * FIELD_TO_WINDOW_SCALE + FIELD_OFFSET_X * 2)
WINDOW_HEIGHT = round(FIELD_CELL_SIZE * FIELD_HEIGHT_CELLS * FIELD_TO_WINDOW_SCALE + FIELD_OFFSET_Y * 2)
WINDOW_TITLE = "LCT_ATS"

# Нумерация ячеек начинается с левой нижней (1), идёт вправо и переносится по строкам (НЕ ЗМЕЙКОЙ, СО СДВИГОМ)
FIELD_SCHEMA = {
    "roads": [
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        22,
        26,
        27,
        29,
        31,
        35,
        38,
        40,
        44,
        47,
        49,
        50,
        51,
        52,
        53,
        56,
        58,
        62,
        65,
        66,
        67,
        68,
        69,
        71,
        75,
        76,
        78,
        79,
        80,
    ],
    "zones": {
        "low_speed": [62, 71, 31, 40],
        "pedestrian": [56, 15],
        "start_finish": [19],
    },
    "cyber_triggers": {
        "CybP_01": [11, 29],
        "CybP_06": [62, 71, 31, 40],
    },
    "obstacles": [],
    "markers": [1, 5, 9, 37, 41, 45, 73, 77, 81],
}


def get_zone(zone):
    return FIELD_SCHEMA["zones"].get(zone, None)


def get_trigger(trigger):
    return FIELD_SCHEMA["cyber_triggers"].get(trigger, None)


ZONE_COLORS = {
    "road": (36, 35, 40, 1),
    "low_speed": (50, 70, 200, 150),
    "start_finish": (253, 127, 0, 150),
    "pedestrian": (254, 102, 254, 140),
    "obstacles": (140, 140, 140, 100),
    "markers": (140, 140, 140, 100),
    None: (80, 80, 80, 100),
}

ROBOT_WIDTH = 210
ROBOT_HEIGHT = 260
ROBOT_WHEEL_OFFSET_X = 165
ROBOT_WHEEL_OFFSET_Y = 165
ROBOT_WHEEL_WIDTH = 45
ROBOT_WHEEL_RADIUS = 98

NUM_ROBOTS = 5

# КОНСТАНТЫ ДЛЯ ЗАЕЗДОВ

MISSION_TIME_LIMIT = 15 * 60
CLEANING_TIME_LIMIT = 5
AP_REBOOT_TIME = 5
