import json
import re
import os
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.parse
import calendar
from ics_utils import events_to_ics


def post_calendar(start, end, res_type, cal_view, federation_ids):
    data = []
    data.append(("start", start))
    data.append(("end", end))
    data.append(("resType", str(res_type)))
    data.append(("calView", cal_view))
    for fid in federation_ids:
        data.append(("federationIds[]", fid))
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://edt.uvsq.fr/",
    }
    req = urllib.request.Request(
        "https://edt.uvsq.fr/Home/GetCalendarData",
        data=urllib.parse.urlencode(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return json.loads(text)


def calendar_json_to_events(json_list, federation_ids=None):
    evts = []
    tz = timezone.utc

    def to_utc(dt_str):
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    for item in json_list:
        modules = item.get("modules") or []
        group = None
        if federation_ids and len(federation_ids) > 0:
            group = federation_ids[0]
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
        evt = {
            "id": item.get("id"),
            "type": item.get("eventCategory") or "",
            "name": modules[0] if modules else "",
            "group": group,
            "details": "\n".join(desc_lines),
            "salle": salle,
            "start": to_utc(item.get("start")) if item.get("start") else None,
            "end": to_utc(item.get("end")) if item.get("end") else None,
            "color": (
                item.get("backgroundColor")
                or item.get("background")
                or item.get("backColor")
            ),
        }
        evts.append(evt)
    return evts


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
        last_day = calendar.monthrange(d.year, d.month)[1]
        end = d.replace(day=last_day).date()
    else:
        start = d.date()
        end = d.date()
    return start.isoformat(), end.isoformat()


def month_start_end(y, m):
    first = f"{y:04d}-{m:02d}-01"
    last_day = calendar.monthrange(y, m)[1]
    last = f"{y:04d}-{m:02d}-{last_day:02d}"
    return first, last


def fetch_year(date_str, res_type, federation_ids):
    d = datetime.fromisoformat(date_str)
    start_year = d.year if d.month >= 9 else d.year - 1
    months = list(range(9, 13)) + list(range(1, 9))
    combined = []
    seen = set()
    for m in months:
        y = start_year if m >= 9 else start_year + 1
        s, e = month_start_end(y, m)
        for it in post_calendar(s, e, res_type, "month", federation_ids):
            iid = it.get("id")
            if iid not in seen:
                seen.add(iid)
                combined.append(it)
    return combined


def run(period, date, entity_type, entity_arg, out_fname=None):
    period_to_view = {
        "day": "agendaDay",
        "week": "agendaWeek",
        "month": "month",
        "year": "year",
    }

    start, end = compute_range(period, date)
    res_map = {"module": 100, "room": 102, "group": 103}
    res_type = res_map.get(entity_type, 103)
    federation_ids = [entity_arg]

    if period == "year":
        data = fetch_year(date, res_type, federation_ids)
    else:
        data = post_calendar(
            start,
            end,
            res_type,
            period_to_view.get(period, "agendaDay"),
            federation_ids,
        )

    if not out_fname:
        out_fname = f"{entity_arg}-{period}_{date}.ics"
    events_to_ics(
        calendar_json_to_events(data, federation_ids),
        out_path=os.path.join("calendars", out_fname),
    )
