import devinput
import time

def main():
    led_devices = devinput.list_capable_devices([devinput.EventType.EV_LED])
    if not led_devices:
        raise ValueError("no devices have LEDs")
    print("Available LED Devices:")
    for index, dev in enumerate(led_devices):
        print(f"{index+1}) {dev.name}")
    while True:
        try:
            index = int(input("Pick a device: "))-1
        except ValueError:
            print("Please enter a number.")
            continue
        if not 0<=index<len(led_devices):
            print("Please enter a valid index.")
            continue
        break
    device = led_devices[index]
    with device:
        print("LEDs on device:")
        leds = list(device.capabilities.led_cap)
        for index, cap in enumerate(leds):
            print(f"{index+1}) {cap.name}")
        while True:
            try:
                index = int(input("Pick a LED: "))-1
            except ValueError:
                print("Please enter a number.")
                continue
            if not 0<=index<len(leds):
                print("Please enter a valid index.")
                continue
            break
        led = leds[index]
        on = 1
        while True:
            device.send_event(devinput.Event(led, on))
            on=1-on
            time.sleep(0.1)

if __name__=="__main__":
    main()
