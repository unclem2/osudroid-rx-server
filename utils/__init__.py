import os
import hashlib
import uuid
import aiohttp

def make_safe(n: str):
    return n.lower().replace(' ', '_')

def make_md5(n: str):
    return hashlib.md5(n.encode()).hexdigest()

def make_uuid(name: str = ''):
    return name + str(uuid.uuid4()).replace('-', '')

def check_folder():
    required_folders = ['replays', 'beatmaps']

    if not os.path.isdir('data'):
        os.mkdir('data')

    for folder in required_folders:
        if not os.path.isdir(f'data/{folder}'):
            os.mkdir(f'data/{folder}')

def check_md5(n:str, md5: str):
    return hashlib.md5(n.encode()).hexdigest() == md5

async def discord_notify(message: str, webhook: str):
    async with aiohttp.ClientSession() as session:
        webhook_data = {
            "content": message
        }
        async with session.post(webhook, json=webhook_data) as response:
            if response.status != 204:
                print(f"Failed to send webhook: {response.status}")
            else:
                print("Webhook sent successfully")


