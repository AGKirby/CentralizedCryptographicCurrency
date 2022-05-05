import os

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True

from flask import Flask
from threading import Thread
from itertools import cycle

import ninshubur
from replit import db

import logger

app = Flask('')


@app.route('/')
def main():
    return "Your Bot Is Ready"


def run():
    print("Running Bot")
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    server = Thread(target=run)
    print("Bot is alive")
    server.start()


TOKEN = os.environ['TOKEN']

bot = commands.Bot(command_prefix='~', intents=intents)

status = cycle(['with Python', 'JetHub'])


@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))



@bot.event
async def on_ready():
    # change_status.start()
    print(f'{bot.user} is connected to the server.')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Update Daily Quote
    if(bot.user.mentioned_in(message) and message.channel_id == 920838708519911457): #bot @-ed in #daily-quote channel
        db["daily_quote_msg"] = message.message_id
        db["daily_quote_reactors"] = []
        # Reduce quote purchase price
        global min_quote_price, quote_price_reduction
        if(db["quote_price"] >= (min_quote_price + quote_price_reduction)):
            db["quote_price"] -= quote_price_reduction
        return
    
    await bot.process_commands(message)


###################################################
### Commands to add Discord wallet data in cache
###################################################

@bot.command(
    name='create_wallet',
    help="Creates your own wallet. Use: ~create_wallet [name]"
)
async def create_wallet(ctx, *, name):
    logger.addLog(str(ctx.author), str(ctx.guild), "create_wallet", [name])
    discord = ctx.author
    senderid = getdbkey(discord, "id")
    if senderid is None:
        await ctx.send("Error: You already have a wallet")
        return 
    success, response = ninshubur.createWallet(name, str(discord))
    if success:
        result = ""
        updatedb(discord, "id", response["wallet_id"])
        updatedb(discord, "name", name)
        updatedb(discord, "public_key", response["public_key"])
        output = response["message"]
        output += "\nID: " + str(response["wallet_id"])
        output += "\nPublic Key: " + response["public_key"]
        channel = await discord.create_dm()  #DM private key
        await channel.send(response["private_key"])
        response = output
        logger.writeLog("Success")
    else:
        result = "Error: "
        logger.writeLog("Error")
    await ctx.send(result + response)


def updatedb(discord, key, value):
    fullKey = str(discord) + ":" + key
    db[fullKey] = value


def getdbkey(discord, key):
    fullKey = str(discord) + ":" + key
    if fullKey not in db.keys():
        return None
    return db[fullKey]


@bot.command(
    name='add_id',
    help="Add your wallet id to bot's cache. Use: ~add_id [id]"
)
async def add_id(ctx, id):
    logger.addLog(str(ctx.author), str(ctx.guild), "add_id", [id])
    discord = ctx.author
    try: 
        userid = int(id)
        print(str(userid))
        if(not isinstance(userid, int) or userid < 0):
            await ctx.send("Invalid ID")
            return
        print("Updating db")
        updatedb(discord, "id", userid)
    except:
        await ctx.send("Invalid ID")   
        logger.writeLog("Error: Invalid ID")
        return
    await ctx.send("Successfully added your wallet id to bot's cache")
    logger.writeLog("Success")


@bot.command(
    name='add_name',
    help="Add your name to bot's cache. Use: ~add_name [name]"
)
async def add_name(ctx, *, name):
    logger.addLog(str(ctx.author), str(ctx.guild), "add_name", [name])
    discord = ctx.author
    updatedb(discord, "name", name)
    await ctx.send("Successfully added your name to bot's cache")
    logger.writeLog("Success")


@bot.command(
    name='add_public_key',
    help="Add your public key to bot's cache. Use: ~add_public_key [public_key]"
)
async def add_public_key(ctx, *, public_key):
    logger.addLog(str(ctx.author), str(ctx.guild), "add_public_key", [public_key])
    discord = ctx.author
    updatedb(discord, "public_key", public_key)
    await ctx.send("Successfully added your public key to bot's cache")
    logger.writeLog("Success")


