from dataclasses import dataclass, field


@dataclass
class TrafficSPD:
    d_id: int
    address: str
    port: str
    color: int = 0


@dataclass
class BarrierSPD:
    d_id: int
    address: str
    port: str
    status: int = 1


@dataclass
class BrushSPD:
    d_id: int
    address: str
    port: str
    speed: int = 0
    last_speed: int = 0


class SmartPolygonDevices:
    def __init__(self, context):
        self.context = context

        self.t_lights = [
            TrafficSPD(
                0,
                "127.0.0.1",
                "5031",
            ),
            TrafficSPD(
                1,
                "127.0.0.1",
                "5032",
            ),
            TrafficSPD(
                2,
                "127.0.0.1",
                "5030",
            ),
        ]

        self.barrier = BarrierSPD(
            3,
            "127.0.0.1",
            "15000",
        )

        self.brush = BrushSPD(
            4,
            "127.0.0.1",
            "11500",
        )
