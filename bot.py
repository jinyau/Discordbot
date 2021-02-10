import os
import discord
import random
import re
import unidecode
import asyncio
import ffmpeg
import youtube_dl
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
#GUILD = os.getenv('DISCORD_GUILD')

youtube_dl.utils.bug_reports_message = lambda: ''

intents = discord.Intents.default()

bot = commands.Bot(command_prefix = '!', intents=intents)

banned_words = ['boruto', 'ボルト', 'ぼると', 'b0ruto', 'b0rut0', 'borut0', 'ボuルzaトmaki', 'oturob', 'bouzarumatoki', '8oruto', '80ruto', '8orut0', '80rut0']

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

music_queue = []

song_name_queue = []

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!\n')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    get_message = parse_message(message)

    if any(x in get_message.lower() for x in banned_words):
        channel = bot.get_channel(CHANNEL_ID)
        await message.delete() 
        response = 'Deleted from ' + message.author.name + ' in ' + message.channel.name + ':\n' + message.content
        await channel.send(content=response)

    await bot.process_commands(message)


@bot.event 
async def on_reaction_add(reaction, user):
    if reaction.message.author == user:
        await reaction.remove(user)


@bot.command(name='Aundre', aliases = ['AW', 'aundre', 'aw'])
async def fk_aundre(ctx):
    aundre_winter = 'I am Aundre Winter and my opinions are the worst in the world.'
    response = aundre_winter
    await ctx.send(response)


@bot.command(name='play', aliases = ['p'])
async def play(ctx, url):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    if url is None:
        return await ctx.send('No url or search query.')

    voice_channel = ctx.author.voice.channel

    
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()

    #voice = get(bot.voice_clients, guild=ctx.guild)

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        song_name_queue.append(player.title)
        music_queue.append(player)
        if not voice_client.is_playing():
            voice_client.play(music_queue[0], after=lambda e: play_next(ctx))
            await ctx.send('**Now playing:** {}'.format(player.title))
            voice_client.is_playing()

        else:
            await ctx.send('**Queueing:** {}'.format(player.title))
            
        #with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
        #    info = ydl.extract_info(url, download=False)
        #    URL = info['formats'][0]['url']
        #voice_client.play(player, after=lambda e: print('Player error: %s' %e) if e else None )
        #voice_client.play(discord.FFmpegPCMAudio(URL))

    
        #await ctx.send('**Now playing:** {}'.format(player.title))

@bot.command(name='leave')
async def leave(ctx):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='pause')
async def pause(ctx):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send('Audio is already paused.')


@bot.command(name='resume')
async def resume(ctx):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_paused():
        voice_client.resume()
    else:
        await ctx.send('Audio is not paused.')


@bot.command(name='skip')
async def skip(ctx):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.stop()
        #del song_name_queue[0]
        #del music_queue[0]
        #voice_client.play(music_queue[0], after=lambda e: play_next(ctx))
        #play_next(ctx)
    else:
        await ctx.send('Nothing is queued.')


@bot.command(name='queue')
async def queue(ctx):
    await ctx.send('Queue:\n' + '\n'.join(song_name_queue))

@bot.command(name='clear')
async def clear (ctx):
    global music_queue
    global song_name_queue
    voice_state = ctx.author.voice
    if voice_state is None:
         return await ctx.send('`You need to be in a voice channel to use this command!`')

    music_queue = []
    song_name_queue = []
    await ctx.send('Queue is cleared.')


@bot.command(name='stop')
async def stop(ctx):
    global music_queue
    global song_name_queue
    voice_state = ctx.author.voice
    if voice_state is None:
         return await ctx.send('`You need to be in a voice channel to use this command!`')
    
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.stop()
        music_queue = []
        song_name_queue = []
        await ctx.send('Bot is stopped and queue is cleared.')

    else:
        await ctx.send('No music is playing.')

     

def parse_message(message):
    #parsed_message = message.content.replace('-','').replace(' ', '').replace(':','').replace(';','').replace('/','').replace('~','').replace('・','').replace('.','').replace(',','').replace('♡','')
    stripped_accent = unidecode.unidecode(message.content)
    parsed_message = re.sub('[^A-Za-z0-9ぁ-ゔァ-ヴー]+', '', stripped_accent)
    return parsed_message
    
def play_next(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if len(music_queue) > 1:
        del music_queue[0]
        del song_name_queue[0]
        voice_client.play(music_queue[0], after=lambda e: play_next(ctx))
        voice_client.is_playing()

bot.run(TOKEN)

