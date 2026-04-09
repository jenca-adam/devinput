import devinput
import time


def main():
    clickers = devinput.list_capable_devices(devinput.KeyEvent.BTN_MOUSE)
    if not clickers:
        raise ValueError("no devices can click")
    print("Available clickers:")
    for index, dev in enumerate(clickers):
        print(f"{index+1}) {dev.name}")
    while True:
        try:
            index = int(input("Pick a device: ")) - 1
        except ValueError:
            print("Please enter a number.")
            continue
        if not 0 <= index < len(clickers):
            print("Please enter a valid index.")
            continue
        break
    clicker = clickers[index]
    rate = float(input("Enter click rate (clicks/s):"))
    sleep_time = 1 / rate
    print("Press Ctrl-C to stop")
    with clicker:
        while True:
            clicker.send_event(devinput.Event(devinput.KeyEvent.BTN_MOUSE, 1))
            clicker.send_event(devinput.Event(devinput.KeyEvent.BTN_MOUSE, 0))
            clicker.send_event(devinput.Event(devinput.SynEvent.SYN_REPORT, 0))
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
