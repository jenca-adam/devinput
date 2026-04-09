import devinput


def main():
    lid_switches = devinput.list_capable_devices(devinput.SwEvent.SW_LID)
    if not lid_switches:
        raise ValueError("no lid switches found")
    lid_switch = lid_switches[0]
    print(f"Selected lid: {lid_switch.name}")
    confirm = input("continuing will put your device to sleep. continue [y*]")
    if confirm.lower() != "y":
        print("ok")
        return
    with lid_switch:
        lid_switch.send_event(devinput.Event(devinput.SwEvent.SW_LID, 1))
        lid_switch.send_event(devinput.Event(devinput.SynEvent.SYN_REPORT, 0))


if __name__ == "__main__":
    main()
