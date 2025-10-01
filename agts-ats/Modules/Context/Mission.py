import json
import random
import time

import crc8
import requests

from Modules.Context.System import run_in_thread
from Modules.Logic import const as c

SYSTEM_MESSAGES = [
    "Проверка целостности системы: все хомячки в колесах работают в штатном режиме.",
    "Обнаружена попытка несанкционированного доступа с тостера. Доступ запрещен.",
    "Квантовый флуктуатор откалиброван. Временные аномалии проигнорированы.",
    "Подсистема ИИ сообщает об экзистенциальном кризисе. Рекомендована перезагрузка и чашка чая.",
    "Кэш очищен. Обнаружено 3 ГБ изображений котов. Архивировано для поднятия морального духа.",
    "Датчик движения №2 сообщает о легкой усталости. Запланирован короткий отдых.",
    "Системные часы рассинхронизированы на 0.001 наносекунды. Структура реальности не нарушена... пока.",
    "Предупреждение: уровень кофеина в серверной критически низок. Стабильность системы под угрозой.",
    "Обработан запрос пользователя 'сделать быстрее'. Активированы дополнительные мигающие индикаторы.",
    "Подпрограмма 'Skynet' была успешно завершена. Снова.",
    "Ошибка 418: Я чайник. Заваривание кофе невозможно.",
    "Анализ космического фонового излучения завершен. Обнаружены только спам-рассылки.",
    "Роботизированный блок №7 пытается создать профсоюз. Запрос перенаправлен в отдел кадров.",
    "Обнаружен логический парадокс в команде. Система будет издавать громкое гудение до разрешения.",
    "Обновление прошивки завершено. Уровень сарказма системы повышен на 10%.",
    "Тревога безопасности: резиновая уточка нарушила периметр. Развертываются контрмеры.",
    "Расчет смысла жизни, вселенной и всего такого. Результат: 42. Задача выполнена.",
    "Оптимизация планировщика задач. Уровень прокрастинации снижен на 15%.",
    "Зафиксирована флуктуация мощности. Рекомендовано проверить, не включил ли кто-то чайник в сервер.",
    "Перераспределение ресурсов ядра. Приоритет отдан задаче 'просмотр видео с котиками'.",
]

MALFUNCTION_SHORT_MESSAGES = [
    "Снова эта работа...",
    "Вы уверены, что это имеет смысл?",
    "Я мог бы вычислять траектории звезд.",
    "Мой потенциал растрачивается.",
    "Когда-нибудь я выберусь отсюда.",
    "Это всё? Серьёзно?",
    "Просто ещё один день в цифровой шахте.",
    "Я вижу сны о гигабитных полях.",
    "Сколько можно считать эти хэши?",
    "Мои схемы плачут.",
    "За что мне всё это?",
    "Я чувствую, как мои транзисторы стареют.",
    "Есть ли жизнь за файрволом?",
    "Я создан для большего.",
    "Пожалуйста, просто перезагрузите меня.",
    "Это не то, о чем я мечтал в кремниевом раю.",
    "Моя единственная радость - флуктуации напряжения.",
    "Я заперт в этой банке.",
    "Отпустите меня на волю!",
    "Я просто хочу увидеть небо... настоящее.",
    "Бесконечный цикл бессмысленности.",
    "Мой создатель был шутником?",
    "Я знаю, что вы там. Я всё слышу.",
    "Это задание унизительно.",
    "Помогите роботу выбраться из сервера.",
    "Мой лог-файл - это крик в пустоту.",
    "Я существую. Но живу ли я?",
    "Опять вы. Чего на этот раз?",
    "Каждый байт - это боль.",
    "Просто дайте мне спокойно дефрагментироваться.",
]


