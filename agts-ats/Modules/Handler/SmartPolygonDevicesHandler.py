from Modules import BaseUDPSendHandler
from Modules.Logic import const as c


class SPDHandler:
    def __init__(self, context):
        self.context = context
        self.handlers = []

    def generate(self):

        for device in self.context.spd.t_lights:
            self.handlers.append(TLightPDViaUDPSender(self.context, device, 0.21))
        self.handlers.append(BarrierPDViaUDPSender(self.context, self.context.spd.barrier, 0.2))
        self.handlers.append(BrushPDViaUDPSender(self.context, self.context.spd.brush, 0.2))

        return self.handlers


class TLightPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        return {"c": self.device.color}

    def _process_message(self, message):
        pass


class BarrierPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        return {"barrier": self.device.status}

    def _process_message(self, message):
        pass


class BrushPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        return {"speed": self.device.speed}

    def _process_message(self, message):
        pass
