import contextlib
import os,time,re
from app.logics.settings import Settings

class RealCommands:
    def __init__(self) -> None:
        self.broker = Settings().broker
        path = Settings().path
        if os.path.exists(path) == False:
            print("YOU MUST CREATE KEY FILE")
            self.broker.create_key_file()
        self.broker.connect_key(path)

    def test_connection(self,):
        return self.broker.test_order()
    
    def get_order_status(self,id):
        return self.broker.get_order_status(id)
        

    def limit_close(self,symbol,backtesting):
        # Checking connectivity
        print("checking connectivity")
        
        # Checking backtesting mode
        if not backtesting:
            while True:
                try:
                    # Get the quantity of crypto in balance
                    balance = self.broker.get_balances(re.sub("[^0-9a-zA-Z]+", "", symbol.replace(Settings().base_asset,'')))
                    quantity = float(balance['free'])
                    break
                except Exception:
                    time.sleep(0.2)
            print("Creating sell order")
            
            # Initializing counter to overcome order issues
            counter=0
            while(True):
                try:
                    # Create the sell order with the whole quantity of asset
                    order = self.broker.place_order(symbol,"sell",0,quantity,'market')
                    #We test if there is a code error
                    print("SellingOrderApproval",order["msg"])
                    time.sleep(0.2)
                    counter+=1
                    if counter ==10:
                        return {'error':True}
                except Exception:
                    break

            # Now wait for the order to be filled.
            while(True):
                print("Waiting for the order to be filled")
                while(True):
                    try:
                        # Get the quantity of fiat in balance
                        balance = self.broker.get_balances(Settings().base_asset)
                        quantity = float(balance['free'])
                        break
                    except Exception as error:
                        print(error)
                        time.sleep(1)
                        
                ### Get here once fiat balance is successfully retrieved
                # If we have at least 20 $ free of fiat balance then it means sell is executed
                if quantity > 20:
                    print("Order filled")
                    break

                ### Else it means the order is not executed yet
                time.sleep(0.2)                    
            return {'error':False,'order':order}

    def limit_open(self,symbol,backtesting):
        # Checking connectivity
        if backtesting:
            return

        print("getting the balance...")
        while(True):
            try:
                # Get the quantity of fiat in balance
                balance = self.broker.get_balances(Settings().base_asset)
                quantity = float(balance['free'])
                break
            except Exception as error:
                print(error)
                time.sleep(0.2)

        print("Creating buy order...")
        counter=0
        while True:
            try:
                # Create the buy order with the whole quantity you can buy with balance
                try:
                    order = self.broker.place_order(symbol,"buy",0,(quantity-5)/self.broker.price(symbol)['bid'],'market')

                except Exception as error:
                    print(error)

                #We test if there is a code error  
                print("BuyOrderApproval",order["msg"])
                time.sleep(0.2)
                counter+=1
                if counter ==10:
                    return {'error':True}
            except Exception:
                break

        print("Waiting for the order to be filled")
        # Now wait for the order to be filled.
        while True:
            with contextlib.suppress(Exception):
                while(True):
                    try:
                        # Get the quantity of fiat in balance
                        balance = self.broker.get_balances(Settings().base_asset)
                        quantity = float(balance['free'])
                        break
                    except Exception as error:
                        print(error)
                        time.sleep(0.2)
                if quantity < 20:
                    print("Order filled")
                    break
        return {'error':False,'order':order}
    
    def balance_check(self) -> float:
        print("getting the balance...")
        while(True):
            try:
                # Get the quantity of fiat in balance
                balance = self.broker.get_balances(Settings().base_asset)
                quantity = float(balance['free'])
                # It is ok if quanity is high enough
                if quantity > 20:
                    return quantity
                raise Exception("Balance is currently null")
                
            except Exception as error:
                print(error)
                time.sleep(0.2)

    

if __name__ == '__main__':
   #print(RealCommands().broker.place_order("BTC/USD","sell",0,0.000556,'market'))
    # Testing brokerconnection with buy/sell orders
    print(RealCommands().limit_open("BTC/USD",False))
    print(RealCommands().limit_close("BTC/USD",False))
    
    