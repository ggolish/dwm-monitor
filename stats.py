import datetime


def get_date():
    d = datetime.datetime.now()
    return d.strftime("%a %x %I:%M:%S %p")
