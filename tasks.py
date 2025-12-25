from robocorp.tasks import task
from RPA.Desktop import Desktop
from RPA.core.geometry import Point

import time
import os
import json

# pynput para grabar y reproducir eventos reales
from pynput_robocorp import mouse, keyboard
from pynput_robocorp.mouse import Controller as MouseController, Button
from pynput_robocorp.keyboard import Controller as KeyboardController


# ===================================================
# UTILIDADES
# ===================================================

def move_mouse_natural_interruptible(
    desktop,
    target: Point,
    steps=30,
    delay=0.02,
    pause_seconds=5,
    tolerance=3
):
    """
    Mueve el mouse suavemente hacia un punto.
    Si el usuario mueve el mouse, se pausa.
    """
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
    """
    Busca una imagen en pantalla y devuelve su centro
    """
    element = desktop.wait_for_element(
        f"image:{image_path}",
        timeout=timeout
    )

    center_x = element.left + element.width // 2
    center_y = element.top + element.height // 2

    return Point(center_x, center_y)


# ===================================================
# TAREAS
# ===================================================

@task
def minimal_task():
    desktop = Desktop()
    pos = desktop.get_mouse_position()
    print(f"Mouse en X={pos.x}, Y={pos.y}")


@task
def take_reference_screenshot():
    desktop = Desktop()

    os.makedirs("img/screenshot", exist_ok=True)

    desktop.take_screenshot("img/screenshot/ref.png")

    print("Screenshot guardado en img/screenshot/ref.png")


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


# ===================================================
# GRABAR MOVIMIENTOS
# ===================================================

@task
def record_movements():
    events = []
    start_time = time.time()

    pressed_keys = set()
    stop_buffer = ""

    def now():
        return round(time.time() - start_time, 4)

    def on_move(x, y):
        events.append({
            "type": "move",
            "x": x,
            "y": y,
            "time": now()
        })

    def on_click(x, y, button, pressed):
        if pressed:
            events.append({
                "type": "click",
                "x": x,
                "y": y,
                "button": button.name,
                "time": now()
            })

    def on_press(key):
        nonlocal stop_buffer

        pressed_keys.add(key)

        # Si CTRL está presionado, escuchar la palabra "stop"
        if keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys:
            if hasattr(key, "char") and key.char:
                stop_buffer += key.char.lower()

                # Mantener solo los últimos 4 caracteres
                stop_buffer = stop_buffer[-4:]

                if stop_buffer == "stop":
                    print("Combinacion CTRL + stop detectada. Deteniendo grabacion.")
                    return False
        else:
            stop_buffer = ""

        try:
            k = key.char
        except AttributeError:
            k = str(key)

        events.append({
            "type": "key",
            "key": k,
            "time": now()
        })

    def on_release(key):
        if key in pressed_keys:
            pressed_keys.remove(key)

        # Si se suelta CTRL, resetear buffer
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            nonlocal stop_buffer
            stop_buffer = ""

    print("Grabando movimientos. Mantén CTRL y escribe 'stop' para detener.")

    with mouse.Listener(on_move=on_move, on_click=on_click), \
         keyboard.Listener(on_press=on_press, on_release=on_release) as k_listener:
        k_listener.join()

    os.makedirs("data", exist_ok=True)

    with open("data/movimientos.json", "w") as f:
        json.dump(events, f, indent=2)

    print("Grabacion guardada en data/movimientos.json")

# ===================================================
# REPRODUCIR MOVIMIENTOS
# ===================================================

@task
def replay_movements():
    mouse_ctrl = MouseController()
    keyboard_ctrl = KeyboardController()

    with open("data/movimientos.json", "r") as f:
        events = json.load(f)

    print("En 5 segundos enfoca la ventana donde debe ejecutarse...")
    time.sleep(5)

    prev_time = 0
    print("Reproduciendo movimientos...")

    for event in events:
        delay = event["time"] - prev_time
        time.sleep(max(0, delay))

        if event["type"] == "move":
            x = int(event["x"])
            y = int(event["y"])
            mouse_ctrl.position = (x, y)

        elif event["type"] == "click":
            x = int(event["x"])
            y = int(event["y"])
            mouse_ctrl.position = (x, y)

            btn = Button.left if event["button"] == "left" else Button.right
            mouse_ctrl.click(btn)

        elif event["type"] == "key":
            key_value = event["key"]

            # Ignorar teclas problemáticas
            if key_value in ("Key.caps_lock", "Key.ctrl", "Key.ctrl_l", "Key.ctrl_r"):
                continue

            try:
                if key_value.startswith("Key."):
                    key_name = key_value.replace("Key.", "")
                    key_obj = getattr(keyboard.Key, key_name, None)

                    if key_obj:
                        keyboard_ctrl.press(key_obj)
                        keyboard_ctrl.release(key_obj)
                else:
                    keyboard_ctrl.press(key_value)
                    keyboard_ctrl.release(key_value)

            except Exception as e:
                print(f"Tecla ignorada: {key_value} ({e})")

        prev_time = event["time"]

    print("Reproduccion finalizada")
