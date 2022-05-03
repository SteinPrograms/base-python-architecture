from settings import Settings
import pymongo
from urllib.parse import quote_plus

def mean(array : list)->float:
    return sum(array)/len(array)


class Prediction:
    def __init__(self):
        pass

    def request_entry_price(self,):

        uri = "mongodb+srv://hugodemenez:Manonhugo147@test.yqzxd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        client = pymongo.MongoClient(uri)
        db = client.Trading
        try:
            return db.Target.find_one({})['target']
        except Exception:
            return 0.0

    def get_entry_price_target(self,symbol):
        historicalData = Settings().broker.get_historical_data(symbol,60)
        return mean([Data["close"] for Data in historicalData])

        
    def signal(self,symbol:str) ->dict[str]:
        currentPrice = Settings().broker.price(symbol)["bid"]
        if round(currentPrice,0)==round(self.get_entry_price_target(symbol),0):
            return {"signal":"buy"}
        else:
            return {"signal":"neutral"}
        
        
if __name__ == "__main__":
    print(Prediction().request_entry_price())