import aiomangadexapi
import asyncio
import asyncio
import discord
import ffmpeg
import json
import matplotlib.pyplot as plt
import os
import pandas as pd
import random
import re
import sqlite3
import time as t
import unidecode
import youtube_dl
from collections import defaultdict
from datetime import datetime, date, time, timedelta
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
from pandas_datareader import data
from pybooru import Danbooru
from youtube_dl import YoutubeDL


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

YTDL_OPTIONS_2 = {  
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
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

ytdl2 = youtube_dl.YoutubeDL(YTDL_OPTIONS_2)

global music_queue  

music_queue = defaultdict(list)  

global song_name_queue 

song_name_queue = defaultdict(list)

pending_tasks = dict()


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, voice, ctx, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        MUSIC_FLAG = False

        if not voice.is_playing():
            data1 = await loop.run_in_executor(None, lambda: ytdl2.extract_info(url, download=not stream))
            if 'entries' in data1:
                data1 = data1['entries'][0]
            URL = data1['url'] 
            player = cls(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), data=data1)
            music_queue[ctx.guild.id].append(player)
            song_name_queue[ctx.guild.id].append(player.title)
            MUSIC_FLAG = True
            voice.play(music_queue[ctx.guild.id][0], after=lambda e: play_next(ctx))
            await ctx.send('**Now playing:** {}'.format(song_name_queue[ctx.guild.id][0]))

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        count = 1

        if 'entries' in data:
            if(data['entries'][0]['n_entries'] is not None):
                count = data['entries'][0]['n_entries']
                if(count == 1 and MUSIC_FLAG):
                    return 0
            for i in data['entries']:
                example = i
                URL = i['formats'][0]['url']
                player = cls(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), data=data)
                music_queue[ctx.guild.id].append(player)
                song_name_queue[ctx.guild.id].append(i['title'])
                if MUSIC_FLAG:
                    MUSIC_FLAG = False
                    music_queue[ctx.guild.id].pop()
                    song_name_queue[ctx.guild.id].pop()
            if(count ==1):
                return -1
            return count
        else:
            if not MUSIC_FLAG:
                URL = data['url'] 
                player = cls(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), data=data)
                music_queue[ctx.guild.id].append(player)
                song_name_queue[ctx.guild.id].append(player.title)
                return -1
            return count


class Card:
    def __init__(self, suit=0, name=0, val=0):
        self.suit = suit
        self.name = name
        self.val = val

    def __str__(self):
        card_name = self.name  + self.suit
        return card_name


class Deck:
    def __init__(self):
        suits =['♠','♥','♣','♦']
        names = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
        self.cards = []
        for suit in suits:
            for name in names:
                if name in ('J','Q','K'):
                    val = 10
                    self.cards.append(Card(suit,name,val))
                elif name == 'A':
                    val = 11
                    self.cards.append(Card(suit,name,val))
                else:
                    val = int(name)
                    self.cards.append(Card(suit,name,val))
                
    def print_deck(self):
        for card in self.cards:
            print(card)

    def draw(self):
        random.shuffle(self.cards)
        return self.cards.pop()
        

class Hands:
    def __init__(self):
        self.hand = []

    def to_hand(self, card):
        self.hand.append(card)

    def __str__(self, number=0):
        hand_string = ''
        for card in self.hand:
            hand_string = hand_string + card.__str__() + ' '
            if number == 1:
                break
        return hand_string

    def value(self):
        total = 0
        for card in self.hand:
            total = total + card.val
        if total > 21:
            for x in range(len(self.hand)):
                if self.hand[x].val == 11:
                    self.hand[x].val = 1
                    total = total - 10
                    break
        return total


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


