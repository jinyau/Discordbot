import os
import discord
import random
import re
import unidecode
import asyncio
import ffmpeg
import youtube_dl
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import aiomangadexapi
import asyncio
import json
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from pybooru import Danbooru
from pandas_datareader import data
from datetime import datetime, date, time, timedelta

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_ID2 = os.getenv('CHANNEL_ID2')
MANGADEX_USERNAME = os.getenv('MANGADEX_USERNAME')
MANGADEX_PASSWORD = os.getenv('MANGADEX_PASSWORD')
#GUILD = os.getenv('DISCORD_GUILD')

youtube_dl.utils.bug_reports_message = lambda: ''

intents = discord.Intents.default()

bot = commands.Bot(command_prefix = '!', intents=intents)

banned_words = ['boruto', 'ボルト', 'ぼると', 'b0ruto', 'b0rut0', 'borut0', 'ボuルzaトmaki', 'oturob', 'bouzarumatoki', '8oruto', '80ruto', '8orut0', '80rut0']

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
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

global music_queue 

music_queue = []

global song_name_queue 

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
        count = 1
        if 'entries' in data:
            for i in data['entries']:
                URL = i['formats'][0]['url']
                player = cls(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), data=data)
                music_queue.append(player)
                song_name_queue.append(i['title'])
            try:
                count = data['entries'][0]['n_entries']
            except:
                print('no count')
            return count
        else:
            URL = data['url'] 
            player = cls(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), data=data)
            music_queue.append(player)
            song_name_queue.append(player.title)
            return count

async def get_manga(mangadex_link):
    try:
        session = await aiomangadexapi.login(username=MANGADEX_USERNAME,password=MANGADEX_PASSWORD) # we login into mangadex
        updates = await aiomangadexapi.search(session,mangadex_link,True) # get the updates
    except Exception:
        pass
    else:
        await session.close()
        return updates
    await session.close()
    return None


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!\n')
    #manga_update.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    get_message = parse_message(message)

    if any(x in get_message.lower() for x in banned_words):
        channel = bot.get_channel(int(CHANNEL_ID))
        await message.delete() 
        response = 'Deleted from ' + message.author.name + ' in ' + message.channel.name + ':\n' + message.content
        await channel.send(content=response)

    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if after.author == bot.user:
        return
    
    edited_message = parse_message(after)

    if any(x in edited_message.lower() for x in banned_words):
        channel = bot.get_channel(int(CHANNEL_ID))
        await after.delete() 
        response = 'Deleted from ' + after.author.name + ' in ' + after.channel.name + ':\n' + after.content
        await channel.send(content=response)


@bot.event 
async def on_reaction_add(reaction, user):
    if reaction.message.author == user:
        await reaction.remove(user)


@bot.command(name='Aundre', aliases = ['AW', 'aundre', 'aw'])
async def fk_aundre(ctx):
    aundre_winter = 'I am Aundre Winter and my opinions are the worst in the world.'
    response = aundre_winter
    await ctx.send(response)


@bot.command(name='danbooru', aliases = ['anime'])
async def get_anime(ctx, *, tag: str=None):
    if tag is None:
        return await ctx.send('Enter a tag')

    client = Danbooru('danbooru')
    get_image = client.post_list(**{'limit':1, 'page':1, 'tags':tag, 'random': True})
    for image in get_image:
        response = image['large_file_url']

    await ctx.send(response)


@bot.command(name='play', aliases = ['p'])
async def play(ctx, *, url: str=None):
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
        count = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

        if not voice_client.is_playing():
            voice_client.play(music_queue[0], after=lambda e: play_next(ctx))
            if count>1:
                await ctx.send('**Queueing:** {}'.format(count) + ' songs')
            await ctx.send('**Now playing:** {}'.format(song_name_queue[0]))
            voice_client.is_playing()

        elif count>1:
            await ctx.send('**Queueing:** {}'.format(count) + ' songs')
        else:
            await ctx.send('**Queueing:** {}'.format(song_name_queue[-1]))
            
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


