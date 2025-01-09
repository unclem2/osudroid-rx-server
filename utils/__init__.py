import os
import hashlib
import uuid
from discord_webhook import AsyncDiscordWebhook


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


async def send_webhook(isEmbed=False, url, content):
  webhook = AsyncDiscordWebhook(url=url)
  if isEmbed is not False:
    webhook.add_embed(content)
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
