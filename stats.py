import datetime
import pulsectl
import psutil
import os

PULSE = pulsectl.Pulse()


def progress_fmt(x):
    n = int(x * 10)
    m = int(x * 100) % 10
    return "[" + "#" * n + str(m) + " " * (9 - n) + "]"


def get_date():
    d = datetime.datetime.now()
    return d.strftime("%a %x %I:%M:%S %p")


def get_volume(sink_name=None):
    global PULSE
    if sink_name is None:
        sink_name = PULSE.server_info().default_sink_name
    for sink in PULSE.sink_list():
        if sink.name == sink_name:
            volume = progress_fmt(PULSE.volume_get_all_chans(sink))
            return f"Volume: {volume} Mute: {'No ' if sink.mute == 0 else 'Yes'}"
    return "Volume: error"


def get_ram():
    ram = psutil.virtual_memory().percent / 100
    return f"RAM: {progress_fmt(ram)}"


def get_cpu(dev, label):
    p = psutil.cpu_percent()
    p /= 100
    temp = ""
    for d in psutil.sensors_temperatures()[dev]:
        if d.label == label:
            temp = f"{d.current:0.2f}°C"
    return f"CPU: {progress_fmt(p)} {temp}"


def get_gpu(dev, label):
    for d in psutil.sensors_temperatures()[dev]:
        if d.label == label:
            temp = f"{d.current:0.2f}°C"
    return f"GPU: {temp}"


def get_current_track():
    curr_track = "Nothing is playing...."
    for p in psutil.process_iter():
        if p.name().startswith("mpg123"):
            track_name = os.path.split(p.open_files()[1].path)[-1]
            curr_track = f"Now playing: {track_name}"
            if p.status() == "stopped":
                curr_track += " (PAUSED)"
    return curr_track
