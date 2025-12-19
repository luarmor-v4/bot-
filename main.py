import discord
from discord.ext import commands
from discord import app_commands
import random
import string
import time
import asyncio

from config import *
from database import Database
from workink import WorkinkAPI

# ═══════════════════════════════════════════════════════════
# BOT SETUP
# ═══════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = Database()
workink = WorkinkAPI()

# ═══════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════
def generate_key() -> str:
    """Generate random key dengan format PREFIX-XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    segments = [''.join(random.choices(chars, k=4)) for _ in range(4)]
    return f"{KEY_PREFIX}-{'-'.join(segments)}"

def is_admin(user_id: int) -> bool:
    """Cek apakah user adalah admin"""
    return user_id in ADMIN_IDS

def format_time(seconds: float) -> str:
    """Format detik ke jam:menit"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

# ═══════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"═══════════════════════════════════════")
    print(f"🤖 Bot: {bot.user.name}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"👑 Admins: {len(ADMIN_IDS)}")
    print(f"═══════════════════════════════════════")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!getkey | !help"
        )
    )
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ═══════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════

# ═══ GET KEY ═══
@bot.command(name="getkey")
async def getkey(ctx):
    """Dapatkan key - Admin langsung, Member lewat iklan"""
    user_id = ctx.author.id
    username = ctx.author.display_name
    
    # ══════════════════════════════════
    # ADMIN - LANGSUNG GENERATE KEY
    # ══════════════════════════════════
    if is_admin(user_id):
        key = generate_key()
        db.add_key(key, user_id, is_admin=True)
        
        embed = discord.Embed(
            title="👑 ADMIN KEY GENERATOR",
            description="Key berhasil dibuat tanpa verifikasi!",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="🔑 Key Kamu",
            value=f"```{key}```",
            inline=False
        )
        embed.add_field(name="⏰ Durasi", value="24 Jam", inline=True)
        embed.add_field(name="👤 Status", value="Admin", inline=True)
        embed.set_footer(text=f"Generated for {username}")
        
        # Kirim ke DM
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(f"✅ {ctx.author.mention} Key telah dikirim ke DM!")
        except discord.Forbidden:
            await ctx.send(embed=embed)
        
        return
    
    # ══════════════════════════════════
    # MEMBER - HARUS LEWAT IKLAN
    # ══════════════════════════════════
    
    # Cek apakah sudah ada pending
    pending = db.get_pending(user_id)
    if pending and time.time() < pending["expires_at"]:
        remaining = int(pending["expires_at"] - time.time())
        await ctx.send(
            f"⏳ {ctx.author.mention} Kamu sudah request key!\n"
            f"Selesaikan verifikasi atau tunggu {remaining} detik."
        )
        return
    
    # Generate link Work.ink
    link_data = workink.generate_user_link(user_id)
    db.add_pending(user_id, link_data["token"], link_data["link"])
    
    embed = discord.Embed(
        title="🔐 GET YOUR KEY",
        description="Selesaikan langkah berikut untuk mendapatkan key:",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="📋 Langkah-langkah:",
        value=(
            "```\n"
            "1️⃣ Klik link dibawah\n"
            "2️⃣ Selesaikan verifikasi\n"
            "3️⃣ Kembali & ketik !verify\n"
            "```"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔗 Link Verifikasi",
        value=f"**[KLIK DISINI]({link_data['link']})**",
        inline=False
    )
    
    embed.add_field(
        name="⏰ Berlaku",
        value="10 Menit",
        inline=True
    )
    
    embed.add_field(
        name="🎫 Token",
        value=f"`{link_data['token'][:8]}...`",
        inline=True
    )
    
    embed.set_footer(text="⚠️ Jangan share link ini ke orang lain!")
    
    # Kirim ke DM
    try:
        await ctx.author.send(embed=embed)
        await ctx.send(f"📩 {ctx.author.mention} Cek DM untuk link verifikasi!")
    except discord.Forbidden:
        await ctx.send(
            f"{ctx.author.mention} DM kamu tertutup! Buka DM lalu coba lagi.",
            delete_after=10
        )

# ═══ VERIFY ═══
@bot.command(name="verify")
async def verify(ctx):
    """Verifikasi setelah menyelesaikan iklan"""
    user_id = ctx.author.id
    
    # Admin tidak perlu verify
    if is_admin(user_id):
        await ctx.send(f"👑 {ctx.author.mention} Kamu admin! Gunakan `!getkey` langsung.")
        return
    
    # Cek pending
    pending = db.get_pending(user_id)
    
    if not pending:
        await ctx.send(f"❌ {ctx.author.mention} Kamu belum request key! Gunakan `!getkey` dulu.")
        return
    
    # Cek expired
    if time.time() > pending["expires_at"]:
        db.remove_pending(user_id)
        await ctx.send(f"⏰ {ctx.author.mention} Link sudah expired! Gunakan `!getkey` lagi.")
        return
    
    # Verifikasi dengan Work.ink API (opsional)
    # is_completed = workink.verify_completion(user_id, pending["token"])
    
    # Untuk sekarang, langsung approve (bisa ditambah validasi)
    is_completed = True
    
    if is_completed:
        # Generate key
        key = generate_key()
        db.add_key(key, user_id, is_admin=False)
        db.remove_pending(user_id)
        
        embed = discord.Embed(
            title="✅ VERIFIKASI BERHASIL!",
            description="Terima kasih sudah menyelesaikan verifikasi!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🔑 Key Kamu",
            value=f"```{key}```",
            inline=False
        )
        
        embed.add_field(name="⏰ Durasi", value="24 Jam", inline=True)
        embed.add_field(name="📋 Copy", value="Tap key diatas", inline=True)
        
        embed.set_footer(text="Simpan key ini dengan aman!")
        
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(f"✅ {ctx.author.mention} Key dikirim ke DM!")
        except discord.Forbidden:
            await ctx.send(embed=embed)
    else:
        await ctx.send(
            f"❌ {ctx.author.mention} Verifikasi gagal! "
            f"Pastikan sudah menyelesaikan semua langkah di link."
        )

# ═══ CEK KEY ═══
@bot.command(name="cekkey")
async def cekkey(ctx, key: str = None):
    """Cek validitas key"""
    if not key:
        await ctx.send("⚠️ Format: `!cekkey <key>`")
        return
    
    result = db.validate_key(key)
    
    if result["valid"]:
        embed = discord.Embed(
            title="✅ KEY VALID",
            color=discord.Color.green()
        )
        embed.add_field(name="🔑 Key", value=f"`{key}`", inline=False)
        embed.add_field(name="⏰ Sisa Waktu", value=result["remaining"], inline=True)
    else:
        embed = discord.Embed(
            title="❌ KEY TIDAK VALID",
            color=discord.Color.red()
        )
        embed.add_field(name="🔑 Key", value=f"`{key}`", inline=False)
        embed.add_field(name="❓ Alasan", value=result["reason"], inline=True)
    
    await ctx.send(embed=embed)

# ═══ MY ID ═══
@bot.command(name="myid")
async def myid(ctx):
    """Lihat Discord ID kamu"""
    embed = discord.Embed(
        title="🆔 Discord ID",
        color=discord.Color.blurple()
    )
    embed.add_field(name="User", value=ctx.author.mention, inline=True)
    embed.add_field(name="ID", value=f"`{ctx.author.id}`", inline=True)
    embed.add_field(name="Status", value="👑 Admin" if is_admin(ctx.author.id) else "👤 Member", inline=True)
    
    await ctx.send(embed=embed)

# ═══ ADMIN COMMANDS ═══
@bot.command(name="genkey")
async def genkey(ctx, amount: int = 1):
    """[ADMIN] Generate multiple keys"""
    if not is_admin(ctx.author.id):
        await ctx.send("❌ Hanya admin!")
        return
    
    if amount > 10:
        amount = 10
    
    keys = []
    for _ in range(amount):
        key = generate_key()
        db.add_key(key, ctx.author.id, is_admin=True)
        keys.append(key)
    
    keys_text = "\n".join([f"• `{k}`" for k in keys])
    
    embed = discord.Embed(
        title=f"👑 GENERATED {amount} KEYS",
        description=keys_text,
        color=discord.Color.gold()
    )
    
    try:
        await ctx.author.send(embed=embed)
        await ctx.send(f"✅ {amount} keys dikirim ke DM!")
    except:
        await ctx.send(embed=embed)

@bot.command(name="stats")
async def stats(ctx):
    """[ADMIN] Lihat statistik"""
    if not is_admin(ctx.author.id):
        await ctx.send("❌ Hanya admin!")
        return
    
    stats = db.get_stats()
    workink_stats = workink.get_stats()
    
    embed = discord.Embed(
        title="📊 STATISTIK BOT",
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(name="🔑 Total Keys", value=stats["total_keys"], inline=True)
    embed.add_field(name="✅ Active Keys", value=stats["active_keys"], inline=True)
    embed.add_field(name="❌ Expired Keys", value=stats["expired_keys"], inline=True)
    embed.add_field(name="⏳ Pending Users", value=stats["pending_users"], inline=True)
    embed.add_field(name="👀 Link Views", value=workink_stats.get("views", "N/A"), inline=True)
    embed.add_field(name="✅ Completions", value=workink_stats.get("completions", "N/A"), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="addadmin")
async def addadmin(ctx, user: discord.Member):
    """[OWNER] Tambah admin baru"""
    if ctx.author.id != ADMIN_IDS[0]:  # Hanya owner pertama
        await ctx.send("❌ Hanya owner!")
        return
    
    if user.id in ADMIN_IDS:
        await ctx.send(f"⚠️ {user.mention} sudah admin!")
        return
    
    ADMIN_IDS.append(user.id)
    await ctx.send(f"✅ {user.mention} ditambahkan sebagai admin!")

# ═══ HELP ═══
@bot.command(name="help")
async def help_cmd(ctx):
    """Tampilkan bantuan"""
    embed = discord.Embed(
        title="📖 BANTUAN",
        description="Daftar perintah yang tersedia:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="👤 User Commands",
        value=(
            "`!getkey` - Dapatkan key\n"
            "`!verify` - Verifikasi setelah iklan\n"
            "`!cekkey <key>` - Cek validitas key\n"
            "`!myid` - Lihat Discord ID"
        ),
        inline=False
    )
    
    if is_admin(ctx.author.id):
        embed.add_field(
            name="👑 Admin Commands",
            value=(
                "`!genkey <jumlah>` - Generate multiple keys\n"
                "`!stats` - Lihat statistik\n"
                "`!addadmin @user` - Tambah admin"
            ),
            inline=False
        )
    
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════════
# RUN BOT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    bot.run(DISCORD_TOKEN)
