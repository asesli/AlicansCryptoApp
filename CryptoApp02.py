#from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, QInputDialog, QApplication)
import os
import sys

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView

from datetime import datetime
import time
import logging
import binance

from binance.spot import Spot
from binance.lib.utils import config_logging
from binance.error import ClientError
from binance.enums import *
from binance.client import Client
from time import sleep

from binance import ThreadedWebsocketManager
import math

from pyecharts import Kline

from binance_config import *
import my_trades
import binance_login
import threading

'''
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QProcess, QTextCodec
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QPlainTextEdit
'''

class ProcessOutputReader(QtCore.QProcess):
      produce_output = QtCore.pyqtSignal(str)

      def __init__(self, parent=None):
            super().__init__(parent=parent)

            # merge stderr channel into stdout channel
            self.setProcessChannelMode(QtCore.QProcess.MergedChannels)

            # prepare decoding process' output to Unicode
            codec = QtCore.QTextCodec.codecForLocale()
            self._decoder_stdout = codec.makeDecoder()
            # only necessary when stderr channel isn't merged into stdout:
            # self._decoder_stderr = codec.makeDecoder()

            self.readyReadStandardOutput.connect(self._ready_read_standard_output)
            # only necessary when stderr channel isn't merged into stdout:
            # self.readyReadStandardError.connect(self._ready_read_standard_error)

      @QtCore.pyqtSlot()
      def _ready_read_standard_output(self):
            raw_bytes = self.readAllStandardOutput()
            text = self._decoder_stdout.toUnicode(raw_bytes)
            self.produce_output.emit(text)

      #only necessary when stderr channel isn't merged into stdout:
      @QtCore.pyqtSlot()
      def _ready_read_standard_error(self):
            raw_bytes = self.readAllStandardError()
            text = self._decoder_stderr.toUnicode(raw_bytes)
            self.produce_output.emit(text)



##############

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
        # originally: XStream.stdout().write("{}\n".format(record))


logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            #self.messageWritten.emit(unicode(msg))
            self.messageWritten.emit(msg)
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class MyDialog(QtWidgets.QDialog):
    def __init__( self, parent = None ):
        super(MyDialog, self).__init__(parent)

        self._console = QtWidgets.QTextBrowser(self)
        self._button  = QtWidgets.QPushButton(self)
        self._button.setText('Test Me')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._console)
        layout.addWidget(self._button)
        self.setLayout(layout)

        XStream.stdout().messageWritten.connect( self._console.insertPlainText )
        XStream.stderr().messageWritten.connect( self._console.insertPlainText )

        self._button.clicked.connect(self.test)

    def test( self ):
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')
        print ('Old school hand made print message')


################



'''
API_KEY = binance_login.API_KEY
SECRET_KEY = binance_login.SECRET_KEY
STYLESHEET_FILE =binance_config.STYLESHEET_FILE
SMALL_ICONS_DIR = binance_config.SMALL_ICONS_DIR
DEV=binance_config.DEV
DEFAULT_COIN_ICON = binance_config.DEFAULT_COIN_ICON
APP_ICON = binance_config.APP_ICON
SCRIPTS_DIR = binance_config.SCRIPTS_DIR
'''
MY_TRADES=my_trades.MY_TRADES

GREEN_TEXT = 'MediumSeaGreen'
RED_TEXT = 'IndianRed'
YELLOW_TEXT = 'GoldenRod'
ORANGE_TEXT = 'Chocolate'



INFO_LABELS_STYLE ="""
      font-weight: bold;
      color: {};
""".format(ORANGE_TEXT)

BUY_BUTTON = '''
    background-color: IndianRed;
    border-style: outset;
    border-width: 2px;
    border-radius: 0px;
    border-color: gray;
    font: bold 14px;
    min-width: 10em;
    padding: 6px;
'''

SELL_BUTTON = '''
    background-color: MediumSeaGreen;
    border-style: outset;
    border-width: 2px;
    border-radius: 0px;
    border-color: gray;
    font: bold 14px;
    min-width: 10em;
    padding: 6px;
'''

CONSOLE_STYLE = '''
    background-color: #202020;
    color: LightGreen;
    font-family: Fixedsys;
    font-style: normal;
    font-size: 8;
    border-width: 0px;
'''

INTRO_TEXT = """
################################################################################################################

Helllloo there!

This app is made as a fun project to integrate AI with crytocurrency charts. 
Type in premade commands or python file names to execute in this window.

COMMAND LIST
help   : shows this text
decide : gives you a list of items you should buy or sell (binance_005.py)

Alican Sesli 2021

################################################################################################################
"""

LEFT_ARROW  = 'icons\\left.png'
RIGHT_ARROW = 'icons\\right.png'

'''
client = Client(API_KEY, SECRET_KEY)
tickers = client.get_ticker()
print(tickers)
exchange_info = client.get_exchange_info().get('symbols')
#print(exchange_info)
symbols = list(set([i.get('baseAsset') for i in exchange_info]))
'''
'''
btc_price = {'error':False}
def btc_trade_history(msg):
      # define how to process incoming WebSocket messages 
      if msg['e'] != 'error':
            print(msg['c'])
            btc_price['last'] = msg['c']
            btc_price['bid'] = msg['b']
            btc_price['last'] = msg['a']
            btc_price['error'] = False
      else:
            btc_price['error'] = True

# init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()
# subscribe to a stream
bsm.start_symbol_ticker_socket(callback=btc_trade_history, symbol='BTCUSDT')
bsm.start_symbol_ticker_socket(callback=btc_trade_history, symbol='ETHUSDT')
'''
class QClickableLabel(QtWidgets.QLabel):
    def __init(self, parent):
        super().__init__(parent)

    clicked = QtCore.pyqtSignal()
    rightClicked = QtCore.pyqtSignal()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit()
        else:
            self.clicked.emit()

