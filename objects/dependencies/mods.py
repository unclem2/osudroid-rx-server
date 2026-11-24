import json

from fastapi import Depends, Query
from osudroid_api_wrapper import ModList


def get_mod_entries(mods: str | None = Query(None)) -> list[dict]:
    if not mods:
        return []
    try:
        entries = json.loads(mods)
    except json.JSONDecodeError:
        return []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict) and entry.get("acronym")]


def get_modlist(mod_entries: list[dict] = Depends(get_mod_entries)) -> ModList | None:
    return ModList.from_dict(mod_entries) if mod_entries else None
