import datetime
import pulsectl

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
            return f"Volume: {volume}"
    return "Volume: error"
