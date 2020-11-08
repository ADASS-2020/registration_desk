import asyncio
import csv
import logging
import re
import os
import discord
from discord.ext import commands
from discord.utils import get

# logging config
logging.basicConfig(
    filename='.log/reg.log',
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d-%b-%y %H:%M:%S',
)

# set up channel ids and enviroment variables
reg_channel_id = int(os.environ['REG_CHANNEL_ID'])

try:
    log_channel_id = int(os.environ['LOG_CHANNEL_ID'])
except Exception:
    log_channel_id = None

try:
    only_respond_reg = int(os.environ['ONLY_RESPOND_REG'])
except Exception:
    only_respond_reg = False

ROLES = (
    'speaker',
    'trainer',
    'posterauth',
    'admin',
    'loc',
    'poc',
    'volunteer',
)


# TODO: seperate customization in conf file
event_name = 'ADASS'

instruction = f'Welcome to {event_name}! ' + \
    'Please use `!register <Full Name>, <registration reference>` to ' + \
    'register.\nE.g. `!register James Brown, 0123-ABCDEFG-456`'

last_help_msg = None
help_msg_every = 10         # how many messages between auto help messages


def welcome_msg(mention, roles):
    if len(roles) == 2:
        return f'Welcome {mention}, you now have the ' + \
            f'{roles[0]} and {roles[1]} roles.'
    elif len(roles) == 1:
        return f'Welcome {mention}, you now have the {roles[0]} role.'
    else:
        text = ', '.join(roles[1:-1])
        return f'Welcome {mention}, you now have the ' + \
            f'{roles[0]}, {text} and {roles[-1]} roles.'


bot = commands.Bot(
    command_prefix='!',
    description=f'Registration Desk for {event_name}',
    help_command=None,
)


def get_input(info):
    result = re.match(r"([\w\s.\-\\']+)[,|#\W]+(\S+)", info)
    if result:
        return result.group(1), result.group(2)


def roles_given(name, ticket_id):
    # check the roles that need to be given to the user
    # return list of roles that need to be given
    with open(os.environ['DATA_PATH'], newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        for person in datareader:
            try:
                if ticket_id.lower() == person.get('ticket_id', '').lower():
                    if name.lower() == person.get('name', '').lower():
                        # All good: get roles.
                        roles = [r for r in ROLES
                                 if person.get(f'is{r}', 'False') == 'True']
                        roles.append('attendee')
                        return roles
            except Exception as e:
                logging.warn(f'Exception {e!r} while processing reg file')
                continue


async def resend_help():
    global last_help_msg
    await bot.wait_until_ready()
    channel = bot.get_channel(reg_channel_id)
    while True:
        messages = await channel.history(after=last_help_msg).flatten()
        if len(messages) >= help_msg_every:
            last_help_msg = await channel.send(instruction)
        await asyncio.sleep(10)                 # task runs every x seconds


@bot.event
async def on_ready():
    global last_help_msg
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening,
                                  name='!help'),
    )
    last_help_msg = await bot.get_channel(reg_channel_id).send(instruction)
    print('Bot is ready')
    logging.info('Bot logged in')


@bot.command()
async def register(ctx, *, info):
    log_msg = None

    if not only_respond_reg or ctx.channel.id == reg_channel_id:
        try:
            name, ticket_id = info.rsplit(',', maxsplit=1)
            name = name.strip()
            ticket_id = ticket_id.strip()
        except Exception:
            name = 'Unknown'
            ticket_id = None

        mem_nick = list(map(lambda mem: mem.nick, ctx.guild.members))

        if name in mem_nick:  # if nick is taken
            await ctx.message.delete()
            update_msg = await ctx.send(
                f'Cannot register {name}, please check and try again, ' +
                'or ask @loc for help'
            )

            await ctx.author.send(
                f'{ctx.author.mention} Sorry, your name has already been registered. The reason could be:\n1) your ticket has not be assgined to you property or;\n2) although it seems quite rare, someone has the same name as you.\n\nYou may ask the person who bought you the ticket to check if they have assgin the ticket to you with your full name. In anycase, if you need a team member to help, contact @loc in the channel'       # noqa
            )
            roles = []
            log_msg = f'FAIL: Request form user {ctx.author} with name={name}, ticket_id={ticket_id} has duplicated name'           # noqa
        else:
            if ticket_id is not None:
                roles = roles_given(name, ticket_id)
            else:
                roles = None

        if roles is None:  # if no match from data
            log_msg = f'FAIL: Cannot find request form user {ctx.author} with name={name}, ticket_id={ticket_id}'  # noqa

            await ctx.message.delete()
            update_msg = await ctx.send(
                f'Cannot register {name}, please check and try again, or ask @loc for help'                    # noqa
            )

            await ctx.author.send(
                f'{ctx.author.mention} Sorry, cannot find the ticket associated to {ticket_id} with name: {name}.\n\nPlease check and make sure:\n1) the name and registration reference match your registration details ;\n2) seperate you name and registration reference with a ",";\nthen try again.\n\nIf you want a team member to help you, please contact @loc in the channel'     # noqa
            )
        elif len(roles) > 0:  # if match found
            log_msg = f'SUCCESS: Register user {ctx.author} name={name}, ticket_id={ticket_id} with roles={roles}'      # noqa

            for role in roles:
                role_id = get(ctx.author.guild.roles, name=role)
                await ctx.author.add_roles(role_id)

            await ctx.author.send(welcome_msg(ctx.author.mention, roles))

            # Change username to the person real name
            # if roles != ['attendee']:
            if roles:
                if len(name) > 32:
                    reg_role = get(ctx.author.guild.roles, name='registration')
                    await ctx.send(f'Sorry {ctx.author.mention}\'s name {name} is too long for Discord to handle. {reg_role.mention} could you contact them and handle it?')     # noqa
                else:
                    await ctx.author.edit(nick=name)

            await ctx.message.delete()
            update_msg = await ctx.send(f'{name} registered')
            await update_msg.add_reaction('🎟️')
            await update_msg.add_reaction('🤖')

        if log_msg is not None:
            logging.info(log_msg)
            if log_channel_id is not None:
                await bot.get_channel(log_channel_id).send(log_msg)


@bot.command()
async def help(ctx):
    global last_help_msg
    if not only_respond_reg or ctx.channel.id == reg_channel_id:
        last_help_msg = await ctx.send(instruction)

bot.loop.create_task(resend_help())
bot.run(os.environ['REG_BOT_SECRET'])
