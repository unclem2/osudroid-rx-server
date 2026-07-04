import logging
import os
import time

from fastapi import APIRouter, Request
from argon2 import PasswordHasher
import geoip2.database

from objects import glob
from handlers.response import Failed, Success
import utils
from objects.player import Player

ph = PasswordHasher()
router = APIRouter()

php_file = True


@router.post("")
async def login(request: Request):
    form = await request.form()

    if "username" not in form or len(form["username"]) == 0:
        return Failed("Invalid username.")

    p: Player = glob.players.get(username=form["username"])

    if not p:
        return Failed("User not found.")
    if int(form["version"]) != int(glob.config.online_version):
        return Failed("This client is outdated")

    if glob.config.maintenance == True:
        return Failed("Maintenance")

    res = await glob.db.fetch(
        "SELECT password_hash, status FROM users WHERE id = $1", [p.id]
    )
    status = res["status"]
    pswd_hash = res["password_hash"]
    hashes = glob.cache["hashes"]

    if pswd_hash in hashes:
        if form["password"] != hashes[pswd_hash]:
            return Failed("Wrong password.")
    else:
        try:
            ph.verify(pswd_hash, form["password"])
        except Exception:
            return Failed("Wrong password.")

        hashes[pswd_hash] = form["password"]

    if status != 0:
        return Failed("Banned.")

    p.last_online = time.time()

    if not p.uuid:
        p.uuid = utils.make_uuid(p.username)

    if os.path.isfile(f"data/avatar/{p.id}.png"):
        p.avatar = f"{glob.config.host}/user/avatar/{p.id}.png"
    else:
        p.avatar = f"https://s.gravatar.com/avatar/{p.email_hash}"
    try:
        if p.country == None:
            if os.path.exists("GeoLite2-Country.mmdb"):
                with geoip2.database.Reader("GeoLite2-Country.mmdb") as reader:
                    ip = request.client.host
                    response = reader.country(ip)
                    country = response.country.iso_code
                    await glob.db.execute(
                        "UPDATE users SET country = $1 WHERE id = $2",
                        [country, p.id],
                    )
                    p.country = country
    except Exception as e:
        logging.error(f"Failed to get country from ip: {e}")

    return Success(
        "{id} {uuid} {rank} {legacy_metric} {score} {pp} {acc} {username} {avatar}".format(
            id=p.id,
            uuid=p.uuid,
            rank=p.stats.pp_rank if glob.config.pp else p.stats.score_rank,
            legacy_metric=int(p.stats.pp if glob.config.pp else p.stats.rscore)
            if glob.config.legacy == True
            else "",
            score=p.stats.rscore if glob.config.legacy == False else "",
            pp=p.stats.pp if glob.config.legacy == False else "",
            acc=p.stats.droid_acc,
            username=p.username,
            avatar=p.avatar,
        )
    )
