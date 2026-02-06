"""Module pour vérifier la disponibilité des salles."""

from datetime import datetime, timedelta, timezone
from celcat2ics import post_calendar, calendar_json_to_events


def overlaps(a_start, a_end, b_start, b_end):
    """Vérifie si deux plages horaires se chevauchent."""
    return a_start < b_end and a_end > b_start


def single_room_availability(date_str, room):
    """Vérifie la disponibilité d'une salle pour une journée (matin et après-midi)."""
    tz = timezone.utc
    d = datetime.fromisoformat(date_str).date()
    dn = d + timedelta(days=1)

    federation_ids = [room]
    data = post_calendar(
        d.isoformat(), dn.isoformat(), 102, "agendaDay", federation_ids
    )
    events = []
    if isinstance(data, list) and data:
        events = calendar_json_to_events(data, federation_ids)
        for ev in events:
            s = ev.get("start")
            e = ev.get("end")
            if not s or not e:
                continue
            s_local = s.astimezone(tz)
            e_local = e.astimezone(tz)

            return (
                overlaps(
                    s_local,
                    e_local,
                    datetime(d.year, d.month, d.day, 8, 0, tzinfo=tz),
                    datetime(d.year, d.month, d.day, 13, 0, tzinfo=tz),
                ),
                overlaps(
                    s_local,
                    e_local,
                    datetime(d.year, d.month, d.day, 13, 0, tzinfo=tz),
                    datetime(d.year, d.month, d.day, 18, 0, tzinfo=tz),
                ),
            )
    return (False, False)


def _colored_icon(icon: str, is_busy: bool):
    """Retourne une icône colorée selon la disponibilité."""
    green = "\x1b[32m"
    red = "\x1b[31m"
    reset = "\x1b[0m"
    return f"{green}{icon}{reset}  " if not is_busy else f"{red}{icon}{reset}  "


def subtitle(text, max_len):
    """Affiche un sous-titre (souligné et centré)."""
    underline = "\x1b[4m"
    reset = "\x1b[0m"
    spaces = " " * ((max_len + 6 - len(text)) // 2)
    print(f"{spaces}{underline}{text}{reset}{spaces}")


def title(text, max_len):
    """Affiche un titre (gras, souligné et centré)."""
    bold = "\x1b[1m"
    underline = "\x1b[4m"
    reset = "\x1b[0m"
    spaces = " " * ((max_len + 6 - len(text)) // 2)
    print(f"{bold}{underline}{spaces}{text}{spaces}{reset}")


def pre_process(cfg):
    """Prétraite un fichier de config pour extraire le nombre de salles et le nom le plug long."""
    rooms = 0
    max_len = 0
    with open(cfg, "r", encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            rooms += 1
            max_len = max(max_len, len(line.rstrip("\n")))
    return rooms, max_len


def print_availability(date, cfg, max_len):
    """Affiche la disponibilité de toutes les salles du fichier de config."""
    with open(cfg, "r", encoding="utf-8") as f:
        for line in f:
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
