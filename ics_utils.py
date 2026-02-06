"""Module utilitaire pour générer des fichiers ICS."""

from io import BytesIO
import uuid
from datetime import datetime, timezone
import os


def fmt(dt):
    """Formate un datetime au format ICS."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def events_to_ics(events, out_path=None):
    """Convertit une liste d'événements en fichier ICS."""
    if out_path is None:
        out_path = os.path.join("calendars", "calendar.ics")
    buf = BytesIO()

    buf.write("BEGIN:VCALENDAR\n".encode("utf-8"))
    buf.write("VERSION:2.0\n".encode("utf-8"))
    buf.write("PRODID:-//UVSQ-celcat//EN\n".encode("utf-8"))
    for e in events:
        uid = f"{fmt(datetime.now(timezone.utc))}-{uuid.uuid4()}@uvsq"
        buf.write("BEGIN:VEVENT\n".encode("utf-8"))
        buf.write((f"UID:{uid}\n").encode("utf-8"))
        buf.write((f"DTSTAMP:{fmt(datetime.now(timezone.utc))}\n").encode("utf-8"))
        if e.get("start"):
            buf.write((f"DTSTART:{fmt(e['start'])}\n").encode("utf-8"))
        if e.get("end"):
            buf.write((f"DTEND:{fmt(e['end'])}\n").encode("utf-8"))
        buf.write((f"LOCATION:{e.get('salle', '')}\n").encode("utf-8"))
        desc = (e.get("details") or "").replace("\n", "\\n")
        buf.write((f"DESCRIPTION:{desc}\n").encode("utf-8"))
        summary = e.get("type", "")
        if e.get("name"):
            summary = summary + " - " + e.get("name") if summary else e.get("name")
        buf.write((f"SUMMARY:{summary}\n").encode("utf-8"))
        buf.write("TRANSP:OPAQUE\n".encode("utf-8"))
        buf.write("END:VEVENT\n".encode("utf-8"))
    buf.write("END:VCALENDAR".encode("utf-8"))
    data = buf.getvalue()
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    return data