@bot.command(
    name='add_private_key',
    help="Add your private key to bot's cache. WARNING: Do not use if security is a high priority! Use: ~add_private_key [private_key]"
)
async def add_private_key(ctx, *, private_key):
    logger.addLog(str(ctx.author), str(ctx.guild), "add_private_key", [])
    discord = ctx.author
    updatedb(discord, "private_key", private_key)
    await ctx.send("Successfully added your private key to bot's cache")
    logger.writeLog("Success")
  

###################################################
### Commands for the currency
###################################################

@bot.command(
    name='public_board',
    help="Get the public board of wallets. Use: ~public_board"
)
async def public_board(ctx):
    logger.addLog(str(ctx.author), str(ctx.guild), "public_board", [])
    success, response = ninshubur.getPublicBoard()
    if success:
        result = ""
        array = response.split(",")
        board = ""
        itemNum = 1
        for item in array: 
            if(itemNum == 4): #drop public key
                itemNum = 1
            else: 
                itemNum += 1
                content = item
                if(itemNum != 4):
                    content += ", "
                else: 
                    content += "\n"
                board += content
        response = board
        logger.writeLog("Success")
    else: 
        result = "Error: "
        logger.writeLog("Error")
    await ctx.send(result + response)


@bot.command(
    name='my_balance',
    help="Get your wallet's balance. Use: ~my_balance *[private_key]*"
)
async def my_balance(ctx, *, private_key=""):
    logger.addLog(str(ctx.author), str(ctx.guild), "my_balance", [private_key])
    discord = ctx.author
    senderid = getdbkey(discord, "id")
    if senderid is None:
        logger.writeLog("Error: Your wallet is not registered with this Discord Bot")
        await ctx.send("Error: Your wallet is not registered with this Discord Bot")
        return
    prvKey = str(discord)+":private_key"
    if prvKey in db.keys() and db[prvKey] != "":
        private_key = getdbkey(discord, "private_key")
    privateKey = ninshubur.rsa.PrivateKey.load_pkcs1(private_key)
    success, response = ninshubur.getBalance(senderid, privateKey)
    if success:
        result = ""
        logger.writeLog("Success")
    else: 
        result = "Error: "
        logger.writeLog("Error")
    await ctx.send(result + response)


@bot.command(
    name='transfer',
    help="Get your wallet's balance. Use: ~transfer [send_to_id] [amount] *[private_key]*"
)
async def transfer(ctx, *, args):
    logger.addLog(str(ctx.author), str(ctx.guild), "transfer", [args])
    # Get arguments 
    partioned_args = args.partition(" ")
    send_to_id = partioned_args[0]
    remaining_args = partioned_args[2]
    try: 
        partioned_args = remaining_args.partition(" ")
        amount = partioned_args[0]
        private_key = partioned_args[2]
    except: 
        # if no private key sent
        amount = remaining_args
        private_key = ""
    # Get Discord and Wallet ID
    discord = ctx.author
    senderid = getdbkey(discord, "id")
    if senderid is None: 
        logger.writeLog("Error: Your wallet is not registered with this Discord Bot")
        await ctx.send("Error: Your wallet is not registered with this Discord Bot")
        return
    #Get Receiver ID
    try: 
        receiverid = int(send_to_id)
        if((not isinstance(receiverid, int)) or receiverid < 0):
            logger.writeLog("Invalid argument send_to_id")
            await ctx.send("Invalid argument send_to_id")
            return
    except:
        logger.writeLog("Invalid argument send_to_id")
        await ctx.send("Invalid argument send_to_id")
        return
    #Get Amount
    try: 
        amount = float(amount)
        if((not isinstance(amount, float)) or amount < 0):
            logger.writeLog("Invalid argument amount")
            await ctx.send("Invalid argument amount")
            return
    except:
        logger.writeLog("Invalid argument amount")
        await ctx.send("Invalid argument amount")
        return
    #Get Private Key
    prvKey = str(discord)+":private_key"
    if prvKey in db.keys() and db[prvKey] != "":
        private_key = getdbkey(discord, "private_key")
    privateKey = ninshubur.rsa.PrivateKey.load_pkcs1(private_key)
    success, response = ninshubur.transfer(senderid, receiverid, amount, privateKey)
    if success:
        result = ""
        receiver = getDiscordById(receiverid) 
        if receiver is not None:
            sendReceiveMessage(receiver, amount, discord)
        logger.writeLog("Success")
    else: 
        result = "Error: "
        logger.writeLog("Error")
    await ctx.send(result + response)



