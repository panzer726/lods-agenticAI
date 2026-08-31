import tinytuya
light = tinytuya.OutletDevice('a36cb72light1945cf9235fcsy', '192.168.1.2', 'Ke;0MYt#GGtwb?+u')
light.set_version(3.5)
print(light.status())

import time

def rgb_to_tuya_hex(h, s, v):
    return f"{h:04x}{s:04x}{v:04x}"

def sunrise_wakeup(light, duration_minutes=25, steps=30):
    interval = (duration_minutes * 60) / steps

    # Set dim starting color BEFORE turning on, so no bright flash
    light.set_value(21, "colour")
    time.sleep(0.2)
    light.set_value(24, rgb_to_tuya_hex(10, 1000, 10))  # very dim red
    time.sleep(0.2)
    light.set_value(20, True)
    time.sleep(0.3)

    # Phase 1: dim red -> orange/yellow, brightening slowly
    color_steps = steps // 2
    for i in range(color_steps + 1):
        progress = i / color_steps
        hue = int(10 + (45 - 10) * progress)
        sat = int(1000 - 400 * progress)
        val = int(10 + (300 - 10) * progress)

        color_hex = rgb_to_tuya_hex(hue, sat, val)
        light.set_value(24, color_hex)
        time.sleep(interval)

    # Phase 2: transition to white, starting dim, ramping up gradually
    light.set_value(22, 10)
    time.sleep(0.3)
    light.set_value(21, "white")
    time.sleep(0.2)

    white_steps = steps - color_steps
    for i in range(white_steps + 1):
        progress = i / white_steps
        brightness = int(10 + (1000 - 10) * progress)
        temp = int(600 - (600 - 200) * progress)

        light.set_value(22, brightness)
        time.sleep(0.05)
        light.set_value(23, temp)
        time.sleep(interval)

sunrise_wakeup(light, duration_minutes=25, steps=30)