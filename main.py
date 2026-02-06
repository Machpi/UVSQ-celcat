#!/usr/bin/env python3
import os
import platform
import sys
from datetime import datetime
from celcat2ics import run
from room_availability import pre_process, print_availability
from fetch_rooms import get_rooms, write_rooms_cfg

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import tty
    import termios


def clear():
    print("\x1b[2J\x1b[H", end="")


def getch():
    if platform.system() == "Windows":
        ch = msvcrt.getwch()
        if ch == "\x03":
            raise KeyboardInterrupt
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return f"[{ord(ch2)}]"
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x1b":
                next1 = sys.stdin.read(1)
                if next1 == "[":
                    next2 = sys.stdin.read(1)
                    return f"\x1b[{next2}"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def select_menu(prompt, options, start_idx=0):
    idx = start_idx
    while True:
        clear()
        print(prompt + ":")
        for i, opt in enumerate(options):
            prefix = "→ " if i == idx else "  "
            print(f"{prefix}{opt}")
        k = getch()
        if k in ("\x1b[A", "[72]"):
            idx = (idx - 1) % len(options)
        elif k in ("\x1b[B", "[80]"):
            idx = (idx + 1) % len(options)
        elif k in ("\r", "\n", "\x0d"):
            return options[idx]
    clear()


def cl_input(prompt):
    clear()
    return input(prompt)


def verify_date(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str)
        if date_obj.weekday() == 6:
            print("Le campus est fermé le dimanche.")
            sys.exit(1)
        return date_obj
    except ValueError:
        print("Format de date invalide. Utilisez AAAA-MM-JJ.")
        sys.exit(1)


def generate_ics():
    period = select_menu("Période ", ["day", "week", "month", "year"])
    today = datetime.now().date().isoformat()
    date_input = cl_input(f"Date [{today}] : ").strip()
    date = date_input or today
    verify_date(date)
    etype = select_menu("Type ", ["module", "room", "group"], start_idx=2)
    default_args = {
        "group": "M2 Secrets",
        "room": "122 - DESCARTES (MASTER)",
        "module": "MYSEC304",
    }
    default_arg = default_args.get(etype, "")
    earg = cl_input(f"{etype.capitalize()} [{default_arg}] : ").strip() or default_arg
    default_cal_name = f"{earg}-{period}_{date}"
    cal_name = (
        cl_input(f"Nom du calendrier [{default_cal_name}] : ").strip()
        or default_cal_name
    )

    base = os.path.basename(cal_name)
    if not base.lower().endswith(".ics"):
        base += ".ics"
    run(period, date, etype, earg, out_fname=base)
    clear()
    sys.exit(0)


def generate_cfg():
    rooms = get_rooms()
    depts = {}
    for r in rooms:
        dept = None
        if isinstance(r, dict):
            raw = r.get("raw")
            if isinstance(raw, dict):
                dept = raw.get("dept")
            if not dept:
                dept = r.get("dept")
        if dept:
            d = str(dept).strip()
            if d:
                depts[d] = depts.get(d, 0) + 1
    dept_options = ["Tous"]
    display_to_dept = {}
    if depts:
        for k in sorted(depts.keys()):
            display = f"{k} ({depts[k]})"
            dept_options.append(display)
            display_to_dept[display] = k
    chosen_display = select_menu("Choisir un département (ou Tous)", dept_options)
    if chosen_display == "Tous":
        chosen_dept = "Tous"
    else:
        chosen_dept = display_to_dept.get(chosen_display, chosen_display)
    cfg_dir = "configs"
    os.makedirs(cfg_dir, exist_ok=True)
    default_name = "rooms.txt"
    if chosen_dept != "Tous":
        str_dept = "".join(
            c for c in chosen_dept if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        str_dept = str_dept.replace(" ", "_") or str_dept
        default_name = f"rooms_{str_dept}.txt"
    name = cl_input(f"Nom du fichier [{default_name}] : ").strip() or default_name
    out_path = os.path.join(cfg_dir, name)
    filtered_rooms = []
    if chosen_dept == "Tous":
        filtered_rooms = rooms
    else:
        for r in rooms:
            dept = None
            if isinstance(r, dict):
                raw = r.get("raw")
                if isinstance(raw, dict):
                    dept = raw.get("dept")
                if not dept:
                    dept = r.get("dept")
            if dept and str(dept).strip() == chosen_dept:
                filtered_rooms.append(r)
    write_rooms_cfg(filtered_rooms, out_path)
    clear()
    sys.exit(0)


def find_rooms():
    today = datetime.now().date().isoformat()
    date_input = cl_input(f"Date [{today}] : ").strip()
    date = date_input or today
    verify_date(date)
    cfg_dir = "configs"
    rooms = []
    cfg_files = [
        f for f in os.listdir(cfg_dir) if os.path.isfile(os.path.join(cfg_dir, f))
    ]
    if not cfg_files:
        print("Aucun fichier de configuration trouvé")
        sys.exit(1)
    choice = select_menu("Choisir une config", cfg_files)
    cfg_path = os.path.join(cfg_dir, choice)
    if not os.path.exists(cfg_path):
        print(f"Le fichier '{choice}' n'existe pas.")
        sys.exit(1)
    (rooms, max_len) = pre_process(cfg_path)
    if rooms == 0:
        print(f"La config '{choice}' est vide ou invalide.")
        sys.exit(1)
    clear()
    print_availability(date, cfg_path, max_len)
    sys.exit(0)


def interactive_menu():
    options = [
        "Générer un .ics",
        "Générer un fichier de config",
        "Trouver des salles libres",
        "Quitter",
    ]
    idx = 0
    try:
        while True:
            clear()
            for i, opt in enumerate(options):
                prefix = "→ " if i == idx else "  "
                print(f"{prefix}{opt}")
            k = getch()
            if k in ("\x1b[A", "[72]"):
                idx = (idx - 1) % len(options)
            elif k in ("\x1b[B", "[80]"):
                idx = (idx + 1) % len(options)
            elif k in ("\r", "\n", "\x0d"):
                choice = options[idx]
                if choice.startswith("Générer un ."):
                    generate_ics()
                elif choice.startswith("Générer"):
                    generate_cfg()
                elif choice.startswith("Trouver"):
                    find_rooms()
                else:
                    break
    except KeyboardInterrupt:
        clear()


if __name__ == "__main__":
    interactive_menu()
