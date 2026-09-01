import discord
import requests    
from dotenv import load_dotenv
import os
load_dotenv(override=True)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'chatbot is online')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print("\nYOU: ",message.content,"\n")
    resp = requests.post("http://localhost:8000/message",json={"source":"discord","content":message.content})
    await message.channel.send(resp.json()["reply"])
    print(resp.json()["reply"])

client.run( os.getenv('discord_api_key') )
