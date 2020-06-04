import datetime
import pulsectl
import psutil
import os
import logging 

PULSE = pulsectl.Pulse()

NET_PREV_RXBYTES = 0
NET_PREV_TXBYTES = 0


def progress_fmt(x):
    n = int(x * 10)
    m = int(x * 100) % 10
    return "[" + "#" * n + str(m) + "-" * (9 - n) + "]"


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
    try:
        for p in psutil.process_iter():
            if p.name().startswith("mpg123"):
                track_name = os.path.split(p.open_files()[1].path)[-1]
                curr_track = f"Now playing: {track_name}"
                if p.status() == "stopped":
                    curr_track += " (PAUSED)"
    except Exception as e:
        logging.warn(f"Error parsing track info: {str(e)}")
    return curr_track


def get_net():
    global NET_PREV_RXBYTES, NET_PREV_TXBYTES
    devpath = "/sys/class/net"
    devs = [os.path.join(devpath, f) for f in os.listdir(devpath)]
    netfiles = [(os.path.join(d, "statistics", "rx_bytes"),
                 os.path.join(d, "statistics", "tx_bytes")) for d in devs]
    curr_rxbytes, curr_txbytes = 0, 0
    for rxpath, txpath in netfiles:
        with open(rxpath, "r") as fd:
            curr_rxbytes += float(fd.read())
        with open(txpath, "r") as fd:
            curr_txbytes += float(fd.read())

    net_down = curr_rxbytes - NET_PREV_RXBYTES
    net_up = curr_txbytes - NET_PREV_TXBYTES
    NET_PREV_RXBYTES = curr_rxbytes
    NET_PREV_TXBYTES = curr_txbytes

    return f"{format_net(net_down)} ▼ | {format_net(net_up)} ▲"


def format_net(x):
    units = [" B", "KB", "MB", "GB", "TB"]
    unit = 0
    while x >= 1000 and unit != len(units) - 1:
        x /= 1000
        unit += 1
    return f"{x:6.2f} {units[unit]}"
