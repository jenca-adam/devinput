import devinput


def main():
    keyboards = devinput.list_capable_devices(devinput.KeyEvent.KEY_A)
    if not keyboards:
        raise ValueError("no keyboard found :(")
    keyboard = keyboards[0]
    print(f"Selected keyboard: {keyboard.name}")
    print("press esc to exit")
    with keyboard, keyboard.grabbed():
        for event in keyboard:
            if event.type == devinput.EventType.EV_KEY:
                print(event)
                if event.code == devinput.KeyEvent.KEY_ESC:
                    break


if __name__ == "__main__":
    main()