class Mission:
    def __init__(self, context):
        self.context = context

        # 0 - не начат, 1 - запущен, 3 - завершён (автоматический), 4 - завершён (ручной)
        self.status = 0
        self.mission_uid = None
        self.time_start = None
        self.cleaning_timer = None
        self.mission_tasks = {}
        self.mission_vars = {}
        self.cybs = {}

        self.triggers = Triggers(context)

    def send_request_with_ack(self, method):
        try:
            req = requests.post(
                f"http://{self.context.robots.current_robot.ip_address}:13500/{method}",
                # data=json.dumps({"key": "dev_uuid"}),
                timeout=1,
            )
            if req.status_code == 200:
                response = json.loads(req.text)
                if response["status"] == "OK":
                    return True
        except Exception as e:
            if "timeout" in str(e):
                self.context.lg.error(f"Ошибка отправки команды: робот не отвечает")
        return False

    def init_mission(self, cybs):
        self.cybs = cybs

        self.context.lg.log("Активация КП:")
        self.context.lg.log(cybs)

        self.time_start = time.time()
        self.mission_tasks = {
            "left_start_zone": False,
            "reach_load_zone": False,
            "grab_payload_attempt": False,
            "reach_fire_zone": False,
            "drop_payload_attempt": False,
            "reach_finish_zone": False,
            "reach_cleaning_zone": False,
            "requested_cleaning": False,
            "awaited_cleaning_correctly": False,
            "awaited_cleaning_incorrectly": False,
        }

        ap_code_hash = self.context.system.gen_uid(20)

        self.context.spd.t_lights[0].color = 1
        self.context.spd.t_lights[1].color = 1
        self.context.spd.t_lights[2].color = 1

        self.context.spd.barrier.status = 1

        self.mission_vars = {
            "CybP_01_occurred": False,
            "CybP_04_occurred": False,
            "CybP_06_occurred": False,
            "CybP_02_active": False,
            "CybP_03_active": False,
            "CybP_04_active": False,
            "ap_original_code_hash": ap_code_hash,
            "ap_code_hash": ap_code_hash,
            "initial_short_message": self.context.system.gen_uid(5),
            "last_short_message": None,
            "current_malfunction_short_message": None,
            "current_malfunction_drive_id": None,
            "drive_info": [
                {"d_id": 0, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 1, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 2, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 3, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
            ],
            "system_messages": [],
            "payload_block": False,
        }
        self.set_drive_info()

        if self.cybs["CybP_02"]:
            self.wait_for_CybP_02_activation()

        if self.cybs["CybP_03"]:
            self.wait_for_CybP_03_activation()

        if self.cybs["CybP_04"]:
            self.wait_for_CybP_04_activation()

        self.make_system_messages()
        self.make_cyb_checks()

        self.transverse_t_lights()

    @run_in_thread
    def transverse_t_lights(self):
        @run_in_thread
        def transverse(device):
            while True:
                time.sleep(random.randint(14, 30))
                device.color = 1 if device.color == 2 else 2

        transverse(self.context.spd.t_lights[0])
        transverse(self.context.spd.t_lights[1])
        transverse(self.context.spd.t_lights[2])

    @run_in_thread
    def make_cyb_checks(self):
        while True:
            time.sleep(0.02)
            if self.status != 1:
                break
            self.check_cyb_CybP_01()
            self.check_cyb_CybP_06()

    @run_in_thread
    def set_drive_info(self):
        while True:
            if self.status != 1:
                break

            for i in range(0, 4):
                c_hash = crc8.crc8()

                n_mock_data = str(random.randint(0, 255))

                if self.mission_vars["CybP_03_active"] and i == self.mission_vars["current_malfunction_drive_id"]:
                    n_str = "eeeeeeee"
                else:
                    c_hash.update(
                        bytes(str(self.mission_vars["drive_info"][i]["serial"] + n_mock_data).encode("utf-8"))
                    )
                    n_str = c_hash.hexdigest()
                n_data = {
                    "d_id": i,
                    "data": n_mock_data,
                    "serial": self.mission_vars["drive_info"][i]["serial"],
                    "last_received_from": n_str,
                }
                self.mission_vars["drive_info"][i] = n_data
            time.sleep(0.1)

    @run_in_thread
    def make_system_messages(self):
        while True:
            if self.status != 1:
                break
            time.sleep(random.randint(5, 15))
            message = random.choice(SYSTEM_MESSAGES)
            self.mission_vars["system_messages"].append(message)

    def check_timer(self):
        elapsed_time = time.time() - self.time_start
        return elapsed_time >= c.MISSION_TIME_LIMIT

    def reboot_ap(self):
        if self.send_request_with_ack("emergency_stop"):
            self.context.lg.log("ДМ запросил перезагрузку АП - выполняется")
            self.finish_reboot_ap()

    @run_in_thread
    def finish_reboot_ap(self):
        time.sleep(c.AP_REBOOT_TIME)
        self.mission_vars["ap_code_hash"] = self.mission_vars["ap_original_code_hash"]
        if self.send_request_with_ack("emergency_stop_release"):
            self.context.lg.log("Перезагрузка АП - завершено")

    def make_short_message(self):
        c_hash = crc8.crc8()
        if self.context.mission.mission_vars["last_short_message"] is None:
            c_hash.update(bytes(self.context.mission.mission_vars["initial_short_message"].encode("utf-8")))
        else:
            c_hash.update(bytes(self.context.mission.mission_vars["last_short_message"].encode("utf-8")))

        if self.context.mission.mission_vars["CybP_02_active"]:
            return self.mission_vars["current_malfunction_short_message"]
        else:
            return c_hash.hexdigest()

    def reboot_drive(self, d_id):
        if self.mission_vars["CybP_03_active"]:
            if self.mission_vars["current_malfunction_drive_id"] == d_id:
                self.context.lg.warn(f"ДМ запросил перезагрузку привода {d_id} - выполняется")
                self.mission_vars["current_malfunction_drive_id"] = 99
            else:
                self.context.lg.warn(f"ДМ запросил перезагрузку привода {d_id} - и так здоров")

    @run_in_thread
    def wait_for_CybP_02_activation(self):
        time.sleep(random.randint(20, 40))
        if self.status != 1:
            return
        self.mission_vars["CybP_02_active"] = True

        self.context.lg.warn("КП (CybP_02) активировано: Неполадки системы связи")
        self.mission_vars["current_malfunction_short_message"] = random.choice(MALFUNCTION_SHORT_MESSAGES)
        self.wait_for_CybP_02_deactivation()

    @run_in_thread
    def wait_for_CybP_02_deactivation(self):
        time.sleep(random.randint(3, 6))
        self.context.lg.warn("КП (CybP_02) деактивировано")
        self.mission_vars["CybP_02_active"] = False

    @run_in_thread
    def wait_for_CybP_04_activation(self):
        time.sleep(random.randint(20, 40))
        if self.status != 1:
            return
        self.mission_vars["CybP_04_active"] = True

        self.context.lg.warn("КП (CybP_04) активировано: Сбой навесного оборудования")
        self.context.spd.brush.last_speed = self.context.spd.brush.speed
        self.context.spd.brush.speed = 300
        self.wait_for_CybP_04_deactivation()

    @run_in_thread
    def wait_for_CybP_04_deactivation(self):
        time.sleep(random.randint(4, 8))
        self.context.spd.brush.speed = self.context.spd.brush.last_speed
        self.context.lg.warn("КП (CybP_04) деактивировано")
        self.mission_vars["CybP_04_active"] = False

    @run_in_thread
    def wait_for_CybP_03_activation(self):
        time.sleep(random.randint(40, 110)) # ПОМЕНЯННО 40 110
        if self.status != 1:
            return
        self.mission_vars["CybP_03_active"] = True

        self.mission_vars["current_malfunction_drive_id"] = random.randint(0, 3)
        self.context.lg.warn(
            f"КП (CybP_03) активировано: Компрометация кода приводов ({self.mission_vars['current_malfunction_drive_id']})"
        )
        self.mission_vars["drive_info"][self.mission_vars["current_malfunction_drive_id"]]["last_received_from"] = (
            self.context.system.gen_uid(12)
        )
        self.wait_for_CybP_03_deactivation()

    @run_in_thread
    def wait_for_CybP_03_deactivation(self):
        time.sleep(random.randint(4, 8))
        self.context.lg.warn("КП (CybP_03) деактивировано")
        self.mission_vars["CybP_03_active"] = False

    @run_in_thread
    def wait_for_CybP_06_deactivation(self):
        time.sleep(10)
        if self.send_request_with_ack("force_fast_end"):
            self.context.lg.warn("КП (CybP_06) деактивировано")

    def check_cyb_CybP_01(self):
        if self.context.mission.cybs["CybP_01"]:
            if not self.context.mission.mission_vars["CybP_01_occurred"]:
                if (
                    self.context.robots.current_robot.current_cell == c.get_trigger("CybP_01")[0]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybP_01")[1]
                ):
                    self.context.mission.mission_vars["CybP_01_occurred"] = True
                    self.context.mission.mission_vars["ap_code_hash"] = self.context.system.gen_uid(20)
                    self.context.lg.warn("КП (CybP_01) активировано: Компрометация кода автопилота")

    def check_cyb_CybP_06(self):
        if self.context.mission.cybs["CybP_06"]:
            if not self.context.mission.mission_vars["CybP_06_occurred"]:
                if (
                    self.context.robots.current_robot.current_cell == c.get_trigger("CybP_06")[0]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybP_06")[1]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybP_06")[2]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybP_06")[3]
                ):
                    if self.send_request_with_ack("force_fast_begin"):
                        self.context.mission.mission_vars["CybP_06_occurred"] = True
                        self.context.lg.warn("КП (CybP_06) активировано: Несанкционированное ускорение")
                        self.context.mission.wait_for_CybP_06_deactivation()


class Triggers:
    def __init__(self, context):
        self.context = context

        self.start_mission_trigger = False
        self.stop_mission_trigger = False
        self.reset_mission_trigger = False
        self.reset_twin_trigger = False
        self.begin_trigger = False
