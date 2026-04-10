import devinput
import asyncio


async def main():
    keyboard = devinput.list_capable_devices(devinput.KeyEvent.KEY_A)[0]
    mouse = devinput.list_capable_devices(devinput.KeyEvent.BTN_MOUSE)[0]
    print(f"Selected keyboard: {keyboard.name}")
    print(f"Selected mouse: {mouse.name}")
    with keyboard, mouse:
        while True:
            task1 = asyncio.create_task(keyboard.get_event_async())
            task2 = asyncio.create_task(mouse.get_event_async())

            done, pending = await asyncio.wait(
                [task1, task2], return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                print(task.result())

            for task in pending:
                task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