async def get_time(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = seconds % 3600 // 60
    return '{:02d} hours {:02d} minutes'.format(h, m)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!\n')
    #manga_update.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        cooldown = await get_time(error.retry_after)
        msg = 'You can claim again in ' + cooldown + '.'
        await ctx.send(msg)
    else:
        print(error)


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
    if reaction.message.author != bot.user:
        if reaction.message.author == user:
            await reaction.remove(user)


@bot.command(name='Aundre', aliases = ['AW', 'aundre', 'aw'])
async def fk_aundre(ctx):
    aundre_winter = 'I am Aundre Winter and my opinions are the worst in the world.'
    response = aundre_winter
    await ctx.send(response)


@bot.command(name='jordan', aliases = ['j', 'gay', 'blacked'])
async def jordan(ctx):
    response = 'https://media.discordapp.net/attachments/804193490241978420/811127242369138720/gayslobberkiss1.gif?width=400&height=223'
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
        count = await YTDLSource.from_url(voice_client, ctx, url, loop=bot.loop, stream=True)

        if not voice_client.is_playing():
            voice_client.play(music_queue[ctx.guild.id][0], after=lambda e: play_next(ctx))
            if count>1:
                await ctx.send('**Queueing:** {}'.format(count) + ' songs')
            await ctx.send('**Now playing:** {}'.format(song_name_queue[ctx.guild.id][0]))

        if count>1:
            await ctx.send('**Queueing:** {}'.format(count) + ' songs')
        elif count == -1:
            await ctx.send('**Queueing:** {}'.format(song_name_queue[ctx.guild.id][-1]))
            
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
    queue_list = []
    embed_list = []
    n = 15
    count = 1
    nums = map(str, range(1, len(song_name_queue[ctx.guild.id])+1))
    # output = "\n".join((x+'. '+y) for x,y in zip(nums, song_name_queue))
    for x,y in zip(nums, song_name_queue[ctx.guild.id]):
        output = x+'. '+y
        queue_list.append(output)
    for i in range(0, len(queue_list), n):
        embed = discord.Embed(title='Music Queue '  + str(count) , description=('\n'.join(queue_list[i:i + n])))
        embed_list.append(embed)
        count = count + 1
    if not embed_list:
        return await ctx.send('Queue is currently empty.')
    elif len(embed_list) == 1:
        return await ctx.send(embed=embed_list[0])
    else:
        message = await ctx.send(embed=embed_list[0])
        await message.add_reaction('◀')
        await message.add_reaction('▶')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id

        i = 0
        reaction = None

        while True:
            if str(reaction) == '◀':
                if i > 0:
                    i -= 1
                    await message.edit(embed = embed_list[i])
                elif i == 0:
                    i = len(embed_list) - 1
                    await message.edit(embed = embed_list[-1])
            elif str(reaction) == '▶':
                if i < len(embed_list) - 1 :
                    i += 1
                    await message.edit(embed = embed_list[i])
                elif i == len(embed_list) - 1:
                    i = 0
                    await message.edit(embed = embed_list[0])
            
            try:
                # if ctx.author in pending_tasks:
                #     pending_tasks[ctx.author].close()
                # pending_tasks[ctx.author] = bot.wait_for('reaction_add', timeout=60.0, check=check)
                # reaction, user =  await pending_tasks[ctx.author]
                reaction, user = await bot.wait_for('reaction_add', timeout = 30.0, check = check)
                await message.remove_reaction(reaction, user)

            except:
                break
        
        await message.clear_reactions()


@bot.command(name='move')
async def move(ctx, number:int=None):
    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send('`You need to be in a voice channel to use this command!`')

    if number is None:
        return await ctx.send('No position enter.')

    if number>len(song_name_queue[ctx.guild.id]):
        return await ctx.send('Out of bounds.')

    song_name = song_name_queue[ctx.guild.id][number-1]
    song_name_queue[ctx.guild.id].insert(1, song_name_queue[ctx.guild.id].pop(number-1))
    music_queue[ctx.guild.id].insert(1, music_queue[ctx.guild.id].pop(number-1))
    response = song_name + ' was moved to the front of queue.'
    return await ctx.send(response)


@bot.command(name='clear')
async def clear (ctx):
    global music_queue
    global song_name_queue
    voice_state = ctx.author.voice
    if voice_state is None:
         return await ctx.send('`You need to be in a voice channel to use this command!`')

    music_queue[ctx.guild.id] = []
    song_name_queue[ctx.guild.id] = []
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
        music_queue[ctx.guild.id] = []
        song_name_queue[ctx.guild.id] = []
        voice_client.stop()

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
    embed_list = []
    n = 15
    count = 1
    conn = sqlite3.connect('manga.db')
    c = conn.cursor()
    c.execute("SELECT * FROM manga")
    rows = c.fetchall()
    for row in rows:
        revised_string = '[' + row[1] + ']' + '(' + row[0] + ')'
        manga_list.append(revised_string)
    conn.close()
    for i in range(0, len(manga_list), n):
        embed = discord.Embed(title='Manga List '  + str(count) , description=('\n'.join(manga_list[i:i + n])))
        embed_list.append(embed)
        count = count + 1
        #embed2 = discord.Embed(title='Manga List Cont', description=('\n'.join(manga_list[13:])))
    message = await ctx.send(embed=embed_list[0])
    await message.add_reaction('◀')
    await message.add_reaction('▶')

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id

    i = 0
    reaction = None

    while True:
        if str(reaction) == '◀':
            if i > 0:
                i -= 1
                await message.edit(embed = embed_list[i])
            elif i == 0:
                i = len(embed_list) - 1
                await message.edit(embed = embed_list[-1])
        elif str(reaction) == '▶':
            if i < len(embed_list) - 1 :
                i += 1
                await message.edit(embed = embed_list[i])
            elif i == len(embed_list) - 1:
                i = 0
                await message.edit(embed = embed_list[0])
        
        try:
            # if ctx.author in pending_tasks:
            #     pending_tasks[ctx.author].close()
            # pending_tasks[ctx.author] = bot.wait_for('reaction_add', timeout=60.0, check=check)
            # reaction, user =  await pending_tasks[ctx.author]
            reaction, user =  await bot.wait_for('reaction_add', timeout=60.0, check=check)
            await message.remove_reaction(reaction, user)

        except:
            break
    
    await message.clear_reactions()


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

    
@bot.command(name='credit', aliases = ['credits'])
async def credit(ctx):
    credit = await account(ctx)

    await ctx.send('You have ' + str(credit) + ' credits.')


@bot.command(name='daily')
@commands.cooldown(1,79200,commands.BucketType.member)
async def daily(ctx):

    credit = await account(ctx, 200)

    await ctx.send('You added 200 credits to your account. Your total credits is ' + str(credit) + '.')

@bot.command(name='leaderboard', aliases = ['lb'])
async def leaderboard(ctx):
    with open('credits.json', 'r') as f:
        accounts = json.load(f)

    embed = discord.Embed(title = ctx.guild.name + ' Leaderboard')
    embed.set_thumbnail(url = ctx.guild.icon_url)
    count = 1
    number = 0
    for w in sorted(accounts[str(ctx.guild.id)], key=accounts[str(ctx.guild.id)].get, reverse=True):
        user = await bot.fetch_user(w)
        username = user.display_name
        if number == 0:
            embed.add_field(name = 'Rank', value = str(count))
            embed.add_field(name = 'Name', value = username)
            embed.add_field(name = 'Amount', value = accounts[str(ctx.guild.id)][w])
            number = 1
        else:
            embed.add_field(name = '\u200b', value = str(count))
            embed.add_field(name = '\u200b', value = username)
            embed.add_field(name = '\u200b', value = accounts[str(ctx.guild.id)][w])
        count = count + 1
        if(count>15):
            break
    await ctx.send(embed=embed)

async def account(ctx, credit = 0):
    with open('credits.json', 'r') as f:
        accounts = json.load(f)

    count = 0

    if str(ctx.guild.id) not in accounts:
        accounts[str(ctx.guild.id)] = {}
    if str(ctx.author.id) not in accounts[str(ctx.guild.id)]:
        accounts[str(ctx.guild.id)][str(ctx.author.id)] = 0
    accounts[str(ctx.guild.id)][str(ctx.author.id)] = accounts[str(ctx.guild.id)][str(ctx.author.id)] + credit
    count = accounts[str(ctx.guild.id)][str(ctx.author.id)]
    with open('credits.json', 'w') as f:
        json.dump(accounts, f)

    return count


async def withdraw(ctx, amount):
    await account(ctx)

    with open('credits.json', 'r') as f:
        accounts = json.load(f)
    
    if amount > accounts[str(ctx.guild.id)][str(ctx.author.id)]:
        amount = accounts[str(ctx.guild.id)][str(ctx.author.id)]
        accounts[str(ctx.guild.id)][str(ctx.author.id)] = 0
    else:
        accounts[str(ctx.guild.id)][str(ctx.author.id)] = accounts[str(ctx.guild.id)][str(ctx.author.id)] - amount
    
    with open('credits.json', 'w') as f:
        json.dump(accounts, f)
    
    return amount


@bot.command(name='blackjack', aliases = ['bj'])
async def blackjack(ctx, bet = 0):
    if bet!= 0:
        amount = await withdraw(ctx, abs(bet))
        await ctx.send('You bet ' + str(amount) + ' credits.')
    

    WIN_FLAG = None
    GAME = True
    mention = ctx.author.mention
    deck = Deck()
    player_hand = Hands()
    dealer_hand = Hands()
    player_hand.to_hand(deck.draw())
    dealer_hand.to_hand(deck.draw())
    player_hand.to_hand(deck.draw())
    dealer_hand.to_hand(deck.draw())

    embed = discord.Embed(title = 'Blackjack')
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name='Player Hand', value = player_hand, inline = True)
    embed.add_field(name='\u200b', value = '\u200b', inline = True)
    embed.add_field(name='Dealer Hand', value = dealer_hand.__str__(1) + ' ?' , inline = True)
    embed.add_field(name='Your Value', value = player_hand.value(), inline = True)
    embed.add_field(name='\u200b', value = '\u200b', inline = True)
    embed.add_field(name='Dealer Value', value = '?', inline = True)

    message = await ctx.send(embed=embed)
    await message.add_reaction('<:HIT:827771632822911046>')
    await message.add_reaction('<:STAY:827771644968960020>')

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id


    if(player_hand.value() == dealer_hand.value() == 21):
        await asyncio.sleep(1)
        embed.title =  'Tie!'
        await message.edit(embed = embed)
        embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
        embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
        await message.clear_reactions()
    elif(player_hand.value() == 21):
        await asyncio.sleep(1)
        embed.title =  'You Win! Blackjack!'
        embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
        embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
        await message.edit(embed = embed)
        await message.clear_reactions()
        WIN_FLAG = True

    reaction = None

    while player_hand.value() < 21:
        if str(reaction) == '<:HIT:827771632822911046>':
            player_hand.to_hand(deck.draw())
            embed.set_field_at(0,name='Player Hand', value = player_hand)
            embed.set_field_at(3,name='Your Value', value = player_hand.value())
            await message.edit(embed=embed)
        elif str(reaction) == '<:STAY:827771644968960020>':
            embed.title = '''Dealer's turn.'''
            embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
            embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
            await message.edit(embed=embed)
            if(dealer_hand.value()>player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Dealer Wins. You Lose!'
                    await message.edit(embed=embed)
                    WIN_FLAG = False
                    GAME = False
                    break
            if(dealer_hand.value()==player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Draw.'
                    await message.edit(embed=embed)
                    GAME = False
                    break
            if(dealer_hand.value()<player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Player Wins!'
                    await message.edit(embed=embed)
                    WIN_FLAG = True                    
                    GAME = False  
                    break
            while(dealer_hand.value()<17):
                await asyncio.sleep(1)
                dealer_hand.to_hand(deck.draw())
                embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
                embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
                await message.edit(embed=embed)
                if(dealer_hand.value()==player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Draw.'
                    await message.edit(embed=embed)
                    GAME = False
                    break
                if(dealer_hand.value()>21):
                    embed.title = 'Dealer bust. You Win!'
                    await message.edit(embed=embed)
                    WIN_FLAG = True
                    GAME = False
                    break
                if(dealer_hand.value()>player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Dealer Wins. You Lose!'
                    await message.edit(embed=embed)
                    WIN_FLAG = False
                    GAME = False
                    break
                if(dealer_hand.value()<player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Player Wins!'
                    await message.edit(embed=embed)
                    WIN_FLAG = True
                    GAME = False
                    break
        if player_hand.value() > 21:
            embed.title = 'You Lose! Bust!'
            await message.edit(embed=embed)
            WIN_FLAG = False
            GAME = False
            break
        if player_hand.value() == 21:
            embed.title = '''Dealer's turn.'''
            embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
            embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
            await message.edit(embed=embed)
            if(dealer_hand.value()<player_hand.value() and dealer_hand.value()>=17):
                embed.title = 'You win!'
                await message.edit(embed=embed)
                WIN_FLAG = True
                GAME = False
                break
            if(dealer_hand.value()==player_hand.value()):
                embed.title = 'Draw.'
                await message.edit(embed=embed)
                GAME = False
                break
            while(dealer_hand.value()<17):
                await asyncio.sleep(1)
                dealer_hand.to_hand(deck.draw())
                embed.set_field_at(2,name='Dealer Hand', value = dealer_hand)
                embed.set_field_at(5,name='Dealer Value', value = dealer_hand.value())
                await message.edit(embed=embed)
                if(dealer_hand.value()==player_hand.value()):
                    embed.title = 'Draw.'
                    await message.edit(embed=embed)
                    GAME = False
                    break
                if(dealer_hand.value()>21):
                    embed.title = 'Dealer bust. You Win!'
                    await message.edit(embed=embed)
                    WIN_FLAG = True
                    GAME = False    
                    break
                if(dealer_hand.value()<player_hand.value() and dealer_hand.value()>=17):
                    embed.title = 'Player Wins!'
                    await message.edit(embed=embed)
                    WIN_FLAG = True
                    GAME = False
                    break
        if not GAME:
            break

        try:
            reaction, user =  await bot.wait_for('reaction_add', timeout=30.0, check=check)
            await message.remove_reaction(reaction, user)

        except:
            break

    await message.clear_reactions()
    if(bet!=0):
        mention = ctx.author.mention
        if(WIN_FLAG):
            winnings = 2 * amount
            account_balance = await account(ctx,winnings)
            await ctx.send(mention + ' You won ' + str(winnings) +  ' credits. Your total credits is ' + str(account_balance) + '.')
        elif WIN_FLAG is False:
            account_balance = await account(ctx)
            await ctx.send(mention + ' You lost ' + str(amount) +' credits. Your total credits is ' + str(account_balance) + '.')
        else:
            winnings = amount
            account_balance = await account(ctx,winnings)
            await ctx.send(mention + ' Draw. Your total credits is ' + str(account_balance) + '.')


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
                    await channel.send("<@&820037605457920020> " + stuff['title'] + ' ' + str(stuff['chapters']))
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

    if len(music_queue[ctx.guild.id]) > 1:    
        del music_queue[ctx.guild.id][0]
        del song_name_queue[ctx.guild.id][0]
        voice_client.play(music_queue[ctx.guild.id][0], after=lambda e: play_next(ctx))
        voice_client.is_playing()
        asyncio.run_coroutine_threadsafe(ctx.send('**Now playing:** {}'.format(song_name_queue[ctx.guild.id][0])), bot.loop)
    else:
        try:
            del music_queue[ctx.guild.id][0]
            del song_name_queue[ctx.guild.id][0]
        except:
            pass
        t.sleep(5)
        if not voice_client.is_playing() and voice_client.is_connected():
            asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
            asyncio.run_coroutine_threadsafe(ctx.send('Disconnecting from voice due to inactivity.'), bot.loop)



bot.run(TOKEN)
