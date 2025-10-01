import arcade
import cv2
import numpy as np
from PIL import Image

from Modules import BaseHandler
from Modules.Logic import const as c, Rect


class RenderHandler(BaseHandler):
    def __init__(self, context):
        super().__init__(context)

        app = AppWindow(context)
        try:
            arcade.run()
        except KeyboardInterrupt as e:
            self.context.lg.log("Нажмите ещё раз для выхода...")
        except Exception as e:
            pass

    def run(self):
        pass


class AppWindow(arcade.Window):
    def __init__(self, context):
        super().__init__(c.WINDOW_WIDTH, c.WINDOW_HEIGHT, c.WINDOW_TITLE)
        self.app_context = context
        self.update_fill_counter = 0
        self.fill_pattern = None

        arcade.set_background_color(arcade.color.ARSENIC)
        self.background = arcade.load_texture("Modules/Assets/background.jpg")

    def reset(self):
        pass

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
            self.background,
            arcade.LRBT(
                c.FIELD_OFFSET_X,
                c.WINDOW_WIDTH - c.FIELD_OFFSET_X,
                c.FIELD_OFFSET_Y,
                c.WINDOW_HEIGHT - c.FIELD_OFFSET_Y,
            ),
        )

        # self.draw_grid()
        self.draw_polygon_zones()
        self.draw_borders()
        self.draw_fill()
        self.draw_robots()

    def draw_fill(self):
        if not self.app_context.field.filled:
            return

        if self.fill_pattern is None or self.update_fill_counter > 20:
            self.update_fill_counter = 0
            bit_array = np.unpackbits(np.frombuffer(self.app_context.field.filled, dtype=np.uint8))

            image_data = bit_array[: 720 * 720].reshape((720, 720))
            image_data = image_data.astype(np.uint8) * 255
            image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2RGBA)
            image_data = cv2.flip(image_data, 0)

            alpha_channel = image_data[:, :, 0].copy()
            image_data[:, :, 0] = 0
            image_data[:, :, 1] = 200
            image_data[:, :, 2] = 200
            alpha_channel[alpha_channel > 0] = 100
            image_data[:, :, 3] = alpha_channel

            pil_image = Image.fromarray(image_data)
            texture = arcade.Texture(pil_image)
            self.fill_pattern = texture
        else:
            self.update_fill_counter += 1
        try:
            arcade.draw_texture_rect(
                self.fill_pattern,
                arcade.LRBT(
                    c.FIELD_OFFSET_X,
                    c.WINDOW_WIDTH - c.FIELD_OFFSET_X,
                    c.FIELD_OFFSET_Y,
                    c.WINDOW_HEIGHT - c.FIELD_OFFSET_Y,
                ),
            )
        except Exception as e:
            self.app_context.lg.error(f"Ошибка отрисовки заполненной области: {e}")

    def draw_polygon_zones(self):
        for cell in self.app_context.field.cells:
            color = c.ZONE_COLORS.get(cell.zone_type, c.ZONE_COLORS[None])
            for robot in self.app_context.robots.list:
                if cell.contains(robot.chassis) and cell.zone_type != "road" and cell.zone_type != "start_finish":
                    color = (color[0], color[1], color[2], 220)
            arcade.draw_polygon_filled(cell.get_translated_vertices(), color)

            if cell.indicator is not None:
                vertices = cell.get_indicator_vertices()
                arcade.draw_polygon_filled(vertices, cell.indicator)
                arcade.draw_polygon_outline(vertices, (0, 0, 0))

    def draw_robots(self):
        for robot in self.app_context.robots.list:
            if robot.r_id is not None:
                if robot.position_quality < 0.1:
                    continue
                arcade.draw_polygon_filled(robot.chassis.get_translated_vertices(), robot.base_color)
                # arcade.draw_polygon_outline(robot.wheel_base.get_translated_vertices(), (0, 254, 254))
                arcade.Text(
                    "R_" + robot.r_id,
                    robot.chassis.get_translated_center()[0],
                    robot.chassis.get_translated_center()[1] + 40,
                    font_size=18,
                    color=(20, 20, 20)
                ).draw()
                for wheel in robot.wheels:
                    color = (200, 200, 200)
                    for cell in self.app_context.field.cells:
                        if cell.contains(wheel) and cell.zone_type != "road":
                            color = (254, 0, 0)
                        if cell.contains(wheel) and (
                                cell.zone_type == "low_speed"
                                or cell.zone_type == "start_finish"
                                or cell.zone_type == "pedestrian"
                        ):
                            color = (0, 0, 254)
                            # arcade.draw_polygon_filled(cell.get_translated_vertices(), (0, 254, 0))
                    arcade.draw_polygon_filled(wheel.get_translated_vertices(), color)

    @staticmethod
    def draw_grid():
        for x in range(c.FIELD_OFFSET_X, c.WINDOW_WIDTH, round(c.FIELD_CELL_SIZE * c.FIELD_TO_WINDOW_SCALE)):
            arcade.draw_line(x, 0, x, c.WINDOW_HEIGHT, arcade.color.BLUEBERRY, 1)
        for y in range(c.FIELD_OFFSET_Y, c.WINDOW_HEIGHT, round(c.FIELD_CELL_SIZE * c.FIELD_TO_WINDOW_SCALE)):
            arcade.draw_line(0, c.WINDOW_HEIGHT - y, c.WINDOW_WIDTH, c.WINDOW_HEIGHT - y, arcade.color.BLUEBERRY, 1)

    @staticmethod
    def draw_borders():
        arcade.draw_line(c.FIELD_OFFSET_X, 0, c.FIELD_OFFSET_X, c.WINDOW_HEIGHT, arcade.color.RED, 1)
        arcade.draw_line(
            c.WINDOW_WIDTH - c.FIELD_OFFSET_X,
            0,
            c.WINDOW_WIDTH - c.FIELD_OFFSET_X,
            c.WINDOW_HEIGHT,
            arcade.color.RED,
            1,
        )
        arcade.draw_line(0, c.FIELD_OFFSET_Y, c.WINDOW_WIDTH, c.FIELD_OFFSET_Y, arcade.color.RED, 1)
        arcade.draw_line(
            0,
            c.WINDOW_HEIGHT - c.FIELD_OFFSET_Y,
            c.WINDOW_WIDTH,
            c.WINDOW_HEIGHT - c.FIELD_OFFSET_Y,
            arcade.color.RED,
            1,
        )

    @staticmethod
    def draw_edges(rect: Rect, color=arcade.color.YELLOW):
        vertices = rect.get_translated_vertices()
        for i in range(len(vertices)):
            start_point = vertices[i]
            end_point = vertices[(i + 1) % len(vertices)]
            arcade.draw_line(start_point[0], start_point[1], end_point[0], end_point[1], color, 2)
            arcade.draw_circle_filled(vertices[i][0], vertices[i][1], 1, color)
