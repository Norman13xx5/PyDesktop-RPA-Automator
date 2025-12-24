from robocorp.tasks import task
from RPA.Desktop import Desktop  # Importar la biblioteca de automatización del escritorio

@task
def minimal_task():
    desktop = Desktop()
    position = desktop.get_mouse_position()
    print(f"La posición actual del mouse es: X={position.x}, Y={position.y}")

@task
def minimal2_task2():
    desktop = Desktop()
    position = desktop.get_mouse_position()
    print(f"La posición actual del mouse es: X={position.x}, Y={position.y}")