@bot.command(
    name='trans',
    help="Get your wallet's balance. Use: ~trans [amount] [receiver_discord]"
)
async def trans(ctx, amount, receiver_discord):
    logger.addLog(str(ctx.author), str(ctx.guild), "trans", [amount, receiver_discord])
    # Get Discord and Wallet ID
    discord = ctx.author
    senderid = getdbkey(discord, "id")
    if senderid is None:
        logger.writeLog("Error: Your wallet is not registered with this Discord Bot")
        await ctx.send("Error: Your wallet is not registered with this Discord Bot")
        return
    # Get Receiver ID
    try: 
        receiver = await bot.fetch_user(receiver_discord)
    except: 
      logger.writeLog("Error: Invalid Receiver Discord id")
      await ctx.send("Error: Invalid Receiver Discord id")
      return
    print(str(receiver))
    receiverid = getdbkey(receiver, "id")
    if receiverid is None:
        logger.writeLog("Error: Receiver does not have a stored id in the bot")
        await ctx.send("Error: Receiver does not have a stored id in the bot")
        return
    receiverid = getdbkey(receiver, "id")
    #Get Amount
    try: 
        amount = float(amount)
        if(not isinstance(amount, float) or amount < 0):
            logger.writeLog("Error: Invalid argument amount")
            await ctx.send("Error: Invalid argument amount")
            return
    except:
        logger.writeLog("Error: Invalid argument amount")
        await ctx.send("Error: Invalid argument amount")
        return
    #Get Private Key
    prvKey = str(discord)+":private_key"
    if prvKey in db.keys() and db[prvKey] != "":
        private_key = getdbkey(discord, "private_key")
    else: 
        logger.writeLog("Error: You must have a stored private key to use this command")
        await ctx.send("Error: You must have a stored private key to use this command")
        return
    privateKey = ninshubur.rsa.PrivateKey.load_pkcs1(private_key)
    success, response = ninshubur.transfer(senderid, receiverid, amount, privateKey)
    if success:
        sendReceiveMessage(receiver, amount, discord)
        logger.writeLog("Success")
    else: 
        logger.writeLog("Error")
        result = "Error: "
    await ctx.send(result + response)


#Utility function for getting a discord by wallet id
def getDiscordById(id):
    discord = None
    for key in db.keys():
        try: 
            if(key.endswith(":id") and id == db[key]):
                return discord
        except: 
            pass
    return None
  

###################################################
### Pay people for reacting to the Daily Quote
###################################################

@commands.has_role("Mod")
@bot.command(
    name='daily_quote_msg',
    help="Update daily quote message id. Must be a mod on the Daily Quote server."
)
async def daily_quote_msg(ctx, msgid):
    if(ctx.guild.id == 920838354042499093):
        db["daily_quote_msg"] = msgid
        await ctx.send("Updated daily quote message id")
        return
    await ctx.send("Failed to update daily quote message id")


@bot.event
async def on_raw_reaction_add(payload):
    if(payload.message_id == db["daily_quote_msg"]):
        discord = payload.author
        id = getdbkey(discord, "id")
        if id is not None and str(discord) not in db["daily_quote_reactors"]:
            logger.addLog(str(payload.author), str(payload.guild), "Daily Quote Reaction", [])
            success, response = ninshubur.transfer(2, id, 10, db["bot_private_key"])
            if success:
                db["daily_quote_reactors"].append(discord)
                sendReceiveMessage(discord, 10, "Currency Bot")
                logger.writeLog("Success")
            else: 
                logger.writeLog("Error")


async def sendReceiveMessage(receiver, amount, sender):
    logger.writeLog("Receive Message to " + str(receiver))
    message = "You received " + str(amount) + "  gratification coins from " + str(sender) + "."
    channel = await receiver.create_dm()  #DM message
    await channel.send(message)

###################################################
### Purchase an Alan's Famous Quote
###################################################

base_quote_price = 1000
min_quote_price = 100
quote_price_reduction = 50
#Initalize Quote Price
if("quote_price" not in db.keys()):
    db["quote_price"] = base_quote_price


