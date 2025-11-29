import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
import requests
from utils import combined_hash, download_image, insert_data
from supabase import create_client
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("TOKEN")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon or service_role
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) # type:ignore

intents = nextcord.Intents.default()
intents.message_content = True  # required to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

# Print all the contents of the message.
def print_message_details(message):
    print("\n========== MESSAGE DETAILS ==========")
    print(f"Message ID: {message.id}")
    print(f"Author: {message.author} (ID: {message.author.id})")
    print(f"Content: {message.content}")
    print(f"Channel: {message.channel} (ID: {message.channel.id})")
    print(f"Guild: {message.guild} (ID: {message.guild.id if message.guild else 'DM'})")
    print(f"Created At: {message.created_at}")
    print(f"Edited At: {message.edited_at}")

    print("\n--- Attachments ---")
    for att in message.attachments:
        print(f"  Name: {att.filename}, URL: {att.url}, Size: {att.size} bytes")

    print("\n--- Mentions ---")
    print(f"Users: {message.mentions}")
    print(f"Roles: {message.role_mentions}")
    print(f"Channels: {message.channel_mentions}")

    print("\n--- Embeds ---")
    print(message.embeds)

    print("\n--- Stickers ---")
    print(message.stickers)

    print("\n--- Reactions ---")
    print(message.reactions)

    print("\n--- Flags ---")
    print(message.flags)

    print("\n=====================================\n")

# Processes the incoming message streams
def process_msg(message):
    print(f"Processing Message {message.id}")
    msg_id = str(message.id)
    author_name = str(message.author.name)
    author_id = str(message.author.id)
    msg_content = str(message.content)
    created_at = message.created_at.isoformat()
    # edited_at = message.edited_at.isoformat()
    images_addr = []
    images_url = []
    for att in message.attachments:
        print(f"attemepting to download image")
        try:
            images_url.append(str(att.url))
            images_addr.append(download_image(att.url))
        except:
            pass
    
    # Computing the hash values
    comp_hash = combined_hash(msg_content, images_addr)

    # Saving the data to supabase
    data = {
        "msg_id" : msg_id,
        "author_name": author_name,
        "author_id": author_id,
        "final_hash": comp_hash,
        "msg_content": msg_content,
        "msg_sent_at": created_at,
        "images": images_url,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    print(data)

    res = insert_data(data, supabase=supabase)
    print(res)
    
    
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


# Read every message in server
@bot.event
async def on_message(message):
    # Prevent bot from responding to itself
    if message.author == bot.user:
        return
    
    process_msg(message=message)

    # Example: bot replies if someone says "hello"
    if "hello" in message.content.lower():
        await message.channel.send("Hello! 👋")

    # Needed so commands still work
    await bot.process_commands(message)


# Simple command example
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def about(ctx):
    """Tells what this bot does."""
    about_text = (
        "**🤖 About This Bot**\n"
        "- Reads messages in the server\n"
        "- Runs an algorithm to keep check on what msgs are getting viral\n"
        "- Fact Checks the claims of viral posts and verify their truth\n"
        "- Created using **nextcord** and **Python**"
    )
    await ctx.send(about_text)


bot.run(TOKEN) #type:ignore
