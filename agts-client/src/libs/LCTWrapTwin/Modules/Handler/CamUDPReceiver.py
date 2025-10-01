import numpy as np
import cv2

from src.libs.LCTWrapTwin.Modules import BaseUDPReceiveHandler


class CamUDPReceiver(BaseUDPReceiveHandler):
    def __init__(self, context, host="0.0.0.0", port=5066):
        super().__init__(context, host, port)

    def _process_message(self, message):
        try:
            jpeg_size = int.from_bytes(message[:4], byteorder='little')
            if len(message) < 4 + jpeg_size:
                self.context.warn(f"Incomplete frame received: {len(message)} bytes, expected {4 + jpeg_size}")
                return
            jpeg_data = message[4:4 + jpeg_size]
            frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.context.camera_frame = frame
        except Exception as e:
            pass
