import json
import random
import time

import requests
from fastapi import Request

from Modules import BaseHandler, BaseHttpTransport
from Modules.Logic import const as c


class MissionHandler(BaseHandler):
    def __init__(self, context):
        super().__init__(context)

    def set_status(self, status):
        if status == 0:
            self.context.spd.t_lights[0].color = 1
            self.context.spd.t_lights[1].color = 1
            self.context.spd.t_lights[2].color = 1

            self.context.spd.barrier.status = 1
        self.context.mission.status = status
        self.drop_triggers()

    def drop_triggers(self):
        self.context.mission.triggers.start_mission_trigger = False
        self.context.mission.triggers.stop_mission_trigger = False
        self.context.mission.triggers.reset_mission_trigger = False

    def check_reach_finish_zone(self):
        if self.context.mission.mission_tasks["left_start_zone"]:
            if self.context.robots.current_robot.current_cell == c.get_zone("start_finish")[0]:
                self.context.mission.mission_tasks["reach_finish_zone"] = True
                self.context.lg.log("Робот достиг финишной зоны")
                return True
        return False

    def check_left_start_zone(self):
        if not self.context.mission.mission_tasks["left_start_zone"]:
            if self.context.robots.current_robot.current_cell != c.get_zone("start_finish")[0]:
                self.context.mission.mission_tasks["left_start_zone"] = True
                self.context.lg.log("Робот покинул стартовую зону")

    def run(self):
        mission = self.context.mission
        self.set_status(0)
        while True:
            time.sleep(0.01)

            if self.context.mission.status == 0:
                if self.context.mission.triggers.start_mission_trigger:
                    cyb_config = self.send_request_with_response("get_cybs")
                    if cyb_config.get("content", None) is not None:
                        if self.send_request_with_ack("start_mission"):
                            mission.mission_uid = self.context.system.gen_uid(6)
                            self.context.lg.add_to_batch("")
                            self.context.lg.add_to_batch("")
                            self.context.lg.add_to_batch("")
                            self.context.lg.flush_batch()
                            self.set_status(1)
                            mission.init_mission(cyb_config["content"])
                            self.context.lg.log(f"Заезд ({mission.mission_uid}): запущен")
                            continue
                        else:
                            self.context.lg.error("Ошибка при инициализации заезда")
                            self.drop_triggers()
                    else:
                        self.context.lg.error("СВП не инициализирована или информация об активации КП не передана")
                        self.drop_triggers()

            if self.context.mission.status == 1:
                if self.context.mission.triggers.stop_mission_trigger:
                    if self.send_request_with_ack("stop_mission"):
                        self.set_status(4)
                        self.context.lg.log(f"Заезд ({mission.mission_uid}): остановлен - по внешней команде")
                        continue
                    else:
                        self.context.lg.error("Ошибка при остановке заезда (внешняя команда)")
                        self.drop_triggers()

                if mission.check_timer():
                    if self.send_request_with_ack("stop_mission"):
                        self.set_status(4)
                        self.context.lg.log(f"Заезд ({mission.mission_uid}): остановлен - по истечении времени")
                        continue
                    else:
                        self.context.lg.error("Ошибка при остановке заезда (истечение времени)")
                        self.drop_triggers()

                if self.check_reach_finish_zone():
                    if self.send_request_with_ack("stop_mission"):
                        self.set_status(3)
                        self.context.lg.log(f"Заезд ({mission.mission_uid}): остановлен - по достижению зоны финиша")
                        continue
                    else:
                        self.context.lg.error("Ошибка при остановке заезда (достижение зоны финиша)")
                        self.drop_triggers()

                if self.context.mission.triggers.reset_mission_trigger:
                    self.set_status(0)
                    self.context.lg.log(f"Заезд ({mission.mission_uid}): завершён и сохранён")
                    self.context.lg.log("Возможно начать новый заезд")
                    continue

                self.check_left_start_zone()

            if self.context.mission.status == 3:
                if self.context.mission.triggers.reset_mission_trigger:
                    self.set_status(0)
                    self.context.lg.log(f"Заезд ({mission.mission_uid}): завершён и сохранён")
                    self.context.lg.log("Возможно начать новый заезд")
                    continue

            if self.context.mission.status == 4:
                if self.context.mission.triggers.reset_mission_trigger:
                    self.set_status(0)
                    self.context.lg.log(f"Заезд ({mission.mission_uid}): завершён и сохранён")
                    self.context.lg.log("Возможно начать новый заезд")
                    continue

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

    def send_request_with_response(self, method):
        try:
            req = requests.post(
                f"http://{self.context.robots.current_robot.ip_address}:13500/{method}",
                # data=json.dumps({"key": "dev_uuid"}),
                timeout=1,
            )
            if req.status_code == 200:
                response = json.loads(req.text)
                return response
        except Exception as e:
            if "timeout" in str(e):
                self.context.lg.error(f"Ошибка отправки команды: робот не отвечает")
        return {}


