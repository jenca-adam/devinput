import tkinter
import devinput

COLORS = ["#000000", "#aa0000", "#00aa00", "#0000aa", "#aa00aa"]
WIDTH = 800
DOT_RADIUS = 10


def main():
    devices = devinput.list_capable_devices(
        devinput.AbsEvent.ABS_MT_POSITION_X,
        devinput.AbsEvent.ABS_MT_POSITION_Y,
        devinput.AbsEvent.ABS_MT_TRACKING_ID,
        devinput.KeyEvent.BTN_MOUSE,
    )
    if not devices:
        raise ValueError("No touch devices found")
    device = devices[0]

    print(f"Selected device: {device.name}")
    with device:
        # get bounds
        x_info = device.get_absolute(devinput.AbsEvent.ABS_MT_POSITION_X)
        y_info = device.get_absolute(devinput.AbsEvent.ABS_MT_POSITION_Y)

        print(
            f"Device dimensions: {x_info.maximum-x_info.minimum}x{y_info.maximum-y_info.minimum}"
        )
        height = WIDTH * (y_info.maximum / x_info.maximum)
        root = tkinter.Tk()
        can = tkinter.Canvas()
        can.pack()
        can["width"] = WIDTH
        can["height"] = height

        def loop(*_):
            can.delete("tmp")
            pressed = devinput.KeyEvent.BTN_MOUSE in device.get_keys(
                (devinput.KeyEvent.BTN_MOUSE,)
            )
            tag = "tmp" if not pressed else "perm"
            state = device.get_multi_touch_state(num_slots=5)
            dots = zip(
                state[devinput.AbsEvent.ABS_MT_POSITION_X],
                state[devinput.AbsEvent.ABS_MT_POSITION_Y],
                state[devinput.AbsEvent.ABS_MT_TRACKING_ID],
            )
            for index, dot in enumerate(dots):
                touch_x, touch_y, tracking_id = dot
                if touch_x == -1 or touch_y == -1 or tracking_id == -1:
                    continue
                mapped_x, mapped_y = WIDTH * (
                    (touch_x - x_info.minimum) / (x_info.maximum - x_info.minimum)
                ), height * (
                    (touch_y - y_info.minimum) / (y_info.maximum - y_info.minimum)
                )
                color = COLORS[index % 5]
                can.create_oval(
                    mapped_x - DOT_RADIUS,
                    mapped_y - DOT_RADIUS,
                    mapped_x + DOT_RADIUS,
                    mapped_y + DOT_RADIUS,
                    fill=color,
                    outline=color,
                    tag=tag,
                )
            root.after(1, loop)

        with device.grabbed():
            root.after(0, loop)
            root.mainloop()


if __name__ == "__main__":
    main()
