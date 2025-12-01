import json
import re
from datetime import datetime, timezone, timedelta
from ics_utils import events_to_ics


def post_calendar(start, end, resType, calView, federationIds, colourScheme=3):
    import urllib.request, urllib.parse

    url = "https://edt.uvsq.fr/Home/GetCalendarData"
    data = []
    data.append(("start", start))
    data.append(("end", end))
    data.append(("resType", str(resType)))
    data.append(("calView", calView))
    data.append(("colourScheme", str(colourScheme)))
    for fid in federationIds:
        data.append(("federationIds[]", fid))
    encoded = urllib.parse.urlencode(data)
    body = encoded.encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://edt.uvsq.fr/",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return json.loads(text)


def calendar_json_to_events(json_list, federationIds=None):
    evts = []
    tz = timezone.utc

    def to_utc(dt_str):
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    for item in json_list:
        eid = item.get("id")
        start = to_utc(item.get("start")) if item.get("start") else None
        end = to_utc(item.get("end")) if item.get("end") else None
        color = (
            item.get("backgroundColor")
            or item.get("background")
            or item.get("backColor")
        )
        ev_type = item.get("eventCategory") or ""
        modules = item.get("modules") or []
        name = modules[0] if modules else ""
        group = None
        if federationIds and len(federationIds) > 0:
            group = federationIds[0]
        desc_html = item.get("description") or ""
        desc_text = re.sub(r"<br\s*/?>", "\n", desc_html)
        desc_text = re.sub(r"<[^>]+>", "", desc_text)
        desc_lines = [ln.strip() for ln in desc_text.splitlines() if ln.strip()]
        salle = ""
        for ln in desc_lines:
            if "Salle" in ln or (" - " in ln and any(ch.isdigit() for ch in ln)):
                salle = ln
                break
        if not salle:
            sites = item.get("sites") or []
            if sites:
                salle = sites[0]
        details = "\n".join(desc_lines)
        evt = {
            "id": eid,
            "type": ev_type,
            "name": name,
            "group": group,
            "details": details,
            "salle": salle,
            "start": start,
            "end": end,
            "color": color,
        }
        evts.append(evt)
    return evts


def run(period, date, entity_type, entity_arg, out_fname=None):
    period_to_view = {
        "day": "agendaDay",
        "week": "agendaWeek",
        "month": "month",
        "year": "year",
    }
    calView = period_to_view.get(period, "agendaDay")
    import calendar as _calendar

    def compute_range(period, date_str):
        d = datetime.fromisoformat(date_str)
        if period == "day":
            start = d.date()
            end = d.date() + timedelta(days=1)
        elif period == "week":
            start = (d - timedelta(days=d.weekday())).date()
            end = start + timedelta(days=6)
        elif period == "month":
            start = d.replace(day=1).date()
            last_day = _calendar.monthrange(d.year, d.month)[1]
            end = d.replace(day=last_day).date()
        else:
            start = d.date()
            end = d.date()
        return start.isoformat(), end.isoformat()

    start, end = compute_range(period, date)
    res_map = {"module": 100, "room": 102, "group": 103}
    resType = res_map.get(entity_type, 103)
    federationIds = [entity_arg]

    def month_start_end(y, m):
        import calendar as _calendar

        first = f"{y:04d}-{m:02d}-01"
        last_day = _calendar.monthrange(y, m)[1]
        last = f"{y:04d}-{m:02d}-{last_day:02d}"
        return first, last

    def fetch_year(date_str, resType, federationIds):
        d = datetime.fromisoformat(date_str)
        start_year = d.year if d.month >= 9 else d.year - 1
        months = list(range(9, 13)) + list(range(1, 9))
        combined = []
        seen = set()
        for m in months:
            y = start_year if m >= 9 else start_year + 1
            s, e = month_start_end(y, m)
            try:
                part = post_calendar(s, e, resType, "month", federationIds)
            except Exception as exc:
                print(f"Failed month {y}-{m:02d}:", exc)
                continue
            for it in part:
                iid = it.get("id")
                if iid in seen:
                    continue
                seen.add(iid)
                combined.append(it)
        return combined

    if period == "year":
        data = fetch_year(date, resType, federationIds)
    else:
        data = post_calendar(start, end, resType, calView, federationIds)
    events = calendar_json_to_events(data, federationIds)

    if not out_fname:
        out_path = f"{entity_arg}-{period}_{date}.ics"
    out_path = "calendars/" + out_fname
    events_to_ics(events, out_path=out_path)
