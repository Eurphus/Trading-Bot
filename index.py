# Imports
import discord
import json
import asyncio
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
import matplotlib.pyplot as plt

# Import data from config.json
with open('/media/sf_Shared_Folders/Trading_Bot/config.json') as data:
    config = json.load(data)
# Mysql
import mysql.connector

# Establish Connection
db = mysql.connector.connect(
    host=config["SQL"]["HOST"],
    user=config["SQL"]["USER"],
    password=config["SQL"]["PASS"],
    database=config["SQL"]["DATABASE"]
)

database = db.cursor()

# Initialize API Client
APIClient = Client(config["API"]["API_KEY"],config["API"]["API_SECRET"])

# Check Symbol Information
class symbolPrice():
    def __init__(self, symbol):
        coin = symbol.upper().replace("USDT", "") + 'USDT'
        self.ticker = APIClient.get_ticker(symbol=coin)
        self.averagePrice = float(self.ticker.get('weightedAvgPrice'))
        self.lastPrice = float(self.ticker.get("lastPrice"))
        self.dailyTicker = self.ticker.get("priceChangePercent")
        self.info = APIClient.get_symbol_info(coin)
        self.balance = float(APIClient.get_asset_balance(asset=coin.replace("USDT", ""))["free"])
        # print(self.info["filters"][-3]["stepSize"])

# Find a user through ID's, useful in future
class findUser():
    def __init__(self, type, id):
        if(type == 'discord'):
            database.execute(f"SELECT * FROM userdata WHERE discordid={self.id}")
            data = database.fetchone()
            if(data == None):
                self.userid='invalid'
            else:
                self.userid=data[0]
        if(type == 'telegram'):
            database.execute(f"SELECT * FROM userdata WHERE telegramid={self.id}")
            data = database.fetchone()
            if(data == None):
                self.userid='invalid'
            else:
                self.userid=data[0]

# Buy order
class buyOrder():
    def __init__(self, type, symbol, amount):
        coin = symbol.upper()
        data = symbolPrice(symbol)
        lastPrice = data.lastPrice

        # Get proper quantity
        stepSize = data.info["filters"][2]["stepSize"]
        precision = int(round(-math.log(float(stepSize), 10), 0))
        quantity = round((amount/lastPrice)*0.9995, precision)
        if(type == 'spot'):
            try:
                APIClient.create_order(
                symbol=coin,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                # timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity
                # price=lastPrice
                );
            except BinanceAPIException as APIError:
                 print(APIError)
            else:
                print(f"Bought {coin} {quantity} @ {lastPrice}")
        if(type == 'margin' or type == 'isolated'):
            isolated="False"
            if(type == 'isolated'):
                isolated='True'
            try:
                APIClient.create_margin_order(
                symbol=coin,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                isolated=isolated
                );
            except BinanceAPIException as APIError:
                 print(APIError)
            else:
                print(f"Bought {coin} {quantity} @ {lastPrice}")

# Sell Order
class sellOrder():
    def __init__(self, type, symbol, amount):
        coin = symbol.upper()
        data = symbolPrice(symbol)
        lastPrice = data.lastPrice
        print(data.balance)

        # Get proper quantity
        stepSize = data.info["filters"][2]["stepSize"]
        precision = int(round(-math.log(float(stepSize), 10), 0))
        quantity = round(data.balance*0.9995, precision)
        print(stepSize)
        print(precision)
        print(quantity)
        if(type == 'spot'):
            try:
                APIClient.create_order(
                symbol=coin,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                # timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                # price=lastPrice
                );
            except BinanceAPIException as APIError:
                 print(APIError)
            else:
                print(f"Sold {coin} {quantity} @ {lastPrice}")
        if(type == 'margin' or type == 'isolated'):
            isolated="False"
            if(type == 'isolated'):
                isolated='True'
            try:
                APIClient.create_margin_order(
                symbol=coin,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                isIsolated=isolated
                );
            except BinanceAPIException as APIError:
                 print(APIError)
            else:
                print(f"Sold {coin} {quantity} @ {lastPrice}")

# Create User Class
class createUser():
    def __init__(self, type, id):
        execute=""
        if(type=='discord'):
            execute=f"INSERT INTO userdata (exchangetype, discord, discordid) VALUES ('binance', True, {id})"
        elif(type=='telegram'):
            execute=f"INSERT INTO userdata () VALUES ()"
        database.execute(execute)

# Discord Client
class MyClient(discord.Client):
    # On Ready event
    async def on_ready(self):
        print('Discord Bot Up')

    # on message event
    async def on_message(self, message):
        if(message.content.startswith('!')):
            args = message.content.replace('!', '').split()

            # Price command
            if(str(args[0]) == 'price'):
                if(args):
                    coin = args[1].upper()
                    embedVar = discord.Embed(title=coin + "/USDT", description=f"`{symbolPrice(coin).averagePrice}` **({symbolPrice(coin).dailyTicker}%)**", color=0x36393F, footer='Data provided by Binance API')
                    await message.channel.send(embed=embedVar)

# Price checking event
async def priceTarget(symbol, userid, type):

    # Define 2 arrays for data collection
    x=[];
    y=[];
    while True:
        await asyncio.sleep(10)

        # Query database for trades related to this user with the same symbol
        database.execute(f'SELECT * FROM usertrades WHERE userid={userid} AND symbol="{symbol}";')
        data = database.fetchone()
        target = data[-1]

        # Compare live price & price target
        lastPrice = symbolPrice(symbol).lastPrice
        if(len(x) >= 21000):
            plt.plot(x, label='Price Target')
            plt.plot(y, label='Last Price')
            plt.show()


        # If price rises above target, upgrade target
        if(target < lastPrice):
            print(f'Price Target for ${symbol} Updated to {lastPrice} | lastPrice: {lastPrice} | Target: {target}')
            database.execute(f'UPDATE usertrades SET target={lastPrice} WHERE userid={userid} AND symbol="{symbol}";')

            # If symbol is not already bought when it reaches the target, buy
            if(data[5] == False):
                print(f"Buying {symbol}")
                database.execute(f'UPDATE usertrades SET activeTrade=True WHERE userid="{userid}"')# AND symbol="{symbol}";')
                buyOrder("spot", symbol, data[4])

        # If prices dips below target
        if(target > lastPrice):
            print(f'Price of ${symbol} has fallen, target uneffected. | lastPrice: {lastPrice} | Target: {target}')

            # If symbol is bought when it dips below target, sell
            if(data[5] == True):
                print(f"Selling {symbol}")
                database.execute(f'UPDATE usertrades SET activeTrade=False WHERE userid="{userid}" AND symbol="{symbol}";')
                sellOrder("spot", symbol, data[4])
        x.append(target)
        y.append(lastPrice)


# Event Loop
loop=asyncio.get_event_loop()
try:
    database.execute('SELECT * from usertrades')
    for data in database.fetchall():
        asyncio.ensure_future(priceTarget(data[1], data[2], data[0]))
    loop.run_forever()
finally:
    print("Loop Closed")
    loop.close()

# Run Discord Bot
client = MyClient()
client.run(config["DISCORD_KEY"])
