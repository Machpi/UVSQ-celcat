from datetime import datetime, timedelta, timezone
from celcat2ics import post_calendar, calendar_json_to_events


def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and a_end > b_start


def single_room_availability(date_str, room):
    tz = timezone.utc
    d = datetime.fromisoformat(date_str).date()
    dn = d + timedelta(days=1)

    m_start = datetime(d.year, d.month, d.day, 8, 0, tzinfo=tz)
    m_end = datetime(d.year, d.month, d.day, 13, 0, tzinfo=tz)
    e_start = datetime(d.year, d.month, d.day, 13, 0, tzinfo=tz)
    e_end = datetime(d.year, d.month, d.day, 18, 0, tzinfo=tz)

    resType = 102
    calView = "agendaDay"
    federationIds = [room]
    data = post_calendar(d.isoformat(), dn.isoformat(), resType, calView, federationIds)
    morning_busy = False
    evening_busy = False
    events = []
    if isinstance(data, list) and data:
        events = calendar_json_to_events(data, federationIds)
        for ev in events:
            s = ev.get("start")
            e = ev.get("end")
            if not s or not e:
                continue
            s_local = s.astimezone(tz)
            e_local = e.astimezone(tz)

            if overlaps(s_local, e_local, m_start, m_end):
                morning_busy = True
            if overlaps(s_local, e_local, e_start, e_end):
                evening_busy = True
    return (morning_busy, evening_busy)


def _colored_icon(icon: str, is_busy: bool):
    GREEN = "\x1b[32m"
    RED = "\x1b[31m"
    RESET = "\x1b[0m"
    return f"{GREEN}{icon}{RESET}  " if not is_busy else f"{RED}{icon}{RESET}  "


def subtitle(text, max_len):
    UNDERLINE = "\x1b[4m"
    RESET = "\x1b[0m"
    spaces = " " * ((max_len + 6 - len(text)) // 2)
    print(f"{spaces}{UNDERLINE}{text}{RESET}{spaces}")


def title(text, max_len):
    BOLD = "\x1b[1m"
    UNDERLINE = "\x1b[4m"
    RESET = "\x1b[0m"
    spaces = " " * ((max_len + 6 - len(text)) // 2)
    print(f"{BOLD}{UNDERLINE}{spaces}{text}{spaces}{RESET}")


def pre_process(cfg):
    rooms = []
    max_len = 0
    for line in open(cfg, "r", encoding="utf-8"):
        if not line or line.startswith("#"):
            continue
        rooms.append(line)
        if len(line) > max_len:
            max_len = len(line)
    return rooms, max_len


def print_availability(date, cfg, max_len):
    for line in open(cfg, "r", encoding="utf-8"):
        line = line.rstrip("\n")
        if line == "":
            print()
            continue
        if line.startswith("##"):
            subtitle(line[2:].strip(), max_len)
            continue
        if line.startswith("#"):
            title(line[1:].strip(), max_len)
            continue
        (morning_busy, evening_busy) = single_room_availability(date, line)
        sun = _colored_icon("𖤓", morning_busy)
        moon = _colored_icon("☾", evening_busy)
        name_aligned = line.rstrip("\n").ljust(max_len)
        print(f"{name_aligned}  {sun}{moon}")
