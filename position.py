import datetime
import time

from brokerconnection import RealCommands
from prediction import Prediction
from settings import Settings

class Position:
    '''This class is used to store all the data used to create orders and to make the calculation.
    
    Defaults : backtesting is True and symbol is 'BTC'
    '''
    def __init__(self,backtesting : bool = True,symbol : str = 'BTC',):
        self.symbol = f'{symbol}/{Settings().base_asset}'
        self.backtesting = backtesting
        self.status='close'
        self.current_effective_yield = 1
        self.total_yield = 1
        self.highest_yield=1
    
    def is_open(self):
        return self.status=='open'
    
    def open_position(self):
        """This function send an open order to the broker, with the opening price,
        and then save the data inside the class Position.
        
        """
        if not self.backtesting:
            order = RealCommands().limit_open(symbol=self.symbol, backtesting=self.backtesting)
            if order['error']:
                return False
            self.open_price = float(order['order']['price'])
            current_price = Settings().broker.price(self.symbol)['ask']
        else:
            # Simulation of opening position time by broker
            time.sleep(2)
            current_price = Settings().broker.price(self.symbol)['ask']
            self.open_price = current_price


        self.current_price = current_price
        # Setting highest price and lowest price to the opening price
        self.highest_price = self.open_price
        self.lowest_price = self.open_price
        self.status = 'open'
        self.time = time.time()
        return True


    def close_position(self):
        """This function send a close order to the broker, at market, and then save the data inside an excel spreadsheet.
        
        """
        self.status = 'close'
        self.effective_yield = self.effective_yield_calculation(self.close_price, self.open_price, Settings().fee)
        self.total_yield = round(self.total_yield * self.effective_yield, 5)
        if self.total_yield > self.highest_yield:
            self.highest_yield = self.total_yield
        return


    def force_position_close(self):
        if self.backtesting:
            self.close_price = self.current_price
        else:
            order = RealCommands().limit_close(self.symbol, backtesting=self.backtesting)
            print(order)
            self.close_price = float(order['price'])
        self.close_mode = "force-close"
        
        self.close_position()
        return
    
    

    def check_position(self):
        """ Function to update the current_price, the highest_price and the lowest price
        Then checks if it has to close the position
        
        """
        self.current_price = Settings().broker.price(self.symbol)['bid']

        # Updating highest_price
        if self.current_price > self.highest_price:
            self.highest_price = self.current_price

            # Updating lowest_price
        if self.current_price < self.lowest_price:
            self.lowest_price = self.current_price

            # Calculating current effective_yield
        self.current_effective_yield = self.effective_yield_calculation(
            current_price=self.current_price,
            opening_price=self.open_price,
            fee=Settings().fee
        )

        # Stop loss
        # Close position :
        if self.current_effective_yield < Settings().risk:
            if self.backtesting:
                self.close_price = self.open_price * Settings().risk
            else:
                order = RealCommands().limit_close(self.symbol, backtesting=self.backtesting)
                self.close_price = float(order['price'])
            self.close_mode = "stop-loss"
            self.close_position()
            return

        # Take profit on expected yield
        # Closing on take-profit : Check if the yield  is stronger  than the minimal yield considering fees and slippage
        if self.current_effective_yield > self.expected_yield:
            if self.backtesting:
                self.close_price = self.current_price
            else:
                order = RealCommands().limit_close(symbol=self.symbol, backtesting=self.backtesting)
                self.close_price = float(order['price'])
            self.close_mode = "take-profit"
            self.close_position()
            return
        
    def manage_position(self):
        """Manage position : look for selling or buying actions
        
        """

        statistics = {}
        
        if self.status == 'close':
            self.find_entry_point()

        else:
            try:
                # We check if we have to do something with the current position, update current price highest price and
                # lowest price
                self.check_position()
            except Exception as error:
                print("Unable to check position status",error)

            current_effective_yield = self.effective_yield_calculation(self.current_price, self.open_price, Settings().fee)
            # Give information about the program
            statistics = {'current_price': self.current_price, 
                          'open_price': self.open_price, 
                          'highest_price': self.highest_price, 
                          'lowest_price': self.lowest_price, 
                          'position_yield': f'{str(round((current_effective_yield - 1) * 100, 2))} %', 
                          'current_position_time': str(datetime.timedelta(seconds=round(time.time(), 0) - round(self.time, 0))),
                          'expected_yield': self.expected_yield}


        statistics['current_status'] = self.status
        statistics['total_yield'] = f'{str(round((self.total_yield - 1) * 100, 2))} %'

        for data, value__ in statistics.items():
            print(data, ':', value__, '\n')
        
    def find_entry_point(self):
        """[summary]

        Returns:
            [type]: [description]

        Yields:
            [type]: [description]
        """
        try:
            # We analyze the market with the signals defined inside prediction.py
            predict = Prediction().signal(self.symbol)

            for values in predict:
                print(values, ':', predict[values], '\n')

            # If we get a buy signal then :
            if predict['signal'] == 'buy' and self.open_position():
                self.expected_yield = predict['yield']
                return

        except Exception as error:
            print(f'error while predicting : {error}')
        # Else pause program
        time.sleep(2)
        
    def effective_yield_calculation(self,current_price, opening_price, fee):
        r = float(current_price) / float(opening_price)
        f = float(fee)
        return r - (f + (1 - f) * r * f)