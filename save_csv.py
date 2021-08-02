import sys
print(sys.argv[0])
import logging
import binance
from binance.spot import Spot
import os
import getopt
from binance.lib.utils import config_logging
from binance.error import ClientError
from binance.enums import *
from binance.client import Client
import math
import time
import csv
import binance_login
from datetime import date, datetime, timedelta
api_key = binance_login.API_KEY
secret_key = binance_login.SECRET_KEY
from binance_config import *
#"1 Jan, 2015" 

#make an app that 
#buys crypo if the daily change is -20%
#sells crpto if the daily change is +20%



#client = Client()
#print(client.time())

client = Client(api_key, secret_key)
tickers = client.get_ticker()
exchange_info = client.get_exchange_info().get('symbols')


# fetch 1 minute klines for the last day up until now
#klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")

# fetch 1 day klines for jun-jul 2021
#klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_1DAY, "1 Jun, 2021", "1 Jul, 2021")

#print(get_price_change_percentage_list('BTCUSDT'))

# fetch weekly klines since it listed
#klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")


#GENERATOR
#for kline in client.get_historical_klines_generator("ETHBTC", Client.KLINE_INTERVAL_1DAY, "1 Jun, 2021", "1 Jul, 2021"):
#    print(kline)

'''
1499040000000,      # Open time
"0.01634790",       # Open
"0.80000000",       # High
"0.01575800",       # Low
"0.01577100",       # Close
"148976.11427815",  # Volume
1499644799999,      # Close time
"2434.19055334",    # Quote asset volume
308,                # Number of trades
"1756.87402397",    # Taker buy base asset volume
"28.46694368",      # Taker buy quote asset volume
"17928899.62484339" # Can be ignored
'''
TRADE_SYMBOL = 'BTCUSDT'
if len(sys.argv)>1:
	TRADE_SYMBOL = sys.argv[1].upper()

LAST_X_DAYS = 3650
if len(sys.argv)>2:
	LAST_X_DAYS = int(sys.argv[2])

def calculate_percentage_change(current, previous):
    if current == previous:
        return 100.0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0

def get_trade_klines(coin_trade_str, last_x_days=10):

	csv_file_path =EXPORT_DIR+coin_trade_str+'.csv'

	with open(csv_file_path, 'w', newline='') as csvfile:

		spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		headers = ['open_time',
			'open',
			'high',
			'low',
			'close',
			'volume',
			'close_time',
			'quote_asset_volume',
			'number_of_trades',
			'taker_buy_base_asset_volume',
			'taker_buy_quote_asset_volume',
			'price_change_percent']
		spamwriter.writerow(headers)


		today = date.today()
		yesterday = today - timedelta(days=1)
		yesterday = yesterday.strftime("%B %d, %Y")

		someday = today - timedelta(days=LAST_X_DAYS)
		someday = someday.strftime("%B %d, %Y")		


		print (TRADE_SYMBOL, '-', someday, '-', today.strftime("%B %d, %Y"), '-', LAST_X_DAYS)


		klines = client.get_historical_klines(coin_trade_str, Client.KLINE_INTERVAL_1DAY, someday)# "{} days ago".format(int(last_x_days)))
		#print(len(klines))
		coin_klines = []
		for kline in klines:
			#open/close (which binance uses to calculate the 24 hour period)
			open_price = float(kline[1])
			close_price = float(kline[4])
			#high/low
			highlow=False
			if highlow:
				open_price = float(kline[3])
				close_price = float(kline[2])

			#price_change_percent = calculate_percentage_change(open_price, close_price)
			#if open_price > close_price:
			#	price_change_percent*=-1
			open_time = str(datetime.fromtimestamp(int(kline[0]/1000)))
			close_time = str(datetime.fromtimestamp(int(kline[6]/1000)))

			kline[0] = open_time
			kline[6] = close_time


			price_change_percent = round(close_price * 100 / open_price - 100, 2)
			kline.append(price_change_percent)
			kline_dict = {
				'open_time': kline[0],
				'open': kline[1],
				'high': kline[2],
				'low' : kline[3],
				'close': kline[4],
				'volume': kline[5],
				'close_time': kline[6],
				'quote_asset_volume': kline[7],
				'number_of_trades': kline[8],
				'taker_buy_base_asset_volume': kline[9],
				'taker_buy_quote_asset_volume': kline[10],
				'price_change_percent' : kline[11]
			}
			#print(kline_dict)
			coin_klines.append(kline_dict)
			spamwriter.writerow(kline)
			print( kline_dict )
			#time.sleep(1)
		#print(coin_klines)
	return coin_klines

def get_price_change_percentage_list(coin_trade_str, coin_klines=None):
	if not coin_klines:
		coin_klines = get_trade_klines(coin_trade_str)
	kline_percentages = []
	for i in coin_klines:
		kline_percentages.append( i.get('price_change_percent') )
	return kline_percentages


