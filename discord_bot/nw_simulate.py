import nextcord
from nextcord.ext import commands
import json
import random
import os
from dotenv import load_dotenv
import asyncio
import time

load_dotenv()
TOKEN = os.getenv("NetToken")

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

REAL_NEWS = []
FAKE_NEWS = []

DATASET_DIR = r"C:\GithubRepos\MumbaiHacks25\dataset"

# -----------------------------
#  Global simulation parameters
# -----------------------------

# Burst window time (10–25 seconds)
BURST_DURATION_RANGE = (10, 25)

# Within a burst, fake posts spacing (1–3 seconds)
FAKE_BURST_INTERVAL_RANGE = (1.0, 3.0)

# Each burst sends 1–2 seed reposts
FAKE_BURST_POST_COUNT_RANGE = (1, 2)

# Calm period window (20–45 seconds)
CALM_DURATION_RANGE = (20, 45)

# Calm period post interval (6–12 seconds)
CALM_INTERVAL_RANGE = (6.0, 12.0)


# -----------------------------
#  Dataset loader
# -----------------------------
def load_dataset():
    global REAL_NEWS, FAKE_NEWS
    with open(os.path.join(DATASET_DIR, "real_news.json"), "r", encoding="utf-8") as f:
        REAL_NEWS = json.load(f)
    with open(os.path.join(DATASET_DIR, "fake_news.json"), "r", encoding="utf-8") as f:
        FAKE_NEWS = json.load(f)


@bot.event
async def on_ready():
    load_dataset()
    print("Bot online:", bot.user)
    print(f"Loaded {len(REAL_NEWS)} real and {len(FAKE_NEWS)} fake articles.")


current_channel = None
simulation_running = False

# ------------------------------
# SIMULATION ENGINE
# ------------------------------
async def simulation_loop():
    global simulation_running

    while simulation_running:
        # Burst of 1–2 fake posts inside a burst window
        await run_fake_viral_burst()
        # Then calm period of real news
        await run_calm_period()

    print("Simulation ended.")


async def run_fake_viral_burst():
    global current_channel

    burst_duration = random.randint(*BURST_DURATION_RANGE)
    end_time = time.time() + burst_duration

    print(f"[BURST] Burst window started ({burst_duration}s).")

    # Pick a seed fake article (fallback to real if no fake)
    if FAKE_NEWS:
        seed = random.choice(FAKE_NEWS)
    elif REAL_NEWS:
        seed = random.choice(REAL_NEWS)
    else:
        print("[BURST] No articles available.")
        await asyncio.sleep(burst_duration)
        return

    # Decide how many fake posts to send (1–2)
    post_count = random.randint(*FAKE_BURST_POST_COUNT_RANGE)
    print(f"[BURST] Sending {post_count} fake posts...")

    for _ in range(post_count):
        if not simulation_running:
            break

        await send_post(seed)
        await asyncio.sleep(random.uniform(*FAKE_BURST_INTERVAL_RANGE))

    # Silent until burst window ends
    remaining = end_time - time.time()
    if remaining > 0:
        print(f"[BURST] Silent phase for {remaining:.1f}s")
        await asyncio.sleep(remaining)

    print("[BURST] Burst window ended.")


async def run_calm_period():
    """
    Calm period: only real news (if available), slower posting.
    """
    global current_channel

    calm_duration = random.randint(*CALM_DURATION_RANGE)
    end_time = time.time() + calm_duration

    print(f"[CALM] Stable period for {calm_duration}s")

    while simulation_running and time.time() < end_time:
        if REAL_NEWS:
            article = random.choice(REAL_NEWS)
        elif FAKE_NEWS:  # fallback if no real news
            article = random.choice(FAKE_NEWS)
        else:
            print("[CALM] No articles available.")
            break

        await send_post(article)
        await asyncio.sleep(random.uniform(*CALM_INTERVAL_RANGE))

    print("[CALM] Ended stable period.")


async def send_post(article):
    """
    Sends the article's text and attachments (images) to current_channel.
    """
    if current_channel is None:
        return

    text = article.get("news", "No content")
    images = article.get("images", [])

    file_objects = []
    for img_path in images:
        abs_path = os.path.join(DATASET_DIR, "images", os.path.basename(img_path))
        if os.path.exists(abs_path):
            file_objects.append(nextcord.File(abs_path, filename=os.path.basename(abs_path)))
        else:
            print("Image not found:", abs_path)

    try:
        if file_objects:
            await current_channel.send(content=text, files=file_objects)
        else:
            await current_channel.send(content=text)
    except Exception as e:
        print("Error sending post:", e)


# ------------------------------
# COMMANDS
# ------------------------------
@bot.command()
async def start(ctx):
    global current_channel, simulation_running

    if simulation_running:
        return await ctx.send("Simulation already running!")

    current_channel = ctx.channel
    simulation_running = True

    await ctx.send("Simulation started — Fake bursts + real calm periods enabled.")
    bot.loop.create_task(simulation_loop())


@bot.command()
async def stop(ctx):
    global simulation_running
    simulation_running = False
    await ctx.send("Simulation stopped.")


bot.run(TOKEN)  # type: ignore