@bot.command(
    name='quote_price',
    help="Get the current price to buy a famous quote. Use: ~quote_price"
)
async def quote_price(ctx):
    await ctx.send("The current price to buy one of Adam's Infinite Free Quotes is " + str(db["quote_price"]))


@bot.command(
    name='buy_quote',
    help="Buy one of Adam's Infinite Free Quotes. Get current price with ~quote_price. NOTE: You can only use this command on the Daily Quote discord server. Use: ~buy_quote [quote]"
)
async def buy_quote(ctx, *, quote):
    logger.addLog(str(ctx.author), str(ctx.guild), "buy_quote", [quote])
    # Get Discord and Wallet ID
    discord = ctx.author
    if(ctx.guild.id != 920838354042499093): #Must be on Daily Quote discord
        logger.writeLog("Error: Your must be on the Daily Quote discord server to use this command")
        await ctx.send("Error: Your must be on the Daily Quote discord server to use this command")
        return
    senderid = db[discord + ":id"]
    if senderid is None:
        logger.writeLog("Error: Your wallet is not registered with this Discord Bot")
        await ctx.send("Error: Your wallet is not registered with this Discord Bot")
        return
    #Get Private Key
    prvKey = discord+":private_key"
    if prvKey in db.keys() and db[prvKey] != "":
        private_key = getdbkey(discord, "private_key")
    else: 
        logger.writeLog("Error: You must have a stored private key to use this command")
        await ctx.send("Error: You must have a stored private key to use this command")
        return
    success, response = ninshubur.transfer(senderid, 1, db["quote_price"], private_key)
    if success:
        result = ""
        adam = await bot.fetch_user(591784260340285440)
        sendReceiveMessage(adam, db["quote_price"], discord)
        if(db["quote_price"] < base_quote_price/2):
            db["quote_price"] = base_quote_price
        else: 
            db["quote_price"] = 2 * db["quote_price"]
        alan = await bot.fetch_user(255131611853488128) 
        response = "{}: {} purchased one of {}'s infinite free quotes: {}'".format(alan.mention, discord.mention, adam.mention, quote)
        await ctx.send(response)
        logger.writeLog("Success")
    else: 
        result = "Error: "
        await ctx.send(result + response)
        logger.writeLog("Error")


###################################################
### Commands to add Discord wallet data in cache
###################################################

@commands.has_role("admin")
@bot.command(
    name='get_discord_data',
    help="Get all data saved in Discord database. Use: ~get_discord_data"
)
async def get_discord_data(ctx):
    output = "key,id,name,value\n"
    for key in db.keys():
        output += str(key) + ","
        data = db[key]
        if(hasattr(data, "keys") and "id" in data.keys()):
            output += str(getdbkey(key, "id")) + str(getdbkey(key, "name")) + "\n"
        else: 
            output += str(db[key]) + "\n"
    await ctx.send(output)


@commands.has_role("admin")
@bot.command(
    name='bot_private_key',
    help="Set bot private key. Use: ~bot_private_key"
)
async def bot_private_key(ctx, *, private_key):
    db["bot_private_key"] = private_key


@commands.has_role("admin")
@bot.command(
    name='bot_public_key',
    help="Set bot private key. Use: ~bot_public_key"
)
async def bot_public_key(ctx, *, public_key):
    db["bot_public_key"] = private_key
  

@bot.command(
    name='my_data',
    help="Get all your data saved in Discord bot. CAUTION: Sends Private Key if saved, if so use in private channel. Use: ~my_data"
)
async def my_data(ctx):
    discord = str(ctx.author)
    output = ""
    for key in db.keys():
        if(key.startswith(discord)):
            try: 
                keyStr = key.split(":")[1]
                output += keyStr + ": " + str(db[key]) + "\n"
            except: 
                output += key + ": " + str(db[key]) + "\n"
    await ctx.send(output)


@bot.command(
    name='website',
    help="Get the URL of the associated website. Use: ~website"
)
async def website(ctx):
    await ctx.send("https://courageousranchingsoftwareagent.granetoa.repl.co/")


main()
keep_alive()
bot.run(TOKEN)
#https://discord.com/api/oauth2/authorize?client_id=970366640980127785&permissions=268667904&scope=bot