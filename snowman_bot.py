from random import choice
import os
import discord
from discord.ext import tasks, commands
import psycopg2
import urllib
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE_URL = os.getenv('DATABASE_URL')


class db_talker():
    '''
    Usage:
    with db_talker() as cur:
        cur.execute(...)
    Automatically closes at the end of with block.
    '''

    def __enter__(self):
        self.conn = self.connect_to_elephantsql()
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, *args):
        self.conn.commit()
        self.conn.close()

    def connect_to_elephantsql(self):
        # Connect to ElephantSQL database
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(database=url.path[1:],
        user = url.username,
        password = url.password,
        host = url.hostname,
        port = url.port
        )

        return conn


# client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    with db_talker() as cur:
        cur.execute('select time from turn')
        t1 = datetime.fromtimestamp(cur.fetchone()[0])
        t2 = datetime.now()
        t3 = t1 + timedelta(hours=48)
        time_remaining = t3 - t2

        cur.execute('select name from players where active=true')
        active_player = cur.fetchone()[0]

    guild = discord.utils.get(bot.guilds, name=GUILD)
    channels = bot.get_all_channels()
    channel_list = list()
    for channel in channels:
        channel_list.append(channel)
    general = bot.get_channel(843641902371700739)

    if time_remaining > timedelta(hours=24):
        pass
    elif time_remaining < timedelta(hours=24) and time_remaining > timedelta(hours=23):
        await general.send(f'{active_player} has 24 hours left in their turn')
    elif time_remaining < timedelta(hours=12) and time_remaining > timedelta(hours=11):
        await general.send(f'{active_player} has 12 hours left in their turn')

    # guild = discord.utils.get(bot.guilds, name=GUILD)
    # channels = bot.get_all_channels()
    # channel_list = list()
    # for channel in channels:
    #     channel_list.append(channel)
    # general = bot.get_channel(843641902371700739)
    # print(
    #     f'{bot.user} is connected to the following guild:\n'
    #     f'{guild.name}(id: {guild.id})'
    # )
    # #
    # members = '\n - '.join([member.name for member in guild.members])
    # print(f'Guild Members:\n - {members}')
    # print(f'Channels: {channel_list}')

    # await general.send('Disconnecting, goodbye!!')
    await bot.close()

# @tasks.loop(seconds=3)
# async def myLoop():
#     general = bot.get_channel(843641902371700739)
#     await general.send('Is it working?')
# async def my_task(ctx):
#     while True:
#         general = bot.get_channel(843641902371700739)
#         await general.send('Is it working?')
#         await asyncio.sleep(3)
#
# @bot.command()
# async def info(ctx):
#     bot.loop.create_task(my_task(ctx))
#
# @bot.command(name='99')
# async def nine_nine(ctx):
#     quotes = ['b', 'c', 'd']
#     response = choice(quotes)
#     await ctx.send(response)

# myLoop.start()
bot.run(TOKEN)
quit()