def get_my_coins():
	#Returns a list of coin types(dicts): [{'asset': 'BTC', 'free': '0.00028971', 'locked': '0.00000000'},..]
	coins_in_accounts = client.get_account().get('balances')
	coins_in_accounts = [i for i in coins_in_accounts if (float(i.get('free')) != 0.0 or float(i.get('locked')) != 0.0) ]
	return coins_in_accounts

def get_tradable_coins(coin_str, coin_exchange_symbols=None):
	#returns a list of tradable coins from a given coin.
	coin_exchange_symbols = None or client.get_exchange_info().get('symbols')
	available_coin_trades = [i.get('symbol') for i in coin_exchange_symbols if (coin_str in i.get('symbol') and i.get('status') == 'TRADING' and i.get('isSpotTradingAllowed') == True)]

	return available_coin_trades

def get_coin_price_change_percent(coin_trade_str):
	coin_24hr_change = client.get_ticker(symbol=coin_trade_str)
	if coin_24hr_change:
		priceChangePercent = coin_24hr_change.get('priceChangePercent')
		if priceChangePercent:
			return float( priceChangePercent )
		else:
			return None
	else:
		return None

def get_coin_price(coin_trade_str):
	tickers = client.get_all_tickers()
	coin_price = [i for i in tickers if i.get('symbol') == coin_trade_str][0]
	coin_price_str = coin_price.get('price')
	coin_price_float = float(coin_price_str)
	return coin_price_float

def get_coin_info(coin_trade_str):

	exchange_info = client.get_exchange_info().get('symbols')
	return [i for i in exchange_info if i.get('symbol') == coin_trade_str][0]


def buy_coin(coin_trade_str, buy_quantity):
	#This works
	try:
		order = client.create_test_order(
		        symbol=coin_trade_str,
		        side=Client.SIDE_BUY,
		        type=Client.ORDER_TYPE_MARKET,
		        quantity=str(buy_quantity)
		    )
		print(order)
		return order
	except Exception as e:
		print(e)
		return e

def sell_coin(coin_trade_str, sell_quantity):
	#This works
	try:
		order = client.create_test_order(
		        symbol=coin_trade_str,
		        side=Client.SIDE_SELL,
		        type=Client.ORDER_TYPE_MARKET,
		        quantity=str(sell_quantity)
		    )
		print(order)
		return order
	except Exception as e:
		print(e)
		return e


def get_coins_daily_changes(coin_trade_str, last_x_days):
	#returns a list of percentage changes by day
	return

def get_coins_above_percent_change(percent, coins_in_accounts=None):
	#returns a dict of key/value pairs of exchange symobl / percentage
	ret_list = {}
	if not coins_in_accounts:
		coins_in_accounts = get_my_coins()
	for coin_item in coins_in_accounts:
		coin_tradables = get_tradable_coins(coin_item.get('asset'),coin_exchange_symbols=exchange_info)
		
		for tradable in coin_tradables:
			item = [i for i in tickers if i.get('symbol') == tradable][0]
			#change_percent = get_coin_price_change_percent(tradable)
			change_percent = float(item.get('priceChangePercent'))
			if abs(change_percent) > abs(float(percent)):
				#t = {tradable:change_percent}
				#current_coin = get_coin_info(tradable)
				#print (current_coin)
				coin_klines = get_trade_klines(tradable)
				#print (coin_klines)
				price_change_list = get_price_change_percentage_list(tradable, coin_klines=coin_klines)
				#print(tradable, change_percent, price_change_list)
				ret_list[tradable] = change_percent
		#print(coin_tradables)
		pass
	return ret_list

def get_coins_below_percent_change(percent, coins_in_accounts=None):
	#returns a dict of key/value pairs of exchange symobl / percentage
	ret_list = {}
	if not coins_in_accounts:
		coins_in_accounts = get_my_coins()
	for coin_item in coins_in_accounts:
		coin_tradables = get_tradable_coins(coin_item.get('asset'),coin_exchange_symbols=exchange_info)
		
		for tradable in coin_tradables:
			item = [i for i in tickers if i.get('symbol') == tradable][0]
			#change_percent = get_coin_price_change_percent(tradable)
			change_percent = float(item.get('priceChangePercent'))
			if abs(change_percent) < abs(float(percent)):
				#t = {tradable:change_percent}
				#current_coin = get_coin_info(tradable)
				#print (current_coin)
				coin_klines = get_trade_klines(tradable)
				#print (coin_klines)
				price_change_list = get_price_change_percentage_list(tradable, coin_klines=coin_klines)
				print(tradable, change_percent, price_change_list)
				ret_list[tradable] = change_percent
		#print(coin_tradables)
		pass
	return ret_list


