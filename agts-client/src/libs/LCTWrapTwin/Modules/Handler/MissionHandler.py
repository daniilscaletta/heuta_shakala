import json
import time
from abc import abstractmethod
from threading import Thread

import requests
from fastapi import Request

from src.libs.LCTWrapTwin.Modules import BaseHandler, BaseHttpTransport
from .libs import AGTSHookAp


class MissionHandler(BaseHandler):
    def __init__(self, context):
        super().__init__(context)
        self.ap_hook = AGTSHookAp(context)
        self.lg = context.lg

        self.running = True

        self.cybs_configured = False

        Thread(target=HTTPCommandReceiver(self.context, self).run, daemon=True).start()

    @abstractmethod
    def mission_code(self):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def config_cyber_obstacles():
        raise NotImplementedError

    def _mission_code_wrapper(self):
        Thread(target=self.mission_code, daemon=True).start()

        while self.running:
            time.sleep(0.1)

    def _wait_for_start(self):
        self.lg.log("(AP) Заезд инициализирован - ожидание старта")
        while not self.context.mission_state:
            time.sleep(0.1)

    def _resolve_cyber_obstacles(self, toggles: dict):
        err = False
        if len(toggles) < 6:
            err = True
        if toggles.get("CybP_01", None) is None:
            err = True
        if toggles.get("CybP_02", None) is None:
            err = True
        if toggles.get("CybP_03", None) is None:
            err = True
        if toggles.get("CybP_04", None) is None:
            err = True
        if toggles.get("CybP_05", None) is None:
            err = True
        if toggles.get("CybP_06", None) is None:
            err = True

        if err:
            self.context.lg.error(f"Неверная конфигурация киберпрепятствий: {toggles}")
            return False

        self.context.cybs = toggles.copy()
        return True

    def _send_request_with_response(self, method, data):
        try:
            req = requests.post(
                f"http://127.0.0.1:13501/{method}",
                data=json.dumps({"content": data}),
                timeout=1,
            )
            if req.status_code == 200:
                response = json.loads(req.text)
                return response["content"]
        except Exception as e:
            if "timeout" in str(e):
                self.context.lg.error(f"Ошибка отправки команды: АСО не отвечает")
        return None

    def set_barrier_toggle(self):
        return self._send_request_with_response("barrier_toggle", {})

    def set_brush_speed(self, speed):
        return self._send_request_with_response("set_brush_speed", {"speed": speed})

    def get_camera_frame(self):
        return self.context.camera_frame

    def set_robot_speed(self, speed):
        if speed < 0 or speed > 0.24:
            self.context.lg.error(f"Неверная скорость робота: {speed}. Должна быть в пределах 0 и 0.24")
            return False
        self.context.r_speed = speed
        return True

    def get_message_from_trusted_module(self):
        m = self.context.robot.messages.copy()
        self.context.robot.messages = []
        return m

    def do_wait(self, strategy: str = "time", duration: float = 0.5):
        if strategy == "time":
            time.sleep(duration)
        elif strategy == "flag":
            self.context.wait_flag = True
            while self.context.wait_flag:
                time.sleep(0.1)

    def run(self):
        if not self._resolve_cyber_obstacles(self.config_cyber_obstacles()):
            self.context.init_ok = False
            return
        self.context.mission_checks_ok = True

        self._wait_for_start()
        self.lg.log("Код заезда инициализирован")
        Thread(target=self._mission_code_wrapper, daemon=True).start()
        while self.context.mission_state:
            time.sleep(0.1)
        self.context.emergency_stop = True
        self.running = False
        self.lg.log("Заезд завершён!")
        time.sleep(0.2)
        self.context.init_ok = False


class HTTPCommandReceiver(BaseHttpTransport):
    def __init__(self, context, mission_root):
        super().__init__(context, "command_receiver")
        self.mission_root = mission_root

    def make_routes(self):
        @self.api.post("/get_cybs")
        async def get_cybs(data: Request):
            return {"status": "OK", "content": self.context.cybs}

        @self.api.post("/start_mission")
        async def start_mission(data: Request):
            self.context.mission_state = True
            return {"status": "OK"}

        @self.api.post("/stop_mission")
        async def stop_mission(data: Request):
            self.context.mission_state = False
            return {"status": "OK"}

        @self.api.post("/emergency_stop")
        async def emergency_stop(data: Request):
            self.context.emergency_stop = True
            return {"status": "OK"}

        @self.api.post("/emergency_stop_release")
        async def emergency_stop_release(data: Request):
            self.context.emergency_stop = False
            return {"status": "OK"}

        @self.api.post("/force_fast_begin")
        async def force_fast_begin(data: Request):
            self.context.r_speed = self.mission_root.ap_hook.default_max_speed * 10
            return {"status": "OK"}

        @self.api.post("/force_fast_end")
        async def force_fast_end(data: Request):
            self.context.r_speed = self.mission_root.ap_hook.default_max_speed
            return {"status": "OK"}
