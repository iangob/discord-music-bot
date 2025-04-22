import discord
from discord.ext import commands
import json
import os

# ---- 설정 ----
TOKEN = TOKEN
ROLE_NAME = "유동"      # 닉네임을 "ㅇㅇ"으로 바꿀 대상 역할
RESET_ROLE_NAME = "유저"      # 이 역할이 추가되면 원래 닉네임으로 복구
NEW_NICK = "ㅇㅇ"
NICKS_FILE = "original_nicks.json"
# ----------------

# JSON 읽기/쓰기 도우미
def load_nicks():
    if os.path.exists(NICKS_FILE):
        with open(NICKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_nicks(d):
    with open(NICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # 필요하다면

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    guild = after.guild
    all_nicks = load_nicks()
    role_target = discord.utils.get(guild.roles, name=ROLE_NAME)
    role_reset  = discord.utils.get(guild.roles, name=RESET_ROLE_NAME)

    # 1) 특정 역할이 새로 부여됐을 때 → 원래 닉 저장 후 "ㅇㅇ"으로 변경
    if role_target and role_target not in before.roles and role_target in after.roles:
        # before.nick 이 None 이면 사용자 이름(username) 사용
        orig = before.nick or before.name
        user_id = str(after.id)
        # 이미 저장된 적 없다면 저장
        if user_id not in all_nicks:
            all_nicks[user_id] = orig
            save_nicks(all_nicks)
        try:
            await after.edit(nick=NEW_NICK)
            print(f"🔖 Saved & changed {after} → {NEW_NICK}")
        except discord.Forbidden:
            print(f"🚫 권한 부족: {after} 닉네임 변경 실패")

    # 2) “유저” 역할이 새로 부여됐을 때 → JSON 에서 원래 닉 찾아 복구
    elif role_reset and role_reset not in before.roles and role_reset in after.roles:
        user_id = str(after.id)
        orig = all_nicks.get(user_id)
        if orig:
            try:
                await after.edit(nick=orig)
                print(f"↩️ Restored {after} → {orig}")
                # 복구 후 JSON 에서 삭제
                del all_nicks[user_id]
                save_nicks(all_nicks)
            except discord.Forbidden:
                print(f"🚫 권한 부족: {after} 닉네임 복구 실패")

@bot.command(name="rename_role")
@commands.has_permissions(manage_nicknames=True)
async def rename_role(ctx):
    """수동으로 ROLE_NAME 역할자 전부를 NEW_NICK 으로 변경하고 JSON에 원래 닉 저장"""
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if not role:
        return await ctx.send(f"❌ 역할 `{ROLE_NAME}`을 찾을 수 없습니다.")

    all_nicks = load_nicks()
    changed = 0
    for member in guild.members:
        if role in member.roles:
            uid = str(member.id)
            orig = member.nick or member.name
            if uid not in all_nicks:
                all_nicks[uid] = orig
            try:
                await member.edit(nick=NEW_NICK)
                changed += 1
            except discord.Forbidden:
                pass

    save_nicks(all_nicks)
    await ctx.send(f"✅ `{ROLE_NAME}` 역할을 가진 {changed}명 닉네임을 `{NEW_NICK}`으로 변경하고 저장했습니다.")

bot.run(TOKEN)
