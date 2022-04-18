import datetime
import pulsectl
import psutil
import os
import logging 
import ipaddress

from subprocess import run 

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
    devices = psutil.sensors_temperatures()
    if dev not in devices:
        logging.warn(f"device {dev} not found in temperature sensors '{devices.keys()}'")
        return f"CPU: {dev} not found"
    device = [d for d in devices[dev] if d.label == label]
    if not device:
        logging.warn(f"label {label} not found in temperature sensors '{[d.label for d in devices[dev]]}'")
        temp = f"temp failure"
    else:
        temp = f"{device[0].current:0.2f}°C"
    return f"CPU: {progress_fmt(p)} {temp}"


def get_gpu(dev, label):
    devices = psutil.sensors_temperatures()
    if dev not in devices:
        logging.warn(f"device {dev} not found in temperature sensors '{devices.keys()}'")
        return f"GPU: {dev} not found"
    device = [d for d in devices[dev] if d.label == label]
    if not device:
        logging.warn(f"label {label} not found in temperature sensors '{[d.label for d in devices[dev]]}'")
        temp = f"temp failure"
    else:
        temp = f"{device[0].current:0.2f}°C"
    return f"GPU: {temp}"


def get_current_track(mpchost, mpcport):
    try:
        x = run(["mpc", f"--host={mpchost}", f"--port={mpcport}", "status"], capture_output=True)
        if x.returncode != 0:
            raise Exception(f"mpc failure: {x.stderr.decode()}")
        value = x.stdout.decode().strip()
        pieces = value.split("\n")
        if len(pieces) > 1:
            if len(pieces[0]) > 40:
                pieces[0] = pieces[0][:40] + "..."
            value = " ".join(pieces[:2])
        else:
            value = "Nothing is playing..."
    except Exception as e:
        logging.warn(f"Failed to run mpc: {str(e)}")
        return "Failed to search for tracks..."
    return value


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


def get_battery():
    devpath = "/sys/class/power_supply"
    devs = [os.path.join(devpath, f) for f in os.listdir(devpath) if f.startswith("BAT")]
    batfiles = [(os.path.join(dev, "capacity"), 
                 os.path.join(dev, "status")) for dev in devs]
    cap = 0.0
    count = 0
    status = "🗲"
    for cappath, statuspath in batfiles:
        count += 1
        with open(cappath, "r") as fd:
            cap += float(fd.read())
        with open(statuspath, "r") as fd:
            if fd.read().strip() == "Discharging":
                status = "▼"
    cap = (cap if count == 0 else cap / count) / 100.0
    return f"{status} {progress_fmt(cap)}"

def get_pacman_updates():
    x = run(["pacman", "-Qu"], capture_output=True)
    n = len(x.stdout.decode().splitlines())
    return "System is up to date" if n == 0 else f"{n} updates available"

def get_phone_connection():
    try:
        x = run(["adb", "devices"], capture_output=True)
    except Exception as e:
        logging.error(f"can't check phone connection: {e}")
        return "Unable to check phone connection"

    devices = x.stdout.decode().splitlines()[1:]
    if len(devices) == 0 or devices[0] == "":
        return "phone is not connected"

    def is_ip_address(device):
        if ":" not in device:
            return False
        ip, port = device.split(":")
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False

    wireless = False
    wired = False
    for line in devices:
        if line == "":
            continue
        device = line.split()[0]
        if is_ip_address(device):
            wireless = True
        else:
            wired = True
    if wireless and wired:
        return "phone connected, please disconnect"
    elif wireless:
        return "phone is connected"
    elif wired:
        return "phone is ready to be connected"

    return "unknown error"



