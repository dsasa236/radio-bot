import discord
from discord.ext import commands
import json
import os
import random

# ===== LOAD CONFIG =====
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TOKEN = config.get("TOKEN")
    if not TOKEN:
        raise ValueError("TOKEN ไม่มีใน config.json")
except Exception as e:
    print(f"❌ โหลด config.json ไม่ได้: {e}")
    exit()

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATA =====
def load_data():
    if not os.path.exists("characters.json"):
        return {}
    with open("characters.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open("characters.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ===== CHARACTER =====
def create_character(name):
    return {
        "name": name,
        "hp": 100,
        "maxhp": 100,
        "atk": 10,
        "def": 5,
        "spd": 3,
        "lv": 1,
        "exp": 0,
        "gold": 0,
        "weapon": None,
        "armor": None
    }

# ===== ITEM SYSTEM =====
weapons = [
    {"name": "ไม้", "atk": 2},
    {"name": "ดาบเหล็ก", "atk": 5},
    {"name": "ดาบอัศวิน", "atk": 10},
]

armors = [
    {"name": "เสื้อผ้า", "def": 2},
    {"name": "เกราะหนัง", "def": 5},
    {"name": "เกราะเหล็ก", "def": 10},
]

def drop_item():
    if random.random() < 0.5:
        return random.choice(weapons), "weapon"
    else:
        return random.choice(armors), "armor"

# ===== MONSTER =====
def generate_monster():
    monsters = [
        {"name": "Slime", "hp": 30, "atk": 5, "def": 2, "exp": 20, "gold": 10},
        {"name": "Goblin", "hp": 50, "atk": 8, "def": 3, "exp": 35, "gold": 20},
        {"name": "Wolf", "hp": 70, "atk": 12, "def": 4, "exp": 50, "gold": 30},
        {"name": "Orc", "hp": 100, "atk": 15, "def": 6, "exp": 80, "gold": 50},
    ]
    return random.choice(monsters).copy()

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์: {bot.user}")

# ===== CREATE =====
@bot.command()
async def create(ctx, slot: int, name: str):
    if slot < 1 or slot > 3:
        return await ctx.send("❌ เลือก slot 1-3")

    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"slots": [None, None, None]}

    if slot == 3:
        total_lv = sum(char.get("lv",0) for char in data[user_id]["slots"] if char)
        if total_lv < 10:
            return await ctx.send("🔒 Slot 3 ต้องเลเวลรวม 10")

    if data[user_id]["slots"][slot-1]:
        return await ctx.send("❌ ช่องนี้มีตัวแล้ว")

    data[user_id]["slots"][slot-1] = create_character(name)
    save_data(data)
    await ctx.send(f"✅ สร้าง {name} สำเร็จ!")

# ===== PROFILE =====
@bot.command()
async def profile(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        return await ctx.send("❌ ไม่มีตัวละคร")

    embed = discord.Embed(title="📜 ตัวละครของคุณ", color=0x00ff00)
    for i, char in enumerate(data[user_id]["slots"], start=1):
        if char:
            weapon_name = char.get("weapon", {}).get("name", "-") if char.get("weapon") else "-"
            armor_name = char.get("armor", {}).get("name", "-") if char.get("armor") else "-"
            embed.add_field(
                name=f"[{i}] {char.get('name','?')} Lv.{char.get('lv',1)}",
                value=f"❤️ HP: {char.get('hp',0)}/{char.get('maxhp',0)}\n"
                      f"⚔️ ATK: {char.get('atk',0)} (อาวุธ: {weapon_name})\n"
                      f"🛡️ DEF: {char.get('def',0)} (เกราะ: {armor_name})\n"
                      f"💰 Gold: {char.get('gold',0)}\n"
                      f"✨ EXP: {char.get('exp',0)}/100",
                inline=False
            )
        else:
            if i == 3:
                embed.add_field(name=f"[{i}] 🔒 Locked", value="ต้องเลเวลรวม 10", inline=False)
            else:
                embed.add_field(name=f"[{i}] ว่าง", value="ยังไม่มีตัวละคร", inline=False)

    await ctx.send(embed=embed)

# ===== HUNT =====
@bot.command()
async def hunt(ctx, slot: int):
    if slot < 1 or slot > 3:
        return await ctx.send("❌ เลือก slot 1-3")

    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        return await ctx.send("❌ ไม่มีตัวละคร")

    char = data[user_id]["slots"][slot-1]
    if not char:
        return await ctx.send("❌ ช่องว่าง")

    atk = char.get("atk",0) + (char.get("weapon",{}).get("atk",0) if char.get("weapon") else 0)
    defense = char.get("def",0) + (char.get("armor",{}).get("def",0) if char.get("armor") else 0)
    monster = generate_monster()

    log = f"⚔️ เจอ {monster['name']}!\n"
    while char.get("hp",0) > 0 and monster["hp"] > 0:
        dmg = max(1, atk - monster.get("def",0))
        monster["hp"] -= dmg
        log += f"🗡️ คุณตี {dmg} HP มอนเหลือ {max(monster['hp'],0)}\n"
        if monster["hp"] <= 0: break
        dmg = max(1, monster.get("atk",0) - defense)
        char["hp"] -= dmg
        log += f"💥 มอนตี {dmg} HP คุณเหลือ {max(char.get('hp',0),0)}\n"

    if char.get("hp",0) > 0:
        char["exp"] = char.get("exp",0) + monster.get("exp",0)
        char["gold"] = char.get("gold",0) + monster.get("gold",0)
        log += f"\n🏆 ชนะ! +{monster.get('exp',0)} EXP +{monster.get('gold',0)} Gold\n"

        if random.random() < 0.4:
            item, t = drop_item()
            log += f"🎁 ดรอป: {item['name']}\n"
            char[t] = item

        # LEVEL UP
        while char.get("exp",0) >= 100:
            char["exp"] -= 100
            char["lv"] = char.get("lv",1)+1
            char["maxhp"] = char.get("maxhp",100)+20
            char["atk"] = char.get("atk",10)+3
            char["def"] = char.get("def",5)+2
            char["hp"] = char["maxhp"]
            log += f"✨ เลเวลอัพ! Lv.{char['lv']}\n"
    else:
        char["hp"] = 1
        log += "\n💀 แพ้!"

    save_data(data)

    chunks = [log[i:i+1000] for i in range(0, len(log), 1000)]
    for chunk in chunks:
        embed = discord.Embed(description=f"```{chunk}```", color=0xff9900)
        await ctx.send(embed=embed)

# ===== HEAL =====
@bot.command()
async def heal(ctx, slot: int):
    if slot < 1 or slot > 3:
        return await ctx.send("❌ เลือก slot 1-3")

    user_id = str(ctx.author.id)
    data = load_data()
    char = data.get(user_id, {}).get("slots", [None,None,None])[slot-1]
    if not char:
        return await ctx.send("❌ ไม่มีตัวละคร")

    char["hp"] = char.get("maxhp",100)
    save_data(data)
    await ctx.send(f"💖 {char.get('name','ตัวละคร')} HP เต็ม!")

# ===== RUN =====
bot.run(TOKEN)