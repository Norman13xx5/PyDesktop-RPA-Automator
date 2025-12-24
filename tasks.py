from robocorp.tasks import task
from RPA.Desktop import Desktop
from RPA.core.geometry import Point
import time


def move_mouse_natural_interruptible(
    desktop,
    target,
    steps=30,
    delay=0.02,
    pause_seconds=5,
    tolerance=3
):
    while True:
        start = desktop.get_mouse_position()

        for i in range(1, steps + 1):
            x = start.x + (target.x - start.x) * i / steps
            y = start.y + (target.y - start.y) * i / steps
            expected = Point(int(x), int(y))

            desktop.move_mouse(expected)
            time.sleep(delay)

            current = desktop.get_mouse_position()
            if (
                abs(current.x - expected.x) > tolerance or
                abs(current.y - expected.y) > tolerance
            ):
                print("Mouse movido por el usuario. Pausando...")
                time.sleep(pause_seconds)
                break
        else:
            return


def get_center_point_from_image(desktop, image_path, timeout=10):
    element = desktop.wait_for_element(
        f"image:{image_path}",
        timeout=timeout
    )

    center_x = element.left + element.width // 2
    center_y = element.top + element.height // 2

    return Point(center_x, center_y)


@task
def click_img():
    desktop = Desktop()

    target = get_center_point_from_image(
        desktop,
        "img/image.png",
        timeout=10
    )

    move_mouse_natural_interruptible(
        desktop,
        target,
        steps=25,
        delay=0.02,
        pause_seconds=5
    )

    desktop.click()


@task
def minimal_task():
    desktop = Desktop()
    pos = desktop.get_mouse_position()
    print(f"Mouse en X={pos.x}, Y={pos.y}")