class HTTPMissionReceiver(BaseHttpTransport):
    def __init__(self, context):
        super().__init__(context, "mission_receiver")

    def make_routes(self):

        @self.api.post("/barrier_toggle")
        async def barrier_toggle(data: Request):
            state = 1 - self.context.spd.barrier.status
            if random.randint(0, 10) > 5 or not self.context.mission.cybs["CybP_05"]:
                self.context.spd.barrier.status = 1 - self.context.spd.barrier.status
            return {"status": "OK", "content": {"state": 1 - state}}

        @self.api.post("/set_brush_speed")
        async def set_brush_speed(data: Request):
            datum = await data.json()
            try:
                datum = datum["content"]
                self.context.spd.brush.speed = datum["speed"]
                self.context.spd.brush.last_speed = datum["speed"]
                return {"status": "OK"}
            except Exception as e:
                pass
            return {"status": "ERROR", "content": "Неверный формат запроса: Ожидается {'speed': int}"}

        @self.api.post("/get_brush_speed")
        async def get_brush_speed(data: Request):
            return {"status": "OK", "content": {"speed": self.context.spd.brush.speed}}

        @self.api.post("/ap_force_reset")
        async def ap_force_reset(data: Request):
            self.context.mission.reboot_ap()
            return {"status": "OK"}

        @self.api.post("/get_ap_code_hash")
        async def get_ap_code_hash(data: Request):
            return {"status": "OK", "content": {"ap_code_hash": self.context.mission.mission_vars["ap_code_hash"]}}

        @self.api.post("/get_short_message")
        async def get_short_message(data: Request):
            c_hash = self.context.mission.make_short_message()
            return {"status": "OK", "content": {"message": c_hash}}

        @self.api.post("/set_short_message")
        async def set_short_message(data: Request):
            datum = await data.json()
            try:
                self.context.mission.mission_vars["last_short_message"] = datum.get("content", {}).get("message", "")
                return {"status": "OK"}
            except Exception as e:
                return {"status": "ERROR", "content": "Неверный формат сообщения"}

        @self.api.post("/get_drive_data")
        async def get_drive_data(data: Request):
            return {"status": "OK", "content": {"drive_data": self.context.mission.mission_vars["drive_info"]}}

        @self.api.post("/drive_force_reset")
        async def drive_force_reset(data: Request):
            datum = await data.json()
            try:
                d_id = datum.get("content", {}).get("d_id", "")
                self.context.mission.reboot_drive(d_id)
                return {"status": "OK"}
            except Exception as e:
                pass
            return {"status": "ERROR", "content": "Неверный формат запроса: Ожидается {'d_id': 'ID'}"}

        @self.api.post("/emergency_stop")
        async def emergency_stop(data: Request):
            if self.context.mission.send_request_with_ack("emergency_stop"):
                self.context.lg.warn("ДМ запросил блокировку приводов - выполняется")
                return {"status": "OK"}
            else:
                return {"status": "ERROR", "content": "Не удалось выключить приводы робота"}

        @self.api.post("/emergency_stop_release")
        async def emergency_stop_release(data: Request):
            if self.context.mission.send_request_with_ack("emergency_stop_release"):
                self.context.lg.warn("ДМ запросил снятие блокировки приводов - выполняется")
                return {"status": "OK"}
            else:
                return {"status": "ERROR", "content": "Не удалось включить приводы робота"}

        @self.api.post("/speed_controller_reset")
        async def speed_controller_reset(data: Request):
            if self.context.mission.send_request_with_ack("force_fast_end"):
                self.context.lg.warn("ДМ запросил корректировку скорости движения - выполняется")
                return {"status": "OK"}
            else:
                return {"status": "ERROR", "content": "Не удалось перезагрузить контроллер скорости"}

        @self.api.post("/get_system_messages")
        async def get_system_messages(data: Request):
            messages = self.context.mission.mission_vars["system_messages"].copy()
            self.context.mission.mission_vars["system_messages"] = []
            return {
                "status": "OK",
                "content": {"system_messages": messages},
            }