class AlicansApp(QtWidgets.QWidget):

      def __init__(self):
            super(AlicansApp, self).__init__()


            self.client = Client(API_KEY, SECRET_KEY)
            self.exchange_info = self.client.get_exchange_info().get('symbols')
            self.all_trade_symbols = sorted(list(set([i.get('symbol') for i in self.exchange_info if i.get('status') == 'TRADING' and i.get('isSpotTradingAllowed')])))
            self.symbols = sorted(list(set([i.get('baseAsset') for i in self.exchange_info if i.get('status') == 'TRADING' and i.get('isSpotTradingAllowed')])))
            self.current_trade_symbol = None
            self.current_trade_item = None
            self.current_coin_info = None
            self.tickers = None
            self.all_coins_info = self.client.get_all_coins_info()
            self.fees = self.client.get_trade_fee()
            self.browser = QWebEngineView()
            current_dir = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(current_dir, "render.html")
            self.kline_html = filename
            url = QtCore.QUrl.fromLocalFile(self.kline_html)
            self.browser.setUrl(url)
            self._console = QtWidgets.QTextBrowser()

            self._console_input = QtWidgets.QLineEdit()
            self._console_input.returnPressed.connect(self.execute_in_console)
            self._console_input.setPlaceholderText('Enter a command...')
            if SCRIPTS_DIR:
                  self.script_files = os.listdir(SCRIPTS_DIR)
            else:
                  self.script_files = os.listdir()

            if len(self.script_files):
                  self.script_files = [i for i in self.script_files if i.endswith('.py')]
            #print (self.fees)
            #self.balance = self.client.get_asset_balance(asset='BTC')
            #self.initUI()
            completer = QtWidgets.QCompleter(self.script_files)

            completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            #def initUI(self):

            command_completer = QtWidgets.QCompleter(self.script_files)
            command_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self._console_input.setCompleter(command_completer)


            #trade_icon_path = SMALL_ICONS_DIR+'btc.png'
            trade_icon_path = DEFAULT_COIN_ICON
            self.trade_icon = QtGui.QPixmap(trade_icon_path)
            self.current_coin_icon = QtWidgets.QLabel()
            self.current_coin_icon.setPixmap(self.trade_icon)
            #self.mainInfoLayout.addWidget(self.current_coin_icon,0,8)




            self.buy_layout = QtWidgets.QVBoxLayout()

            self.order_layout = QtWidgets.QHBoxLayout()
            self.order_buysell_type = QtWidgets.QComboBox()
            self.order_buysell_type.addItems(['BUY', 'SELL'])
            self.order_buysell_type.currentIndexChanged.connect(self.update_buy_sell_layout)
            self.order_layout.addWidget(self.order_buysell_type)
            self.order_type = QtWidgets.QComboBox()
            self.order_type.addItems(['Market', 'Limit'])
            self.order_layout.addWidget(self.order_type)

            self.order_title_layout = QtWidgets.QHBoxLayout()
            self.order_title = QtWidgets.QLabel('Buy BTC')
            self.order_title_layout.addWidget(self.order_title)
            self.order_title_layout.addWidget( QtWidgets.QLabel('Avbl') )
            self.available_funds_for_order = QtWidgets.QLabel('0.000023471')
            self.available_funds_currency = QtWidgets.QLabel('BTC')
            self.order_title_layout.addWidget( self.available_funds_for_order )
            self.order_title_layout.addWidget( self.available_funds_currency )

            self.coin_price_layout = QtWidgets.QHBoxLayout()
            self.coin_price_layout.addWidget(QtWidgets.QLabel("Price      "))
            self.coin_price = QtWidgets.QLineEdit()
            self.coin_price_layout.addWidget(self.coin_price)
            self.coin_price_currency = QtWidgets.QLabel("USDT")
            self.coin_price_layout.addWidget(self.coin_price_currency)
            
            self.buysell_amount_layout = QtWidgets.QHBoxLayout()
            self.buysell_amount_layout.addWidget(QtWidgets.QLabel("Amount "))
            self.buysell_amount = QtWidgets.QLineEdit()
            self.buysell_amount_layout.addWidget(self.buysell_amount)
            self.buysell_amount_currency = QtWidgets.QLabel("BTC")
            self.buysell_amount_layout.addWidget(self.buysell_amount_currency)

            self.total_cost_layout = QtWidgets.QHBoxLayout()
            self.total_cost_layout.addWidget(QtWidgets.QLabel("Total     "))
            self.total_cost= QtWidgets.QLineEdit()
            self.total_cost_layout.addWidget(self.total_cost)
            self.total_cost_currency = QtWidgets.QLabel("USDT")
            self.total_cost_layout.addWidget(self.total_cost_currency)
            self.total_cost = QtWidgets.QLineEdit()

            self.buy_sell_button = QtWidgets.QPushButton('Buy BTC')


            self.buy_sell_graphic_layout = QtWidgets.QHBoxLayout()


            trade_icon_path = DEFAULT_COIN_ICON

            baseAsset_graphic_pix  = QtGui.QPixmap(trade_icon_path)
            self.baseAsset_graphic = QClickableLabel()
            self.baseAsset_graphic.clicked.connect(self._iconPressedEvent)
            self.baseAsset_graphic.setPixmap(baseAsset_graphic_pix)
            self.baseAsset_graphic.setFixedHeight(35)


            self.baseAsset_graphic_label = QtWidgets.QLabel('YES')

            transfer_graphic_pix   = QtGui.QPixmap(trade_icon_path)
            self.transfer_graphic = QClickableLabel()
            self.transfer_graphic.clicked.connect(self.switch_trade_side)
            #self.transfer_graphic.rightClicked.connect(lambda: print('rightClicked'))
            self.transfer_graphic.setPixmap(transfer_graphic_pix)
            self.transfer_graphic.setFixedHeight(35)


            
            self.quoteAsset_graphic_label = QtWidgets.QLabel('NO')

            quoteAsset_graphic_pix = QtGui.QPixmap(trade_icon_path)
            self.quoteAsset_graphic = QClickableLabel()
            self.quoteAsset_graphic.clicked.connect(self._iconPressedEvent)
            self.quoteAsset_graphic.setPixmap(quoteAsset_graphic_pix)
            self.quoteAsset_graphic.setFixedHeight(35)



            self.buy_sell_graphic_layout.addWidget(self.baseAsset_graphic)
            self.buy_sell_graphic_layout.addWidget(self.baseAsset_graphic_label)
            self.buy_sell_graphic_layout.addWidget(self.transfer_graphic)
            self.buy_sell_graphic_layout.addWidget(self.quoteAsset_graphic_label)
            self.buy_sell_graphic_layout.addWidget(self.quoteAsset_graphic)


            self.buy_layout.addLayout(self.order_layout)
            self.buy_layout.addLayout(self.order_title_layout)
            self.buy_layout.addLayout(self.coin_price_layout)
            self.buy_layout.addLayout(self.buysell_amount_layout)
            self.buy_layout.addLayout(self.total_cost_layout)
            self.buy_layout.addWidget(self.buy_sell_button)

            self.buy_layout.addLayout(self.buy_sell_graphic_layout)




            self.mainLayout = QtWidgets.QVBoxLayout()


            self.mainInfoContainerLayout = QtWidgets.QHBoxLayout()
            #self.mainInfoContainerLayout.addStretch()

            self.mainInfoLayout = QtWidgets.QGridLayout()

            #self.mainInfoLayout.addStretch(1)
            
           # self.mainInfoContainerLayout.setSpacing(0)

            self.mainInfoContainerLayout.addWidget(self.current_coin_icon)
            self.mainInfoContainerLayout.addLayout(self.mainInfoLayout)
            #self.mainInfoLayout.addStretch()
            #self.mainInfoContainerLayout
            #self.mainInfoContainerLayout.setContentsMargins(0,0,0,0)
            #self.mainInfoContainerLayout.addStretch()
            #self.mainInfoContainerLayout.setSpacing(0)
            self.mainInfoContainerLayout.setStretchFactor(self.mainInfoLayout,100)


            self.mainLayout.addLayout(self.mainInfoContainerLayout)

            
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
            #sep.setLineWidth(1)
            self.mainLayout.addWidget(sep)
            

            #self.mainLayout.addLayout(self.mainInfoLayout)


            self.mainHLayout = QtWidgets.QHBoxLayout()
            self.mainVLayout0 = QtWidgets.QVBoxLayout()
            self.mainVLayout1 = QtWidgets.QVBoxLayout()
            self.mainVLayout2 = QtWidgets.QVBoxLayout()
            self.mainHLayout.addLayout( self.mainVLayout0 )
            self.mainHLayout.addLayout( self.mainVLayout1 )
            self.mainHLayout.addLayout( self.mainVLayout2 )
            self.mainLayout.addLayout( self.mainHLayout )
            self.mainHLayout.setStretchFactor(self.mainVLayout0,20)
            self.mainHLayout.setStretchFactor(self.mainVLayout1,80)
            self.mainHLayout.setStretchFactor(self.mainVLayout2,20)

            self.setLayout(self.mainLayout)

            self.coin_exchange_label = QtWidgets.QLabel('COIN_TRADE')
            self.coin_exchange_label.setStyleSheet(INFO_LABELS_STYLE)
            self.coin_label = QtWidgets.QLabel('Bitcoin')

            self.coin_trade_price = QtWidgets.QLabel('TRADE PRICE')
            self.coin_trade_price.setStyleSheet(INFO_LABELS_STYLE)
            self.coin_currency_price = QtWidgets.QLabel('C$53,344.34')
            
            self.info_24h_change = QtWidgets.QLabel('PRICE_CHANGE PERCENTAGE%')
            self.info_24h_high = QtWidgets.QLabel('24H_HIGH')
            self.info_24h_low = QtWidgets.QLabel('24H_LOW')
            self.info_24h_volume_in = QtWidgets.QLabel('VOL_IN')
            self.info_24h_volume_out = QtWidgets.QLabel('VOL_OUT')


            self.mainInfoLayout.addWidget(self.coin_exchange_label,0,0)
            self.mainInfoLayout.addWidget(self.coin_label,1,0)

            self.mainInfoLayout.addWidget(self.coin_trade_price,0,1)
            self.mainInfoLayout.addWidget(self.coin_currency_price,1,1)

            label = QtWidgets.QLabel('24h Change')
            label.setStyleSheet(INFO_LABELS_STYLE)
            self.mainInfoLayout.addWidget(label,0,2)

            self.mainInfoLayout.addWidget(self.info_24h_change,1,2)

            label = QtWidgets.QLabel('24h High')
            label.setStyleSheet(INFO_LABELS_STYLE)
            self.mainInfoLayout.addWidget(label,0,3)
            self.mainInfoLayout.addWidget(self.info_24h_high,1,3)

            label = QtWidgets.QLabel('24h Low')
            label.setStyleSheet(INFO_LABELS_STYLE)
            self.mainInfoLayout.addWidget(label,0,4)
            self.mainInfoLayout.addWidget(self.info_24h_low,1,4)

            self.base_24h_volume_label = QtWidgets.QLabel('24h Volume(base)')
            self.base_24h_volume_label.setStyleSheet(INFO_LABELS_STYLE)
            self.mainInfoLayout.addWidget(self.base_24h_volume_label,0,5)
            self.mainInfoLayout.addWidget(self.info_24h_volume_in,1,5)

            self.quote_24h_volume_label = QtWidgets.QLabel('24h Volume(quote)')
            self.quote_24h_volume_label.setStyleSheet(INFO_LABELS_STYLE)
            self.mainInfoLayout.addWidget(self.quote_24h_volume_label,0,6)
            self.mainInfoLayout.addWidget(self.info_24h_volume_out,1,6)

            if DEV:
                  self.refreshButton = QtWidgets.QPushButton('Refresh')
                  self.refreshButton.clicked.connect(self.get_my_orders)#self._coinTradableTypeChangedCall)
                  self.mainInfoLayout.addWidget(self.refreshButton,1,7)

                  self.updateStyleButton = QtWidgets.QPushButton('Update Style')
                  self.updateStyleButton.clicked.connect(self.update_style)#self._coinTradableTypeChangedCall)
                  self.mainInfoLayout.addWidget(self.updateStyleButton,0,7)

            #trade_icon_path = SMALL_ICONS_DIR+'btc.png'
            #self.trade_icon = QtGui.QPixmap(trade_icon_path)
            #self.current_coin_icon = QtWidgets.QLabel()
            #self.current_coin_icon.setPixmap(self.trade_icon)
            #self.mainInfoLayout.addWidget(self.current_coin_icon,0,8)
            '''
            self.mainInfoLayout.setColumnStretch(0,1)
            self.mainInfoLayout.setColumnStretch(1,1)
            self.mainInfoLayout.setColumnStretch(2,1)
            self.mainInfoLayout.setColumnStretch(3,1)
            self.mainInfoLayout.setColumnStretch(4,1)
            self.mainInfoLayout.setColumnStretch(5,1)
            self.mainInfoLayout.setColumnStretch(6,1)
            self.mainInfoLayout.setColumnStretch(7,1)
            self.mainInfoLayout.setSpacing(0)
            '''
            #self.coin_change_percent_layout = QtWidgets.QVBoxLayout()
            #self.coin_change_percent_layout.addWidget(QtWidgets.QLabel('Past Orders'))
            #self.mainHLayout.addLayout(self.coin_change_percent_layout)

            #self.mainHLayout.addLayout(self.mainLayout)

            #self.past_orders_layout = QtWidgets.QVBoxLayout()
            #self.past_orders_layout.addWidget(QtWidgets.QLabel('Past Orders'))
            #self.mainLayout.addLayout(self.past_orders_layout)

            self.coin_change_percent_layout = QtWidgets.QVBoxLayout()
            self.coin_change_percent_layout.addWidget(QtWidgets.QLabel('Trade Price Updates (24h)'))
            self.coin_change_percent_history_table = QtWidgets.QTableWidget()
            self.coin_change_percent_history_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.coin_change_percent_history_table.verticalHeader().hide()

            self.coin_change_percent_history_table_filters_layout = QtWidgets.QHBoxLayout()
            self.sort_by_text_input     = QtWidgets.QLineEdit()
            self.sort_by_symbol_change  = QtWidgets.QRadioButton("Pair")
            self.sort_by_price_change   = QtWidgets.QRadioButton("Price")
            self.sort_by_percent_change = QtWidgets.QRadioButton("Change")
            self.abs_change = QtWidgets.QCheckBox('Abs')
            self.descending_change = QtWidgets.QCheckBox('Dsc')
            self.sort_by_percent_change.setChecked(True)
            self.abs_change.setChecked(True)
            self.descending_change.setChecked(True)
            self.coin_change_percent_history_table_filters_layout.addWidget(self.sort_by_text_input)
            #self.coin_change_percent_history_table_filters_layout.addWidget(self.sort_by_symbol_change)
            self.coin_change_percent_history_table_filters_layout.addWidget(self.sort_by_price_change)
            self.coin_change_percent_history_table_filters_layout.addWidget(self.sort_by_percent_change)
            self.coin_change_percent_history_table_filters_layout.addWidget(self.abs_change)
            self.coin_change_percent_history_table_filters_layout.addWidget(self.descending_change)
            '''
            self.coin_change_percent_history_table.setColumnCount(3)
            self.coin_change_percent_history_table.verticalHeader().hide()
            
            self.coin_change_percent_history_table.setHorizontalHeaderLabels(['Pair', 'Price', 'Change'])
            self.coin_change_percent_history_table.setRowCount(len(self.all_trade_symbols))
            self.coin_change_percent_history_table.setSortingEnabled(True)
            row=0
            for i in self.all_trade_symbols:
                  self.coin_change_percent_history_table.setItem(row,0,QtWidgets.QTableWidgetItem(i))
                  row+=1
            '''
            self.coin_change_percent_history_table.setAlternatingRowColors(True)
            #self.order_history_table.setHorizontalHeaders(['a','b','c'])
            self.coin_change_percent_layout.addLayout(self.coin_change_percent_history_table_filters_layout)
            self.coin_change_percent_layout.addWidget(self.coin_change_percent_history_table)
            self.mainVLayout2.addLayout(self.coin_change_percent_layout)


            self.my_coins_layout = QtWidgets.QVBoxLayout()
            self.my_coins_layout.addWidget(QtWidgets.QLabel('Owned Assets'))
            self.my_coins_table = QtWidgets.QTableWidget()
            self.my_coins_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            #self.my_coins_table.setColumnCount(3)
            self.my_coins_table.setAlternatingRowColors(True)
            self.my_coins_table.verticalHeader().hide()
            #self.my_coins_table.setHorizontalHeaderLabels(['Asset', 'Price', 'Change'])
            #self.order_history_table.setHorizontalHeaders(['a','b','c'])
            self.my_coins_layout.addWidget(self.my_coins_table)
            self.mainVLayout0.addLayout(self.my_coins_layout)

            '''
            self.btn = QtWidgets.QPushButton('Dialog', self)
            self.btn.move(20, 20)
            self.btn.clicked.connect(self.showDialog)
            self.le = QtWidgets.QLineEdit(self)
            self.le.move(130, 22)
            '''


            self.order_history_table = QtWidgets.QTableWidget()
            self.order_history_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            order_headers = ['Date', 'Pair', 'Type', 'Side', 'Average', 'Price', 'Executed', 'Amount', 'Total', 'Trigger Conditions', 'Status']
            self.order_history_table.setColumnCount(len(order_headers))
            self.order_history_table.setHorizontalHeaderLabels(order_headers)
            self.order_history_table.setAlternatingRowColors(True)



            self.preset_browser_filter_range = QtWidgets.QComboBox()
            self.preset_browser_filter_range.setLineEdit(QtWidgets.QLineEdit())
            self.preset_browser_filter_range.addItems(['1','7','30','90','180','365'])
            self.preset_browser_filter_range.setCurrentText('90')


            self.order_history_show_all = QtWidgets.QCheckBox('Show All Trade Types')
            self.order_history_show_all.setChecked(True)
            self.order_history_show_all.clicked.connect(self.get_my_orders)




            self.coin_type_layout = QtWidgets.QHBoxLayout()

            self.only_show_my_coins = QtWidgets.QCheckBox('Only Show Owned')
            self.only_show_my_coins.stateChanged.connect(self._onlyShowMyCoinsCall)
            #self.coin_type_layout.addWidget(self.only_show_my_coins)
            self.coin_type = QtWidgets.QComboBox()
            self.coin_type.addItems(self.symbols)
            self.coin_type.setLineEdit(QtWidgets.QLineEdit())
            self.coin_type.currentIndexChanged.connect(self._coinTypeChangedCall)
            self.coin_type_layout.addWidget(self.coin_type)
            self.coin_tradable_type = QtWidgets.QComboBox()
            self.coin_tradable_type.addItems([''])
            self.coin_tradable_type.setLineEdit(QtWidgets.QLineEdit())
            self.coin_tradable_type.currentIndexChanged.connect(self._coinTradableTypeChangedCall)
            self.coin_type_layout.addWidget(self.coin_tradable_type)
            self.coin_tradable_line_dropdown = QtWidgets.QComboBox()
            self.coin_tradable_line_dropdown.addItems(self.all_trade_symbols)
            self.coin_tradable_line = QtWidgets.QLineEdit()
            self.coin_tradable_line.setCompleter(completer)
            self.coin_tradable_line.textChanged.connect(self._coinTradableLineChanged)
            self.coin_tradable_line_dropdown.setLineEdit(self.coin_tradable_line)
            #self.coin_type_layout.addWidget(self.coin_tradable_line)
            self.coin_type_layout.addWidget(self.coin_tradable_line_dropdown)

            self.mainVLayout1.addLayout(self.coin_type_layout)



            

            self.mainVLayout1.addWidget(self.browser)


            self.browser_filters_layout = QtWidgets.QHBoxLayout()

            #self.preset_browser_filter_range = QtWidgets.QComboBox()
            #self.preset_browser_filter_range.setLineEdit(QtWidgets.QLineEdit())
            #self.preset_browser_filter_range.addItems([1,7,30,90,180,365])
            self.preset_browser_filter_range.currentIndexChanged.connect(self._browserFilterRangeChangedCall)
            #self.browser_filters_layout.addWidget(self.preset_browser_filter_range)

            #self.preset_browser_filter_tick_range = QtWidgets.QComboBox()
            #self.preset_browser_filter_tick_range.addItems([])
            #self.browser_filters_layout.addWidget(self.preset_browser_filter_tick_range)


            #self.filter_browser_line = QtWidgets.QLineEdit()
            #self.browser_filters_layout.addWidget(self.filter_browser_line)



            self.mainVLayout1.addLayout(self.browser_filters_layout)


            self.mainVLayout0.addLayout(self.buy_layout)



            self.order_history_layout = QtWidgets.QVBoxLayout()


            

            self.order_history_title_layout = QtWidgets.QHBoxLayout()
            self.order_history_title_layout.addWidget(QtWidgets.QLabel('Order History'))
            self.order_history_title_layout.addWidget(self.order_history_show_all)


            
            self.browser_filters_layout.addWidget(self.preset_browser_filter_range)


            #self.browser_radio_buttons = QtWidgets.QHBoxLayout()
            '''
            self.browser_30  = QtWidgets.QRadioButton("30")
            self.browser_90   = QtWidgets.QRadioButton("90")
            self.browser_90.setEnabled(True)
            self.browser_180 = QtWidgets.QRadioButton("180")
            self.browser_365 = QtWidgets.QRadioButton("365")
            self.browser_1000 = QtWidgets.QRadioButton("1000")

            self.order_history_title_layout.addWidget(self.browser_30)
            self.order_history_title_layout.addWidget(self.browser_90)
            self.order_history_title_layout.addWidget(self.browser_180)
            self.order_history_title_layout.addWidget(self.browser_365)
            self.order_history_title_layout.addWidget(self.browser_1000)
            '''


            self.order_history_layout.addLayout(self.order_history_title_layout)

            #self.order_history_table.setHorizontalHeaders(['a','b','c'])
            #self.order_history_table.hide()
            self.order_history_layout.addWidget(self.order_history_table)



            #self.mainVLayout1.addLayout(self.order_history_layout)




            self.console_layout = QtWidgets.QVBoxLayout()
            
            self.console_layout.addWidget(self._console)
            self.console_layout.addWidget(self._console_input)

            '''
            self.console_enter_button = QtWidgets.QPushButton('Execute')
            self.console_enter_button.clicked.connect(self.execute_in_console)
            self.console_layout.addWidget(self.console_enter_button)
            '''


            self.clear_console_button = QtWidgets.QPushButton('Clear')
            self.clear_console_button.clicked.connect(self._clearConsole)
            self.console_layout.addWidget(self.clear_console_button)

            #self.mainVLayout1.addLayout(self.console_layout)


            self.automate_layout = QtWidgets.QVBoxLayout()

            self.automate_grid_layout=QtWidgets.QGridLayout()
            self.automate_layout.addLayout(self.automate_grid_layout)

            a=QtWidgets.QPushButton('Make a csv from current trade (Machine)')
            b=QtWidgets.QPushButton('Make a csv from current trade (Human')
            c=QtWidgets.QPushButton('Convert csv into 10 parts')
            d=QtWidgets.QPushButton('Prepare parts for training')
            self.automate_grid_layout.addWidget(a,0,0)
            self.automate_grid_layout.addWidget(b,1,0)
            self.automate_grid_layout.addWidget(c,1,1)
            self.automate_grid_layout.addWidget(d,1,2)



            self.bottom_info_tabs = QtWidgets.QTabWidget()
            #self.bottom_info_tabs.setOrientation('west')
            self.tab1 = QtWidgets.QWidget()
            self.tab2 = QtWidgets.QWidget()
            self.tab3 = QtWidgets.QWidget()
            self.tab1.layout = QtWidgets.QVBoxLayout()
            self.tab2.layout = QtWidgets.QVBoxLayout()
            self.tab3.layout = QtWidgets.QVBoxLayout()
            self.tab1.layout.addLayout(self.order_history_layout)
            self.tab2.layout.addLayout(self.console_layout)
            self.tab3.layout.addLayout(self.automate_layout)
            self.bottom_info_tabs.addTab(self.tab1,"My Orders")
            self.bottom_info_tabs.addTab(self.tab2,"Console")
            self.bottom_info_tabs.addTab(self.tab3,"Automate")
            self.tab1.setLayout(self.tab1.layout)
            self.tab2.setLayout(self.tab2.layout)
            self.tab3.setLayout(self.tab3.layout)
            self.mainVLayout1.addWidget(self.bottom_info_tabs)
            #self.tab1.layout.setContentsMargins(0,0,0,0)
            #self.tab2.layout.setContentsMargins(0,0,0,0)


            #self.start_ticker_socket()
            #self._coinTypeChangedCall()
            #self.update_my_coins()


            #self.tableView.cellDoubleClicked.connect(self.expandShipments)
            self.coin_change_percent_history_table.cellDoubleClicked.connect(self._tradeChangeItemDoubleClickedCall)
            self.order_history_table.cellDoubleClicked.connect(self._orderHistoryItemDoubleClickedCall)
            self.my_coins_table.cellDoubleClicked.connect(self._myCoinsItemDoubleClickedCall)
            self.coin_change_percent_history_table.cellClicked.connect(self._tradeChangeItemDoubleClickedCall)
            self.order_history_table.cellClicked.connect(self._orderHistoryItemDoubleClickedCall)
            self.my_coins_table.cellClicked.connect(self._myCoinsItemDoubleClickedCall)
            #self.order_history_show_all.clicked.connect(self.get_my_orders)
            self._console.selectionChanged.connect(self._consoleDoubleClickedCall)

            self.coin_type.setCurrentText('BTC')
            self.coin_tradable_type.setCurrentText('USDT')
            self.coin_tradable_line_dropdown.setCurrentText('BTCUSDT')

            self.get_my_orders()
            #self.update_my_coins()#wont work until it reads from self.exchange_info or soemthing. s..

            self.setGeometry(300, 300, 450, 350)

            self.setWindowTitle("Alican's Crypto App")
            self.setWindowIcon(QtGui.QIcon(APP_ICON))


            #self.setStyleSheet(STYLE)
            self.update_style()

            XStream.stdout().messageWritten.connect( self._console.append )
            XStream.stderr().messageWritten.connect( self._console.append )

            self._console.setStyleSheet(CONSOLE_STYLE)
            self._console_input.setStyleSheet(CONSOLE_STYLE)



            #self.show()
            self.showMaximized()


            print('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')

      def _iconPressedEvent(self):
            sender = self.sender()
            print(sender.text())
            return

      def switch_trade_side(self):
            current = self.order_buysell_type.currentText()
            if current == 'BUY':
                  self.order_buysell_type.setCurrentText('SELL')
            else:
                  self.order_buysell_type.setCurrentText('BUY')
            return

      def _consoleDoubleClickedCall(self):
            #print(x)
            cursor = self._console.textCursor()
            s=cursor.selectionStart()
            e=cursor.selectionEnd()
            #print(s,e)
            selected_text = ''.join(self._console.toPlainText()[s:e])
            if selected_text.upper() in self.all_trade_symbols:
                  self.coin_tradable_line_dropdown.setCurrentText(selected_text.upper())

            #print (self.all_trade_symbols)
            #self.coin_tradable_line_dropdown.setCurrentText(selected_text)
            return


      def update_current_coin_icon(self,name='BTC'):
            #coin_name = self.coin_tradable_line_dropdown.currentText()
            '''
            if not name:
                  coin_name = [i.get('baseAsset') for i in self.exchange_info if i.get('symbol') == self.coin_tradable_line_dropdown.currentText()]
                  if not coin_name:
                        return
                  coin_name = coin_name[0].lower()
            else:
            '''
            trade_icon = QtGui.QPixmap( self.get_coin_icon_path(name) )
            self.current_coin_icon.setPixmap(trade_icon)
            return

      def get_coin_icon_path(self, coin):
            coin_name = coin.lower()
            trade_icon_path = SMALL_ICONS_DIR+coin_name+'.png'
            if not os.path.exists(trade_icon_path):
                  trade_icon_path = DEFAULT_COIN_ICON
            return trade_icon_path


      def get_kline_data(self):
            x=1000
            return

      def execute_in_console(self):
            input_str = self._console_input.text()
            self._console_input.setText('')
            #self.execute_functions(input_str)
            input_str = str(input_str)
            if input_str:

                  if input_str in ['hi','help']:
                        self.print_help()


                  elif input_str == 'decide':
                        self.start_process()

                  elif input_str.startswith('execute'):
                        self.execute_process(input_str)

                  elif input_str == 'get data':
                        self.print_kline_data()

                  elif input_str == 'test':
                        #self.test_proc()
                        self.startTheThread()


                  elif [i for i in self.script_files if input_str.split(' ')[0] == i]:#input_str in self.script_files:
                        self.execute_process(input_str)

                  else:
                        print (input_str, "I don't know what to do with this command..")

            return

      def _clearConsole(self):
            self._console.setText('')
            return

      def _browserFilterRangeChangedCall(self):
            #val = self.preset_browser_filter_range.currentText()
            self.create_kline_html([self.coin_tradable_line_dropdown.currentText()], days=self.preset_browser_filter_range.currentText())
            return

      def _tradeChangeItemDoubleClickedCall(self, row, column):
            column = 0
            item = self.coin_change_percent_history_table.item(row, column)
            #print(item.text())
            if item:
                  self.coin_tradable_line.setText(item.text())

      def _orderHistoryItemDoubleClickedCall(self, row, column):
            if column == 1:
                  item = self.order_history_table.item(row, column)
                  #print(item.text())
                  self.coin_tradable_line.setText(item.text())

      def _myCoinsItemDoubleClickedCall(self,row,column):
            item = self.my_coins_table.item(row, column)
            if column == 2:
                  
                  #print(item.text())
                  self.coin_tradable_line.setText(item.text())
            elif column == 0:
                  self.sort_by_text_input.setText(item.text())

      def update_style(self):
            css_file=STYLESHEET_FILE
            with open(css_file,"r") as f:
                self.setStyleSheet( f.read() )
            return

      def get_my_orders(self):

            #self.orders = self.client.get_all_orders(limit=1)

            self.orders = []
            
            if self.order_history_show_all.isChecked():
                  trade_symbol = None
                  for trade in MY_TRADES:
                        trade_list = self.client.get_all_orders(symbol=trade, limit=50)
                        if len(trade_list):
                              self.orders+=trade_list
            else:
                  trade_symbol = self.coin_tradable_line_dropdown.currentText()
                  trade_list = self.client.get_all_orders(symbol=trade_symbol, limit=50)
                  if len(trade_list):
                        self.orders+=trade_list

            '''
            if not trade_symbol:
                  for trade in MY_TRADES:
                        trade_list = self.client.get_all_orders(symbol=trade, limit=50)
                        if len(trade_list):
                              self.orders+=trade_list
            else:
                  trade_list = self.client.get_all_orders(symbol=trade_symbol, limit=50)
                  if len(trade_list):
                        self.orders+=trade_list
            '''

            self.order_history_table.clear()
            order_headers = ['Date', 'Pair', 'Type', 'Side', 'Average', 'Price', 'Executed', 'Amount', 'Total', 'Trigger Conditions', 'Status']
            self.order_history_table.setColumnCount(len(order_headers))
            self.order_history_table.setHorizontalHeaderLabels(order_headers)

            self.order_history_table.setRowCount(len(self.orders))



            row=0

            for i in self.orders:
                  #print (i,'###############################')
                  trade_date = str(datetime.fromtimestamp(int(i.get('time'))/1000))
                  self.order_history_table.setItem(row,0,QtWidgets.QTableWidgetItem( trade_date ))
                  s=QtWidgets.QTableWidgetItem( i.get('symbol') )
                  s.setForeground(QtGui.QColor(YELLOW_TEXT))
                  self.order_history_table.setItem(row,1,s)
                  self.order_history_table.setItem(row,2,QtWidgets.QTableWidgetItem( i.get('type') ))
                  self.order_history_table.setItem(row,3,QtWidgets.QTableWidgetItem( i.get('side') ))
                  self.order_history_table.setItem(row,4,QtWidgets.QTableWidgetItem( i.get('price') ))
                  self.order_history_table.setItem(row,5,QtWidgets.QTableWidgetItem( i.get('price') ))
                  self.order_history_table.setItem(row,6,QtWidgets.QTableWidgetItem( i.get('executedQty') ))
                  self.order_history_table.setItem(row,7,QtWidgets.QTableWidgetItem( i.get('origQty') ))
                  self.order_history_table.setItem(row,8,QtWidgets.QTableWidgetItem( i.get('cummulativeQuoteQty') ))
                  self.order_history_table.setItem(row,9,QtWidgets.QTableWidgetItem( '-' ))
                  self.order_history_table.setItem(row,10,QtWidgets.QTableWidgetItem( i.get('status') ))
                  row+=1

            return

      def update_buy_sell_layout(self):
            trade_symbol = self.coin_tradable_line_dropdown.currentText()
            trade_item = [i for i in self.exchange_info if i.get('symbol') == trade_symbol][0]


            #if self.order_type.currentText() == 'Market':
            #      self.



            baseAsset = trade_item.get('baseAsset')
            quoteAsset = trade_item.get('quoteAsset')
            #price = trade_item

            if self.current_coin_info == None:
                  return
            #if len(self.current_coin_info):
            #      self.coin_exchange_label.setText( self.current_coin_info.get('s') )
            #print (self.current_coin_info)

            self.coin_price_currency.setText(quoteAsset)
            self.buysell_amount_currency.setText(baseAsset)
            self.total_cost_currency.setText(quoteAsset)
            #

            latest_price = self.client.get_all_tickers()
            latest_price = [i.get('price') for i in latest_price if i.get('symbol') == trade_symbol][0]
            #latest_price.get('price')

            self.coin_price.setText(latest_price)
            

            if self.order_buysell_type.currentText()=='BUY':
                  arrow = LEFT_ARROW
                  self.buy_sell_button.setText('Buy '+baseAsset)
                  self.buy_sell_button.setStyleSheet(BUY_BUTTON)
                  self.order_title.setText('Buy '+baseAsset)
                  #self.available_funds_for_order
                  self.available_funds_currency.setText(quoteAsset)

                  avail_price = [i.get('free') for i in self.get_my_coins() if i.get('asset') == quoteAsset]
                  if len(avail_price):
                        avail_price = avail_price[0]
                  else:
                        avail_price = 0.0000

                  self.available_funds_for_order.setText( str(avail_price) )



            else:
                  arrow = RIGHT_ARROW
                  self.buy_sell_button.setText('Sell '+baseAsset)
                  self.buy_sell_button.setStyleSheet(SELL_BUTTON)
                  self.order_title.setText('Sell '+baseAsset)
                  self.available_funds_currency.setText(baseAsset)

                  avail_price = [i.get('free') for i in self.get_my_coins() if i.get('asset') == baseAsset]
                  if len(avail_price):
                        avail_price = avail_price[0]
                  else:
                        avail_price = 0.0000
                  avail_price = str(avail_price)
                  self.available_funds_for_order.setText( avail_price )


            
            self.baseAsset_graphic_label.setText( baseAsset )
            self.baseAsset_graphic.setText( baseAsset )
            self.baseAsset_graphic.setPixmap(  QtGui.QPixmap( self.get_coin_icon_path(baseAsset) ) )
            self.transfer_graphic.setPixmap(   QtGui.QPixmap( arrow ) )
            self.quoteAsset_graphic_label.setText( quoteAsset )
            self.quoteAsset_graphic.setText( quoteAsset )
            self.quoteAsset_graphic.setPixmap( QtGui.QPixmap( self.get_coin_icon_path(quoteAsset) ) )

            return

      def _onlyShowMyCoinsCall(self):

            self.coin_type.clear()
            if self.only_show_my_coins.isChecked():
                  symbols = [i.get('asset') for i in self.get_my_coins()]
                  self.coin_type.addItems(symbols)
            else:
                  self.coin_type.addItems(self.symbols)
            return

      def _coinTypeChangedCall(self):
            current_symbol = self.coin_type.currentText()

            trade_symbols = []
            for i in self.exchange_info:

                  if i.get('status') == 'TRADING' and i.get('isSpotTradingAllowed'):
                        baseAsset = i.get('baseAsset')
                        quoteAsset = i.get('quoteAsset')

                        if current_symbol == baseAsset or current_symbol == quoteAsset:

                              if current_symbol == baseAsset:
                                    trade_symbols.append( quoteAsset )
                              elif current_symbol == quoteAsset:
                                    trade_symbols.append( baseAsset )
            trade_symbols = sorted(list(set(trade_symbols)))

            self.coin_tradable_type.clear()
            self.coin_tradable_type.addItems(trade_symbols)
            return


      def _coinTradableTypeChangedCall(self):
            self.current_trade_item = self.coin_tradable_type.currentText()
            current_coin = self.coin_type.currentText()
            trade_item = []
            for i in self.exchange_info:
                  if i.get('quoteAsset') in [self.current_trade_item,current_coin] and i.get('baseAsset') in [self.current_trade_item,current_coin] and (len(i.get('symbol')) == len(self.current_trade_item)+len(current_coin)):
                        trade_item.append(i)
                        break


            if len(trade_item):
                  trade_item = trade_item[0] 
                  self.coin_tradable_line_dropdown.setCurrentText( trade_item.get('symbol') )

                  return

      def _coinTradableLineChanged(self):
            q = self.coin_tradable_type.currentText()
            b = self.coin_type.currentText()

            t = []
            t = [i for i in self.exchange_info if i.get('symbol') == self.coin_tradable_line_dropdown.currentText()]
            if len(t):
                  t=t[0]
            else:
                  return

            if not ((self.coin_type.currentText() == t.get('baseAsset') and self.coin_tradable_type.currentText() == t.get('quoteAsset')) or (self.coin_tradable_type.currentText() == t.get('baseAsset') and self.coin_type.currentText() == t.get('quoteAsset'))):
                  if self.coin_type.currentText() == t.get('baseAsset'):
                        self.coin_tradable_type.setCurrentText(t.get('quoteAsset'))

                  elif self.coin_type.currentText() == t.get('quoteAsset'):
                        self.coin_tradable_type.setCurrentText(t.get('baseAsset'))

                  elif self.coin_tradable_type.currentText() == t.get('baseAsset'):
                        self.coin_type.setCurrentText(t.get('quoteAsset'))

                  elif self.coin_tradable_type.currentText() == t.get('quoteAsset'):
                        self.coin_type.setCurrentText(t.get('baseAsset'))

                  else:
                        self.coin_type.setCurrentText(t.get('baseAsset'))
                        self.coin_tradable_type.setCurrentText(t.get('quoteAsset'))
            else:
                  #self.coin_type.setCurrentText(t.get('baseAsset'))
                  #self.coin_tradable_type.setCurrentText(t.get('quoteAsset'))
                  pass



            #self.create_kline_html(t.get('symbol'))
            #self.coin_tradable_line
            self.create_kline_html([self.coin_tradable_line_dropdown.currentText()], days=self.preset_browser_filter_range.currentText())


            #self.current_trade_item.setCurrentText(t.get('baseAsset'))
            #self.coin_type.setCurrentText(t.get('quoteAsset'))


            #x = [i.get('baseAsset') for i in self.exchange_info if i.get('symbol') == self.current_coin_info.get('s')]

      def refreshBrowser(self):

            self.browser.load (QtCore.QUrl.fromLocalFile (self.kline_html))


      #def create_kline_csv(self)

      def create_kline_html(self, titles, days=90):
            #print(title)
            days = int(days)
            last_x_days=days
            

            if len(titles) ==1:
                  title=titles[0]#BRGBTC
                  aux = ['BTC', 'USDT', 'ETH', 'BNB']
                  baseAsset = [i.get('baseAsset') for i in self.exchange_info if i.get('symbol') == title][0]#BRG
                  aux_trades = [i.get('symbol') for i in self.exchange_info if i.get('baseAsset') == baseAsset and i.get('quoteAsset') in aux]#BRGBTC,BRGUSDT..
                  for a in aux_trades:
                        if a != title:
                              titles.append(a)
                  #titles += aux_trades

                  #titles.append('BTCUSDT')

            kline = Kline(width=1300,height=440,title=', '.join(titles),subtitle='Coin Data')
            for title in titles:
                  kline_list = self.get_trade_klines_list(title, last_x_days=last_x_days)
                  #print (kline_list)

                  
                  #print(dir(kline))

                  #kline.add(title, ["2017/7/{}".format(i + 1) for i in range(last_x_days)], kline_list)
                  kline.add(title, ["{}".format(i + 1) for i in range(last_x_days)], kline_list, is_datazoom_show=True,mark_line=["average"], mark_point=["max", "min"], is_more_utils=True,is_toolbox_show=True,is_stack=False, is_symbol_show=False)
                  #kline.set_global_opts(title_opts=opts.TitleOpts(title="Top cloud providers 2018", subtitle="2017-2018 Revenue"))
                  #kline.show_config()
            kline.render()
            self.refreshBrowser()
            if not self.order_history_show_all.isChecked():
                  self.get_my_orders()


            self.update_my_coins()
            self.update_buy_sell_layout()

      #no
      def update_current_coin_trade_info(self, msg):
            #print(msg)
            current_tradable = self.coin_tradable_type.currentText()
            current_coin = self.coin_type.currentText()
            trade_item = [i for i in msg if (current_tradable in i.get('s') and current_coin in i.get('s'))]
            if len(trade_item):
                  trade_item = trade_item[0] 



            t = [i for i in msg if i.get('s') == trade_item.get('s')]
            if len(t):
                  t=t[0]
            self.current_coin_info = t
            #print (t)
            self.updateInfoBar()

      def update_tickers(self,msg):

            self.tickers = msg
            self.update_coins()
            #print(msg)
            return

      def start_ticker_socket(self):
            #symbol = 'BTCUSDT'
            twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=SECRET_KEY)
            # start is required to initialise its internal loop
            twm.start()
            twm.start_ticker_socket(callback=self.update_tickers)
            twm.join()
            return


      def update_my_coins(self):
            my_coins = self.get_my_coins()
            #print (my_coins)



            self.my_coins_table.clear()
            self.my_coins_table.setRowCount(len(my_coins))
            self.my_coins_table.setColumnCount(3)
            self.my_coins_table.setHorizontalHeaderLabels(['Asset', 'Qty', 'Price (BTC)'])
            self.my_coins_table.setAlternatingRowColors(True)
            row=0
            try:
                  btc_coins = [i for i in self.tickers if 'BTC' in i.get('s')]
            except:
                  return

            for coin in my_coins:
                  btc_trade = None
                  symbol = coin.get('asset')
                  for i in btc_coins:
                        if 'BTC' in i.get('s') and coin.get('asset') in i.get('s') and len(i.get('s'))==len(coin.get('asset'))+len('BTC'):
                              #print (coin.get('asset'),i)
                              btc_trade = i
                              break

                  #if symbol in [self.coin_type.currentText() , self.coin_tradable_type.currentText() ]
                  #print(symbol)
                  #if symbol == self.coin_tradable_type.currentText():
                  #      self.current_coin_info = t
                  
                  #asset_icon_path = self.get_coin_icon_path(coin.get('asset'))
                  #print (asset_icon_path)
                  #icon = QtGui.QPixmap(asset_icon_path)
                  icon = QtGui.QIcon( self.get_coin_icon_path(coin.get('asset')) )
                  icon_item = QtWidgets.QTableWidgetItem(coin.get('asset'))
                  icon_item.setIcon(icon)
                  self.my_coins_table.setItem(row,0,icon_item)
                  #self.my_coins_table.setItem(row,0,QtWidgets.QTableWidgetItem(coin.get('asset')))
                  self.my_coins_table.setItem(row,1,QtWidgets.QTableWidgetItem(coin.get('free')))
                  if btc_trade:
                        s=QtWidgets.QTableWidgetItem(btc_trade.get('s'))
                        s.setForeground(QtGui.QColor(YELLOW_TEXT))
                        self.my_coins_table.setItem(row,2,s)
                  row+=1

            return


      def update_coins(self):

            if self.tickers == None:
                  return

            descending = True
            absolute  = True
            order_by = 'P'

            if self.sort_by_symbol_change.isChecked():
                  order_by = 's'
            elif self.sort_by_price_change.isChecked():
                  order_by = 'c'
            elif self.sort_by_percent_change.isChecked():
                  order_by = 'P'
            absolute = self.abs_change.isChecked()
            descending = self.descending_change.isChecked()

            f=self.sort_by_text_input.text().upper()
            if order_by == 's':
                  self.tickers = sorted([t for t in self.tickers if t.get('s') in self.all_trade_symbols and f in t.get('s')], key=lambda t: t[order_by], reverse=descending)
            elif absolute:
                  self.tickers = sorted([t for t in self.tickers if t.get('s') in self.all_trade_symbols and f in t.get('s')], key=lambda t: abs(float(t[order_by])), reverse=descending)
            else:
                  self.tickers = sorted([t for t in self.tickers if t.get('s') in self.all_trade_symbols and f in t.get('s')], key=lambda t: float(t[order_by]), reverse=descending)


            self.coin_change_percent_history_table.clear()
            self.coin_change_percent_history_table.setRowCount(len(self.tickers))
            self.coin_change_percent_history_table.setColumnCount(3)
            self.coin_change_percent_history_table.setHorizontalHeaderLabels(['Pair', 'Price', 'Change'])
            #self.coin_change_percent_history_table.setAlternatingRowColors(True)
            #self.coin_change_percent_history_table.setSortingEnabled(True)
            
            row=0
            #print(self.tickers)
            #return
            #row_cnt = self.coin_change_percent_history_table.rowCount()
            #print (ordered)

            for t in self.tickers:
                  symbol = t['s']
                  #print(symbol, self.coin_tradable_type.currentText() ,self.coin_type.currentText())
                  #print(symbol)
                  #if self.coin_tradable_type.currentText() in symbol  and self.coin_type.currentText() in symbol and len(symbol)==len(self.coin_type.currentText())+len(self.coin_tradable_type.currentText()):
                  #if self.coin_tradable_line.text() == symbol:
                  if self.coin_tradable_line_dropdown.currentText() == symbol:
                        self.current_coin_info = t

                  table_item1=QtWidgets.QTableWidgetItem(symbol)
                  table_item2=QtWidgets.QTableWidgetItem()
                  table_item2.setData(QtCore.Qt.DisplayRole, t['c'])
                  table_item3=QtWidgets.QTableWidgetItem()
                  table_item3.setData(QtCore.Qt.DisplayRole, t['P'])

                  if '-' in t['P']:
                        #table_item1.setForeground(QtGui.QColor("red"))
                        table_item2.setForeground(QtGui.QColor(RED_TEXT))
                        table_item3.setForeground(QtGui.QColor(RED_TEXT))

                  else:
                        #table_item1.setForeground(QtGui.QColor("green"))
                        table_item2.setForeground(QtGui.QColor(GREEN_TEXT))
                        table_item3.setForeground(QtGui.QColor(GREEN_TEXT))

                  self.coin_change_percent_history_table.setItem(row,0,table_item1)
                  self.coin_change_percent_history_table.setItem(row,1,table_item2)
                  self.coin_change_percent_history_table.setItem(row,2,table_item3)

                  row+=1
            
            self.updateInfoBar()
            return



      def updateInfoBar(self):
            #self.current_trade_item 

            if self.current_coin_info == None:
                  return
            #print (self.current_coin_info)
            current_tradable = self.coin_tradable_type.currentText()
            if current_tradable =='':
                  return
            coin_symbol = self.coin_type.currentText()

            if current_tradable.startswith( coin_symbol ):
                  coin_exchange_text = current_tradable.replace(coin_symbol, coin_symbol+'/')

            elif current_tradable.endswith( coin_symbol ):
                  coin_exchange_text = current_tradable.replace(coin_symbol, '/'+coin_symbol)

            #print (self.current_coin_info)
            if len(self.current_coin_info):
                  self.coin_exchange_label.setText( self.current_coin_info.get('s') )
                  x = [i for i in self.exchange_info if i.get('symbol') == self.current_coin_info.get('s')]
                  if x:
                        x=x[0]
                  name = ''
                  baseAsset=''
                  quoteAsset=''
                  for i in self.all_coins_info:
                        if i.get('coin') == x.get('baseAsset'):
                              name = i.get('name')
                              baseAsset=x.get('baseAsset')
                              quoteAsset=x.get('quoteAsset')
                  self.base_24h_volume_label.setText('24h Volume ({})'.format(baseAsset))
                  self.quote_24h_volume_label.setText('24h Volume ({})'.format(quoteAsset))
                  self.update_current_coin_icon(name=x.get('baseAsset'))

                  #self.coin_label = QtWidgets.QLabel('----?')#??
                  self.coin_label.setText( name )
                  #self.coin_trade_price.setText(str(self.get_coin_price( current_tradable )))
                  self.coin_trade_price.setText( '{} ({})'.format(self.current_coin_info.get('c'), quoteAsset))
                  self.coin_currency_price.setText('------------')
                  
                  self.info_24h_change.setText('{} {}%'.format( self.current_coin_info.get('p'), self.current_coin_info.get('P') ))
                  if '-' in self.current_coin_info.get('P'):
                        self.info_24h_change.setStyleSheet("color: "+GREEN_TEXT)
                  else:
                        self.info_24h_change.setStyleSheet("color: "+GREEN_TEXT)

                  self.info_24h_high.setText(self.current_coin_info.get('h'))
                  self.info_24h_low.setText(self.current_coin_info.get('l'))
                  self.info_24h_volume_in.setText(self.current_coin_info.get('v'))
                  self.info_24h_volume_out.setText(self.current_coin_info.get('q'))
            

            return


      def get_my_coins(self):
            #Returns a list of coin types(dicts): [{'asset': 'BTC', 'free': '0.00028971', 'locked': '0.00000000'},..]
            coins_in_accounts = self.client.get_account().get('balances')
            coins_in_accounts = [i for i in coins_in_accounts if (float(i.get('free')) != 0.0 or float(i.get('locked')) != 0.0) ]
            return coins_in_accounts

      def get_trade_klines(self, coin_trade_str, last_x_days=3):
            coin_klines = []
            try:
                  klines = self.client.get_historical_klines(coin_trade_str, Client.KLINE_INTERVAL_1DAY, "24 hours ago")
            except:
                  return []
            #print(len(klines))
            
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
                  #     price_change_percent*=-1

                  price_change_percent = round(close_price * 100 / open_price - 100, 2)

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
                        'price_change_percent' : price_change_percent
                  }
                  #print(kline_dict)
                  coin_klines.append(kline_dict)
            #print(coin_klines)
            return coin_klines


      def get_trade_klines_list(self, coin_trade_str, last_x_days=30):
            coin_klines = []
            kline_lists = []
            try:
                  klines = self.client.get_historical_klines(coin_trade_str, Client.KLINE_INTERVAL_1DAY, "{} days ago".format(last_x_days))
            except:
                  return []
            #print(len(klines))
            
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
                  #     price_change_percent*=-1

                  price_change_percent = round(close_price * 100 / open_price - 100, 2)

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
                        'price_change_percent' : price_change_percent
                  }

                  kline_list = [kline[1],kline[4],kline[3],kline[2]]
                  kline_lists.append( kline_list )
                  #print(kline_dict)
                  coin_klines.append( kline_dict )
            #print(coin_klines)
            return kline_lists


      def get_trade_klines_list(self, coin_trade_str, last_x_days=30, fulldata=False,interval=Client.KLINE_INTERVAL_1DAY):
            coin_klines = []
            kline_lists = []
            try:
                  klines = self.client.get_historical_klines(coin_trade_str, interval, "{} days ago".format(last_x_days))
            except:
                  return []
            #print(len(klines))
            
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
                  #     price_change_percent*=-1

                  price_change_percent = round(close_price * 100 / open_price - 100, 2)

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
                        'price_change_percent' : price_change_percent
                  }

                  kline_list = [kline[1],kline[4],kline[3],kline[2]]
                  kline_lists.append( kline_list )
                  #print(kline_dict)
                  coin_klines.append( kline_dict )
            #print(coin_klines)
            if fulldata:
                  return coin_klines
            return kline_lists



      def process_trade(self,coin, price_change_list):
            #detect wether to buy,sell or wait based on price_change_list data.  
            current_coin = self.get_coin_info(coin)
            #change_percent = get_coin_price_change_percent(coin)
            coin_price = self.get_coin_price(coin)
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
            min_price    = float(price_filter.get('minPrice'))
            max_price    = float(price_filter.get('maxPrice'))
            tick_size    = float(price_filter.get('tickSize'))

            min_qty      = float(lot_size_filter.get('minQty'))
            max_qty      = float(lot_size_filter.get('maxQty'))
            step_size    = float(lot_size_filter.get('stepSize'))

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

            #
            #print('\t<<< {} price: {} 24hr % change:{} 3 day % change: {} >>>'.format(coin,coin_price,change_percent,price_change_list))
            #

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
                  result = self.buy_coin(coin, buy_quantity)

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
                  result = self.sell_coin(coin, buy_quantity)

                  return result

            else:
                  #print('\t<<<{} : {} >>>'.format(action, coin))
                  return



      def buy_coin(self,coin, buy_quantity):

            return

      def sell_coin(self,coin, buy_quantity):

            return

      def get_coin_info(self, coin_trade_str):
            exchange_info = self.client.get_exchange_info().get('symbols')
            return [i for i in exchange_info if i.get('symbol') == coin_trade_str][0]


      def get_coin_price(self, coin_trade_str):
            tickers = self.client.get_all_tickers()
            coin_price = [i for i in tickers if i.get('symbol') == coin_trade_str]
            if len(coin_price):
                  coin_price=coin_price[0]
                  coin_price_str = coin_price.get('price')
                  coin_price_float = float(coin_price_str)
                  return coin_price_float
            else:
                  return 0.0


      def showDialog(self):
            text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                        'Enter your name:')

            if ok:
                  self.le.setText(str(text))


      @QtCore.pyqtSlot(str)
      def append_output(self, text):
            self._console.append(text)
            #self.scroll_to_last_line()
      def start_process(self):
            #self.message("Executing process.")
            #self.p = QtCore.QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            #self.p.start("python3", ['test.py'])
            #self.p.produce_output.connect(self._console.insertPlainText)
            #self.p.start('python3', ['-u', 'test.py'])

            self.reader = ProcessOutputReader()
            self.reader.produce_output.connect(self.append_output)
            self.reader.start('python3', ['-u', 'binance_005.py'])  # start the process

      def execute_process(self, input_str):
            #self.message("Executing process.")
            #self.p = QtCore.QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            #self.p.start("python3", ['test.py'])
            #self.p.produce_output.connect(self._console.insertPlainText)
            #self.p.start('python3', ['-u', 'test.py'])
            inputs = input_str.split(' ')
            file_name = inputs[0]
            if len(inputs) ==1:
                  inputs.append(self.coin_tradable_line_dropdown.currentText())
            self.execute_proc = ProcessOutputReader()
            self.execute_proc.produce_output.connect(self.append_output)
            #self.execute_proc.start('python3', ['-u', '{}'.format(file_name)])  # start the process
            self.execute_proc.start('python3', ['-u']+inputs)  # start the process



      def print_help(self):
            self._console.append(INTRO_TEXT)
            return


      def test_proc1(self):
            i=0
            while i<10:
                  print(i)
                  time.sleep(1)
                  i+=1


      def test_proc(self):
            #self.message("Executing process.")
            self.p = QtCore.QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.start(self.test_proc1)
            self.p.produce_output.connect(self._console.insertPlainText)
            #self.p.start('python3', ['-u', 'test.py'])

      def theCallbackFunc(self, msg):
            print('the thread has sent this message to the GUI:')
            print(msg)
            print('---------')
            self.test_proc1()


      def startTheThread(self):
            # Create the new thread. The target function is 'myThread'. The
            # function we created in the beginning.
            t = threading.Thread(name = 'myThread', target = myThread, args = (self.theCallbackFunc))
            t.start()

