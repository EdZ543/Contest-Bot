import os
import discord
import requests
import datetime
import pytz
from discord.ext import commands, tasks
from replit import db

bot = commands.Bot(command_prefix='c!')
api_url = 'https://dmoj.ca/api/v2/contests'
thumbnail_url = 'https://avatars.githubusercontent.com/u/6934864?s=200&v=4'
contests_url_prefix = 'https://dmoj.ca/contest/'
interval = 10
time_zone = pytz.timezone('EST5EDT')
time_format = '%B %d, %Y, %I:%M%p %Z'

async def send_contest(contest, channel):
	embed = discord.Embed()
	embed.title = contest['name']
	embed.description = contests_url_prefix + contest['key']
	embed.set_thumbnail(url=thumbnail_url)
	embed.add_field(name='Rated', value='Yes' if contest['is_rated'] else 'No', inline=False)
	start_time = datetime.datetime.strptime(contest['start_time'], '%Y-%m-%dT%H:%M:%S%z').astimezone(time_zone).strftime(time_format)
	embed.add_field(name='Start Time', value=start_time, inline=False)
	end_time = datetime.datetime.strptime(contest['end_time'], '%Y-%m-%dT%H:%M:%S%z').astimezone(time_zone).strftime(time_format)
	embed.add_field(name='End Time', value=end_time, inline=False)

	await channel.send(embed=embed)

@tasks.loop(seconds=interval)
async def get_new_contests():
	for server_id in db.keys():
		server = db[server_id]
		channel = bot.get_channel(server['channel_id'])
		if channel == None:
			del db[server_id]
			continue

		response = requests.get(api_url)
		response_data = response.json()['data']['objects']

		for contest in response_data:
			contest_date = datetime.datetime.strptime(contest['end_time'], '%Y-%m-%dT%H:%M:%S%z')
			now_date = pytz.utc.localize(datetime.datetime.now())

			if contest_date > now_date and contest['key'] not in server['current_contests']:
				server['current_contests'].append(contest['key'])
				await send_contest(contest, channel)
			elif contest_date < now_date and contest['key'] in server['current_contests']:
				server['current_contests'].remove(contest['key'])

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	get_new_contests.start()

@bot.command(name='set')
async def set_channel(ctx):
	global context

	server_id = str(ctx.message.guild.id)
	if server_id not in db.keys():
		db[server_id] = {
			'current_contests': [],
			'channel_id': None,
		}

	db[server_id]['channel_id'] = ctx.message.channel.id

	message = f'Ight contest notifications will appear in {ctx.message.channel.mention}'
	await ctx.reply(message)

bot.run(os.environ['DISCORD_TOKEN'])