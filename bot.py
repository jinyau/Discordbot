import os
import discord
import random
import re
import unidecode
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()

bot = commands.Bot(command_prefix = '!', intents=intents)

banned_words = ['boruto', 'ボルト', 'ぼると', 'b0ruto', 'b0rut0', 'borut0', 'ボuルzaトmaki', 'oturob', 'bouzarumatoki', '8oruto', '80ruto', '8orut0', '80rut0']


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!\n')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    get_message = parse_message(message)

    if any(x in get_message.lower() for x in banned_words):
        channel = bot.get_channel(804193490241978420)
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


def parse_message(message):
    #parsed_message = message.content.replace('-','').replace(' ', '').replace(':','').replace(';','').replace('/','').replace('~','').replace('・','').replace('.','').replace(',','').replace('♡','')
    stripped_accent = unidecode.unidecode(message.content)
    parsed_message = re.sub('[^A-Za-z0-9ぁ-ゔァ-ヴー]+', '', stripped_accent)
    return parsed_message
    

bot.run(TOKEN)

