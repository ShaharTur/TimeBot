import os
from keep_alive import keep_alive
import discord
from discord.ext import commands
import pytz
from replit import db
from datetime import datetime
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials
import json

#giving all permissions for the bot
intents = discord.Intents.all()

bot =commands.Bot(command_prefix = '!',intents=intents)

israel_timezone = pytz.timezone('Etc/GMT-3')


def find_row_by_values(worksheet, search_values):
    rows = worksheet.get_all_values()
    for i,row in enumerate(rows):
      if all(value in row for value in search_values):
          return i+1
    return None

join_times = db['join_times'] if 'join_times' in db else {}
leaving_times=db['leaving_times'] if 'leaving_times' in db else {}
dates = db['date'] if 'date' in db else {}


#Google authentication and spreadsheet connection
with open('credentials.json') as f:
    creds_dict = json.load(f)
scope = ['https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(creds_dict,scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open('Discord_Data')

#for a fresh spreadsheet , making sure the spreadsheet is new and clean for the bot .
worksheet = spreadsheet.get_worksheet(0)
data = ["Date",'Username', 'Join Time','Leaving Time', 'Duration']
if worksheet.row_values(1) != data:
  
  worksheet.delete_rows(1)
  print("Data has been deleted from the spreadsheet.")
  worksheet.insert_row(data, 1)
  print("Data has succesfuly added to the spreadsheet.")






@bot.event
async def on_ready():
  print("TimeBot has logged in to 🍕ℙ𝕚𝕫𝕫𝕒 𝔾𝕣𝕠𝕦𝕡🍕 ")


@bot.event
async def on_voice_state_update(member,before,after):
  #Saving join time and leaving time data of users for the time command and for google sheets
  if before.channel is None and after.channel is not None:
    join_time = discord.utils.utcnow()
    join_time = join_time.astimezone(israel_timezone)    
    join_time = join_time.strftime('%H:%M:%S')
    join_times[str(member.id)] = join_time
    db['join_times']= join_times
    
    date = dt.datetime.now().strftime('%Y-%m-%d')
    dates[str(member.id)]= date
    db["date"]=dates
    data_range = worksheet.get_all_values()
    next_row=len(data_range)+1
    range_address = f"A{next_row}:C{next_row}"
    new_values = [[date,member.name,join_time]]
    worksheet.update(range_address,new_values)
    
    print(f'{member.name} has joined a voice channel at {join_time}')

  if before.channel is not None and after.channel is None:
    #saving the leaving time, calculating the leaving time - join time so i can get the duration of each user staying on the server, finding the correct row in my spread sheet to save the data to when there are multiple users joinning . 
    leaving_time = discord.utils.utcnow()
    leaving_time = leaving_time.astimezone(israel_timezone)
    leaving_time  = leaving_time .strftime('%H:%M:%S')
    leaving_times[str(member.id)] = leaving_time
    db['leaving_time']= leaving_times
    search_values = [dates[str(member.id)],member.name,join_times[str(member.id)]]
    
    current_row =find_row_by_values(worksheet,search_values)
    range_address=f"D{current_row}:E{current_row}"
    join_time_calc= datetime.strptime(worksheet.cell(current_row,3).value,'%H:%M:%S').time()
    leaving_time_calc = datetime.strptime(leaving_time,'%H:%M:%S').time()
    leaving_time_calc=dt.datetime.combine(dt.date(1900,1,1),leaving_time_calc)
    join_time_calc=dt.datetime.combine(dt.date(1900,1,1),join_time_calc)
    duration=leaving_time_calc-join_time_calc
    duration = duration.total_seconds()
    #this if statement prevents the confusion in the code which user joins before 00:00 and leaving after 00:00 which prints on the spread sheet a minus value that is incorrect.
    if duration <0 :
      duration_next_day = duration +86400
      last_values =[[leaving_time,duration_next_day]]
      worksheet.update(range_address,last_values)
    else:
      last_values =[[leaving_time,duration]]
      worksheet.update(range_address,last_values)
  
    
    print(f'{member.name} has left a voice channel at {leaving_time}')
# !hello command and test for the new bot
@bot.command()
async def hello(ctx):
  await ctx.send('Hello to you to !')


# !time command - return to the user the amount of time they stayed on the server . 
@bot.command()
async def time(ctx):
  member = ctx.author
  
  join_time =join_times.get(str(ctx.author.id))
  join_time = datetime.strptime(join_time ,'%H:%M:%S')
  time_now = datetime.now(israel_timezone)
  time_now = time_now.strftime('%H:%M:%S')
  time_now = datetime.strptime(time_now ,'%H:%M:%S')
  delta = time_now - join_time
  hours = delta.seconds//3600
  minutes = (delta.seconds// 60)%60 
  seconds = delta.seconds % 60

  
  

  if join_time is not None and member.voice is not None and member.voice.channel is not None:
    await ctx.send(f'You joined at {join_time.time()} which means you are in the server for {hours} hours,{minutes} mintues and {seconds} seconds')

  else:
    await ctx.send("You didn't join any channel you idiot!")
  
  
  

keep_alive()
token = os.environ['TOKEN']
bot.run(token)
