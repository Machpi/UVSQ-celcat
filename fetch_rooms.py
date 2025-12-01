from typing import List, Dict
import requests


def get_rooms():
    session = requests.Session()
    url = "https://edt.uvsq.fr/Home/ReadResourceListItems"
    params = {
        "myResources": "false",
        "searchTerm": "-",
        "pageSize": "500",
        "pageNumber": "1",
        "resType": "102",
        "secondaryFilterValue1": "",
        "secondaryFilterValue2": "",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://edt.uvsq.fr",
    }

    resp = session.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results: List[Dict] = []
    for key in ("items", "rows", "data", "results"):
        if key in data and isinstance(data[key], list):
            data_list = data[key]
            break
    for item in data_list:
        id = item.get("id")
        name = item.get("name")
        results.append({"id": id, "name": name or str(item), "raw": item})
    return results


def write_rooms_cfg(rooms, out_path):
    with open(out_path, "w", encoding="utf-8") as fh:
        for r in rooms:
            line = str(r.get("id"))
            fh.write(line + "\n")
