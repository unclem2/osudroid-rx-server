import os
import hashlib
import discord_webhook
import uuid
from objects import glob


def make_safe(n: str):
    return n.lower().replace(" ", "_")


def make_md5(n: str):
    return hashlib.md5(n.encode()).hexdigest()


def make_uuid(name: str = ""):
    return name + str(uuid.uuid4()).replace("-", "")


def check_folder():
    required_folders = ["replays", "beatmaps"]

    if not os.path.isdir("data"):
        os.mkdir("data")

    for folder in required_folders:
        if not os.path.isdir(f"data/{folder}"):
            os.mkdir(f"data/{folder}")


def check_md5(n: str, md5: str):
    return hashlib.md5(n.encode()).hexdigest() == md5


async def send_webhook(
    url, content, isEmbed=False, title=None, title_url=None, thumbnail=None, footer=None
):
    webhook = discord_webhook.AsyncDiscordWebhook(url=url)
    if isEmbed is not False:
        embed = discord_webhook.DiscordEmbed(title=title, description=content)
        embed.set_url(title_url) if title_url != None else ""
        embed.set_thumbnail(thumbnail) if thumbnail != None else ""
        embed.set_footer(footer) if footer != None else ""
        webhook.add_embed(embed)
        try:
            await webhook.execute()
        except Exception:
            return print("Error while sending webhook")
        return print("Embed Webhook sent successfully")
    webhook.set_content(content)
    try:
        await webhook.execute()
        print("Webhook sent successfully ")
    except Exception:
        return print("Error while sending webhook")
        

async def get_countries():
    countries = await glob.db.fetchall("SELECT DISTINCT country FROM users WHERE country IS NOT NULL ORDER BY country")
    return [row["country"] for row in countries]


def is_convertable(value, type):
    try:
        type(value)
        return True
    except ValueError:
        return False