@bot.command(name='stock')
async def stock(ctx, ticker: str = None):
    if ticker is None:
        return await ctx.send('Enter a ticker.')

    tickers = [ticker.upper()]
    start_date = (datetime.today() - timedelta(weeks=52)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    panel_data = data.DataReader(tickers , 'yahoo', start_date, end_date)


    close_stocks = panel_data['Close']
    all_weekdays = pd.date_range(start=start_date, end=end_date, freq='B')
    close_stocks = close_stocks.reindex(all_weekdays)
    close_stocks = close_stocks.fillna(method='ffill')

    timeseries = close_stocks.loc[:, ticker.upper()]
    short_rolling = timeseries.rolling(window=30).mean()
    long_rolling = timeseries.rolling(window=90).mean()

    fig, ax = plt.subplots(figsize=(16,9))
    plt.grid(True)
    ax.plot(timeseries.index, timeseries, label=ticker.upper())
    ax.plot(short_rolling.index, short_rolling, label='30 days rolling')
    ax.plot(long_rolling.index, long_rolling, label='90 days rolling')

    ax.set_xlabel('Date')
    ax.set_ylabel('Adjusted closing price ($)')
    ax.legend()

    plt.savefig(fname='stock')
    await ctx.send(file=discord.File('stock.png'))
    os.remove('stock.png')


@bot.command(name='mangalist')
async def manga_list(ctx):
    manga_list = []
    conn = sqlite3.connect('manga.db')
    c = conn.cursor()
    c.execute("SELECT * FROM manga")
    rows = c.fetchall()
    for row in rows:
        revised_string = '[' + row[1] + ']' + '(' + row[0] + ')'
        manga_list.append(revised_string)
    conn.close()

    embed = discord.Embed(title='Manga List', description=('\n'.join(manga_list)))

    await ctx.send(embed=embed)


@bot.command(name='addmanga')
async def add_manga(ctx, url: str=None):
    if url is None:
        return await ctx.send('No link.')
    
    if 'https://mangadex.org/title/' not in url:
        return await ctx.send('Not a mangadex title link.')

    conn = sqlite3.connect('manga.db')
    c = conn.cursor()
    c.execute("SELECT * FROM manga where link=(?)",(url,))
    row = c.fetchone()

    if row is not None:
        return await ctx.send("Manga is already in the database.")
    
    manga = await get_manga(url)  
    
    if manga is not None:
        for stuff in manga:
            c.execute("INSERT INTO manga VALUES (?,?,?,?)",(url, stuff['title'], stuff['chapters'], stuff['image']))
            embed = discord.Embed(title='Manga Added', description=stuff['title']+' '+str(stuff['chapters']))
            embed.add_field(name='Link', value=stuff['latest'])
            embed.set_image(url=stuff['image'])
            await ctx.send(embed=embed)

            conn.commit()

    conn.close()


@tasks.loop(minutes=60)
async def manga_update():
    channel = bot.get_channel(int(CHANNEL_ID2))
    conn = sqlite3.connect('manga.db')
    c = conn.cursor()
    c.execute("SELECT * FROM manga")
    rows = c.fetchall()
    for row in rows:
        manga = await get_manga(row[0])
        if manga is not None:
            for stuff in manga:
                if stuff['chapters'] > row[2]:
                    embed = discord.Embed(title='New Chapter', description=row[1]+' '+str(stuff['chapters']))
                    embed.add_field(name='Link', value=stuff['latest'])
                    embed.set_image(url=stuff['image'])
                    await channel.send(embed=embed)
                    c.execute("UPDATE manga SET chapter = (?) WHERE link = (?) ",(stuff['chapters'],row[0]))
                    await channel.send(stuff['title'] + ' ' + str(stuff['chapters']))
                    conn.commit()
        else:
            print('mangadex api error')

    conn.close()


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
        asyncio.run_coroutine_threadsafe(ctx.send('**Now playing:** {}'.format(song_name_queue[0])), bot.loop)


bot.run(TOKEN)

