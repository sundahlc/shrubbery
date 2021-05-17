from random import choice
import os
import discord
from discord.ext import tasks, commands
import psycopg2
from dotenv import load_dotenv

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

    # print(f'{client.user} has connected to Discord!')
    # for guild in client.guilds:
    #     if guild.name == GUILD:
    #         break

    # guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    guild = discord.utils.get(bot.guilds, name=GUILD)
    channels = bot.get_all_channels()
    channel_list = list()
    for channel in channels:
        channel_list.append(channel)
    general = bot.get_channel(843641902371700739)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    #
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
    print(f'Channels: {channel_list}')

    await general.send('Disconnecting, goodbye!!')

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
bot.close()
quit()