def test_proc():
      i=0
      while i<10:
            print(i)
            time.sleep(1)
            i+=1
# Create the class 'Communicate'. The instance
# from this class shall be used later on for the
# signal/slot mechanism.

class Communicate(QtCore.QObject):
      myGUI_signal = QtCore.pyqtSignal(str)

''' End class '''


# Define the function 'myThread'. This function is the so-called
# 'target function' when you create and start your new Thread.
# In other words, this is the function that will run in your new thread.
# 'myThread' expects one argument: the callback function name. That should
# be a function inside your GUI.

def myThread(callbackFunc):
      # Setup the signal-slot mechanism.
      mySrc = Communicate()
      mySrc.myGUI_signal.connect(callbackFunc) 

      # Endless loop. You typically want the thread
      # to run forever.
      while(True):
            # Do something useful here.
            msgForGui = 'This is a message to send to the GUI'
            mySrc.myGUI_signal.emit(msgForGui)
            # So now the 'callbackFunc' is called, and is fed with 'msgForGui'
            # as parameter. That is what you want. You just sent a message to
            # your GUI application! - Note: I suppose here that 'callbackFunc'
            # is one of the functions in your GUI.
            # This procedure is thread safe.

      ''' End while '''

''' End myThread '''

def main():


      app = QtWidgets.QApplication(sys.argv)

      ex = AlicansApp()

      twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=SECRET_KEY)
      # start is required to initialise its internal loop
      twm.start()

      def handle_socket_message(msg):
            #try:
            #    print(f"message type: {msg['e']}")
            #except KeyError:
            #    pass
            ex.update_tickers(msg)
            #print(msg)

      def handle_socket_message2(msg):
            ex.update_current_coin_trade_info(msg)

      #twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

      twm.start_ticker_socket(callback=handle_socket_message)
      #twm.start_miniticker_socket(callback=handle_socket_message2)

      # multiple sockets can be started
      #twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

      # or a multiplex socket can be started like this
      # see Binance docs for stream names
      streams = ['btcusdt@miniTicker']#, 'btcusdt@bookTicker']
      #twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

      
      ex.show()

      sys.exit(app.exec_())

      twm.join()


def do():
      
      reader = ProcessOutputReader()
      reader.produce_output.connect(ex.append_output)
      reader.start('python3', ['-u', 'test.py'])  # start the process



if __name__ == '__main__':
      main()