def process_trade(coin, price_change_list):
	#detect wether to buy,sell or wait based on price_change_list data.  
	current_coin = get_coin_info(coin)
	change_percent = get_coin_price_change_percent(coin)
	coin_price = get_coin_price(coin)
	#snapshot_info = client.get_account_snapshot(type='SPOT')

	

	for i in current_coin.get('filters'):
		#print(i)
		filter_type = i.get('filterType')
		if filter_type == 'LOT_SIZE':
			lot_size_filter = i
		elif filter_type == 'MIN_NOTIONAL':
			minNotional = float(i.get('minNotional'))
			min_notional_filter = i
		elif filter_type == 'PRICE_FILTER':
			price_filter = i


	# THE FOLLOWING FILTERS NEEDS TO BE MET.
	min_price 	 = float(price_filter.get('minPrice'))
	max_price 	 = float(price_filter.get('maxPrice'))
	tick_size 	 = float(price_filter.get('tickSize'))

	min_qty   	 = float(lot_size_filter.get('minQty'))
	max_qty   	 = float(lot_size_filter.get('maxQty'))
	step_size 	 = float(lot_size_filter.get('stepSize'))

	min_notional = 0.0
	if min_notional_filter.get('applyToMarket'):
		min_notional = float(min_notional_filter.get('minNotional'))

	coin_precision = int(current_coin.get('quotePrecision'))


	if price_change_list[-1] < -20:
		action = 'buy'

	elif price_change_list[-1] > 20: 
		action = 'sell'

	else:
		action = 'wait'

	print('\t<<< {} price: {} 24hr % change:{} 3 day % change: {} >>>'.format(coin,coin_price,change_percent,price_change_list))
	if action == 'buy':
		usdt_amount = 10
		usdt_amount = min_notional+1

		buy_quantity = round( usdt_amount / coin_price, coin_precision )
		buy_quantity = math.floor(buy_quantity / step_size) * step_size
		buy_price = buy_quantity * coin_price
		while buy_price < min_notional:
			buy_quantity = round( buy_quantity+step_size,coin_precision )
			buy_quantity = math.floor(buy_quantity / step_size) * step_size
			buy_price = buy_quantity * coin_price

		#print('\t<<< {} price: {} 24hr % change:{} 3 day % change: {} >>>'.format(coin,coin_price,change_percent,price_change_list))
		print('\t<<<{} : {} price: {} quantity:{} >>>'.format(action.upper(), coin, buy_price, buy_quantity))
		result = buy_coin(coin, buy_quantity)

		return result

	elif action == 'sell':
		usdt_amount = 10
		usdt_amount = min_notional+1

		buy_quantity = round( usdt_amount / coin_price, coin_precision )
		buy_quantity = math.floor(buy_quantity / step_size) * step_size
		buy_price = buy_quantity * coin_price
		while buy_price < min_notional:
			buy_quantity = round( buy_quantity+step_size,coin_precision )
			buy_quantity = math.floor(buy_quantity / step_size) * step_size
			buy_price = buy_quantity * coin_price

		#print('\t<<< {} price: {} 24hr % change:{} 3 day % change: {} >>>'.format(coin,coin_price,change_percent,price_change_list))
		print('\t<<<{} : {} price: {} quantity:{} >>>'.format(action.upper(), coin, buy_price, buy_quantity))
		result = sell_coin(coin, buy_quantity)

		return result

	else:
		#print('\t<<<{} : {} >>>'.format(action, coin))
		return

'''
coins_in_accounts = get_my_coins()
#for i in coins_in_accounts:
#	print(i)
coins_in_accounts = [i for i in coins_in_accounts if i.get('asset') == 'USDT']
coin_tradables = get_tradable_coins('USDT',coin_exchange_symbols=exchange_info)
#print(coin_tradables

print('changes greater than %20')
relevant_coins = get_coins_above_percent_change(20,coins_in_accounts=coins_in_accounts)
#print (relevant_coins)
for coin in relevant_coins:
	#print (coin)
	coin_klines = get_trade_klines(coin)
	price_change_list = get_price_change_percentage_list(coin, coin_klines=coin_klines)
	#print(coin, price_change_list)
	process_trade(coin, price_change_list)
'''
if TRADE_SYMBOL.lower() == 'all':
	all_symbols = sorted(list(set([i.get('symbol') for i in exchange_info if i.get('status') == 'TRADING' and i.get('isSpotTradingAllowed')])))
	for i in all_symbols:
		print (i)
		x=get_trade_klines(i)
		waittime = 5
		for w in range(waittime):
			sstr = '...waiting... ({}/{})'.format(w,waittime)
			print(sstr)
			time.sleep(1)

else:
	x=get_trade_klines(TRADE_SYMBOL)





#coin = 'BTCUSDT'



'''
order = client.create_test_order(
    symbol='BNBBTC',
    side=SIDE_BUY,
    type=ORDER_TYPE_LIMIT,
    timeInForce=TIME_IN_FORCE_GTC,
    quantity=100,
    price='0.00001')

print (order)
'''