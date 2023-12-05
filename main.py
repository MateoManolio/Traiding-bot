import datetime
import os
import sys
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ("sma1_period", 50),
        ("sma2_period", 200),
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("bb_period", 20),
        ("bb_dev", 2),
        ("hammer_pattern", True),
        ("shooting_star_pattern", True),
    )

    def __init__(self):
        # Indicadores
        self.sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma1_period)
        self.sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma2_period)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        self.bbands = bt.indicators.BollingerBands(self.data.close, period=self.params.bb_period, devfactor=self.params.bb_dev)
        self.hammer = bt.talib.CDLHAMMER(self.data.open, self.data.high, self.data.low, self.data.close)
        self.shooting_star = bt.talib.CDLSHOOTINGSTAR(self.data.open, self.data.high, self.data.low, self.data.close)

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime[0]
        dt_str = bt.num2date(dt).strftime("%Y-%m-%d %H:%M:%S")  # Convierte el número de punto flotante a cadena de fecha y hora
        print(f"{dt_str} {txt}")

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"Trade Closed - Profit: {trade.pnlcomm}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"Buy Executed - Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}")
            elif order.issell():
                self.log(f"Sell Executed - Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}")

    def next(self):
        #print(f"SMA1: {self.sma1[0]:.2f}, SMA2: {self.sma2[0]:.2f}, RSI: {self.rsi[0]:.2f}, Close: {self.data.close[0]:.2f}, BBands Top: {self.bbands.lines.top[0]:.2f}, BBands Bot: {self.bbands.lines.bot[0]:.2f}, shooting_star: {self.shooting_star[0]:.2f}, hammer: {self.hammer[0]:.2f}")
        # Condiciones para comprar
        buy_condition = (
            (self.sma1 > self.sma2 and self.sma1[-1] < self.sma2[-1]) or 
            (self.data.close < self.bbands.lines.bot or
            self.shooting_star > 0 or 
            self.rsi < self.params.rsi_oversold or self.hammer > 0)
        )

        # Condiciones para vender
        sell_condition = (
            (self.sma1 < self.sma2 and self.sma1[-1] > self.sma2[-1]) or
            (self.rsi > self.params.rsi_overbought or
            self.data.close > self.bbands.lines.top and
            self.shooting_star < 0 or self.hammer < 0)
        )

        if buy_condition:
            self.buy()

        elif sell_condition:
            self.sell()

if __name__ == "__main__":
    cerebro = bt.Cerebro()

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = modpath + '/data/orcl-1995-2014.txt'

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(1999, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2014, 12, 31),
        # Do not pass values after this date
        reverse=False)

    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy)

    # Configura el capital inicial y la comisión
    cerebro.broker.set_cash(100000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"Inicial Capital: {cerebro.broker.getvalue()}")

    cerebro.run()

    print(f"Final Capital: {cerebro.broker.getvalue()}")
    cerebro.plot()
