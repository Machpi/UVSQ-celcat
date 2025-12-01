from datetime import datetime, timedelta, timezone
from celcat2ics import post_calendar, calendar_json_to_events
from typing import Dict


def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and a_end > b_start


def rooms_day_morning_evening(date_str, rooms):
    morning = (8, 13)
    evening = (13, 18)
    tz = tz = timezone.utc
    results = {}

    d = datetime.fromisoformat(date_str).date()
    dn = d + timedelta(days=1)

    def window(h0, h1):
        return (
            datetime(d.year, d.month, d.day, h0, 0, tzinfo=tz),
            datetime(d.year, d.month, d.day, h1, 0, tzinfo=tz),
        )

    m_start, m_end = window(morning[0], morning[1])
    e_start, e_end = window(evening[0], evening[1])

    resType = 102
    calView = "agendaDay"

    for r in rooms:
        federationIds = [r]
        data = post_calendar(
            d.isoformat(), dn.isoformat(), resType, calView, federationIds
        )
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

        results[r] = {
            "morning": morning_busy,
            "evening": evening_busy,
            "events": events,
        }
    return results


def _colored_icon(icon: str, is_free: bool):
    GREEN = "\x1b[32m"
    RED = "\x1b[31m"
    RESET = "\x1b[0m"
    return f"{GREEN}{icon}{RESET}  " if is_free else f"{RED}{icon}{RESET}  "


def print_availability(info: Dict[str, Dict]):
    if not info:
        print("Aucune salle à afficher.")
        return
    max_len = max((len(name) for name in info.keys()), default=0)
    for r, v in info.items():
        morning_free = not bool(v.get("morning"))
        evening_free = not bool(v.get("evening"))
        sun = _colored_icon("𖤓", morning_free)
        moon = _colored_icon("☾", evening_free)
        name_aligned = r.ljust(max_len)
        print(f"{name_aligned}  {sun}{moon}")
