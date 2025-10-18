from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation

Window.size = (400, 300)

class EyeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.eye_width = 80
        self.eye_height = 80

        # Base positions
        self.left_eye_base = (100, 120)
        self.right_eye_base = (220, 120)

        with self.canvas:
            # Background (black)
            Color(0, 0, 0)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)

            # Eyes (blue)
            Color(0, 0.7, 1)
            self.left_eye = RoundedRectangle(pos=self.left_eye_base, size=(self.eye_width, self.eye_height), radius=[20])
            self.right_eye = RoundedRectangle(pos=self.right_eye_base, size=(self.eye_width, self.eye_height), radius=[20])

        # Blinking every 4 seconds
        Clock.schedule_interval(self.animate_blink, 4)

        # Track mouse
        Window.bind(mouse_pos=self.on_mouse_move)

    def animate_blink(self, dt):
        blink_down = Animation(size=(self.eye_width, 10), duration=0.2)
        blink_up = Animation(size=(self.eye_width, self.eye_height), duration=0.2)
        (blink_down + blink_up).start(self.left_eye)
        (blink_down + blink_up).start(self.right_eye)

    def on_mouse_move(self, window, pos):
        x, y = pos
        win_width, win_height = Window.size

        # Horizontal offset: -20 (left), 0 (center), +20 (right)
        if x < win_width * 0.33:
            offset_x = -20
        elif x > win_width * 0.66:
            offset_x = 20
        else:
            offset_x = 0

        # Vertical offset: +20 (down), 0 (center), -20 (up)
        if y < win_height * 0.33:
            offset_y = -20
        elif y > win_height * 0.66:
            offset_y = 20
        else:
            offset_y = 0

        # Animate eye positions smoothly
        new_left_pos = (self.left_eye_base[0] + offset_x, self.left_eye_base[1] + offset_y)
        new_right_pos = (self.right_eye_base[0] + offset_x, self.right_eye_base[1] + offset_y)

        Animation(pos=new_left_pos, duration=0.2).start(self.left_eye)
        Animation(pos=new_right_pos, duration=0.2).start(self.right_eye)

class EyeApp(App):
    def build(self):
        return EyeWidget()

if __name__ == '__main__':
    EyeApp().run()
