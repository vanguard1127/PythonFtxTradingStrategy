import math
import sys
import datetime
import requests
import time
import urllib
import hmac
import hashlib
import ccxt


URL = "https://ftx.com/api/"


class FtxClient:
    def __init__(self, api, secret, subaccount):
        self.api = api
        self.secret = secret
        self.subaccount = urllib.parse.quote(subaccount, safe='')
        self.client = requests.session()
        self.ftx = ccxt.ftx({
            'apiKey': self.api,
            'secret': self.secret,
            'enableRateLimit': True,
            'headers': {
                'FTX-SUBACCOUNT': self.subaccount
            }
        })

    def GetHistoricalPrices(self, market: str, resolution: int, limit: int, startTime: int, endTime: int):
        resp, err = self._get(
            "markets/" + market +
                "/candles?resolution=" + str(resolution) +
                "&limit=" + str(limit) +
                "&start_time=" + str(startTime) +
                "&end_time=" + str(endTime), ""
        )
        if err != None:
            print("Error GetHistoricalPrices ", err)
            return [None, err]

        return [resp, err]


    def GetPositions(self, showAvgPrice: bool):
        resp, err = self._get("positions", "")
        if err != None:
            print("Error GetPositions ", err)
            return [None, err]
        return [resp, err]


    def PlaceOrder(self, market: str, side: str, price: float, _type: str, size: float, reduceOnly: bool, ioc: bool, postOnly: bool):
        order = self.ftx.create_order(market, _type, side, size, price, {})
        return [order, None]
        # requestBody = {
        #     'market': market,
        #     'side': side,
        #     'price': price,
        #     'type': _type,
        #     'size': size,
        #     'reduceOnly': reduceOnly,
        #     'ioc': ioc,
        #     'postOnly': postOnly
        # }
        # resp, err = self._post("orders", requestBody)
        # if err != None:
        #     print("Error PlaceOrder ", err)
        #     return [None, err]
        #
        # return [resp, err]

    def GetOpenOrders(self, market: str):
        orders = self.ftx.fetch_open_orders(market, None, None, {})
        return [orders, None]
        # resp, err = self._get("orders?market=" + market, "")
        #
        # if err != None:
        #     print("Error GetOpenOrders ", err)
        #     return [None, err]
        #
        # return [resp, err]

    def CancelOrder(self, orderId: str):
        ret = self.ftx.cancel_order(orderId, None, {})
        return [ret, None]
        # id = str(orderId)
        # resp, err = self._delete("orders/" + id, "")
        #
        # if err != None:
        #     print("Error CancelOrder", err)
        #     return [None, err]
        #
        # return [resp.json(), err]


    def sign(self, signaturePayload: str) -> str:
        encoded_secret = self.secret.encode()
        secret_byte_array = bytearray(encoded_secret)
        encoded_sgPayload = signaturePayload.encode()
        sgPayload_byte_array = bytearray(encoded_sgPayload)
        signature = hmac.new(secret_byte_array, sgPayload_byte_array, hashlib.sha256).hexdigest()
        return signature

    def signRequest(self, method: str, path: str, body):
        ts = str(int(datetime.datetime.utcnow().timestamp() * 1000))
        signaturePayload = ts + method + "/api/" + path + str(body)
        signature = self.sign(signaturePayload)

        header = {
            'Content-Type': 'application/json',
            'FTX-KEY': self.api,
            'FTX-SIGN': signature,
            'FTX-TS': ts
        }
        if self.subaccount != '':
            header['FTX-SUBACCOUNT'] = self.subaccount
        req = requests.Request(method=method, headers=header, url=(URL + path), json=body)
        prepare = req.prepare()
        return prepare

    def _post(self, path, body):
        req = self.signRequest("POST", path, body)
        try:
            resp = self.client.send(req)
            return [resp.json(), None]
        except:
            print(sys.exc_info()[0])
            err = "error"
            return [None, err]

    def _get(self, path, body):
        req = self.signRequest("GET", path, body)
        try:
            resp = self.client.send(req)
            return [resp.json(), None]
        except:
            print(sys.exc_info()[0])
            err = "error"
            return [None, err]

    def _delete(self, path: str, body: str):
        req = self.signRequest("DELETE", path, body)
        try:
            resp = self.client.send(req)
            return [resp.json(), None]
        except:
            print(sys.exc_info()[0])
            err = "error"
            return [None, err]


def Kappa(arg1: int, arg2: str) -> dict:
    depth = str(arg1)
    try:
        r = requests.get("https://ftx.com/api/markets/" + arg2 + "/orderbook?depth=" + depth)
    except:
        print("Order Book Data Cannot Be Retrived")
        print("Please Wait Until Order Book Data Can Be Retrived")
        time.sleep(15)

        Kappa(arg1, arg2)

    response = r.json()

    if not('result' in response):
        response['result'] = []

    bid_price = []
    bid_size = []
    ask_price = []
    ask_size = []

    if len(response['result']['bids']) != arg1 or len(response['result']['asks']) != arg1:
        print("Order Book Data Is Incomplete")
        print("Please Wait Until Order Book Data Is Full")
        time.sleep(15)

        Kappa(arg1, arg2)

    i = 0
    while i < arg1:
        bid_price.append(response['result']['bids'][i][0])
        bid_size.append(response['result']['bids'][i][1])
        ask_price.append(response['result']['asks'][i][0])
        ask_size.append(response['result']['asks'][i][1])
        i += 1

    kappa = 0.0
    total_bid_size = 0.0
    total_ask_size = 0.0
    j = 0
    while j < arg1:
        kappa = kappa + (bid_price[j] * bid_size[j]) + (ask_price[j] * ask_size[j])
        total_bid_size = total_bid_size + bid_size[j]
        total_ask_size = total_ask_size + ask_size[j]
        j += 1

    midpoint = (bid_price[0] + ask_price[0]) / 2
    imbalance = total_bid_size / (total_bid_size + total_ask_size)
    weighted_midpoint = (imbalance * ask_price[0]) + ((1 - imbalance) * bid_price[0])
    return [midpoint, weighted_midpoint, kappa, bid_price[0], ask_price[0]]


def Sigma(arg1: str, arg2: str, arg3: str, arg4: str, arg5: str, arg6: float) -> float:
    client = FtxClient(arg3, arg4, arg5)
    try:
        interval = int(arg2)
    except:
        print(sys.exc_info()[0])

    t = datetime.datetime.now()
    past_time = int((t - datetime.timedelta(seconds=interval)).timestamp())

    current_time = int(t.timestamp())

    candles, _ = client.GetHistoricalPrices(arg1, interval, 7, past_time, current_time)

    if not ('result' in candles):
        candles['result'] = []
    price_data = []
    if len(candles['result']) == 0:
        if arg6 == 0:
            print("Vol Cannot Be Measured...Shutting Down")
            exit(0)
        return arg6

    price_data.append(candles['result'][0]['open'])
    price_data.append(candles['result'][0]['high'])
    price_data.append(candles['result'][0]['low'])
    price_data.append(candles['result'][0]['close'])

    i = 0
    sum = 0.0

    while i < len(price_data):
        sum = sum + price_data[i]
        i += 1

    mean_price = sum / float(len(price_data))
    average_distance = 0

    j = 0
    while j < len(price_data):
        average_distance = average_distance + pow((price_data[j] - mean_price), 2)
        j += 1

    variance = average_distance / float(len(price_data) - 1)
    sigma = math.sqrt(variance)

    if sigma == 0:
        return arg6
    return sigma


def getBollinger(symbol: str, resolution: str, timeperiod: str, nbdevdn:str, nbdevup: str) -> dict:
    APIKEY = "c3r13u2ad3i98m4ier5g"
    to_unix_timestamp = str(int(datetime.datetime.now().timestamp()))
    from_unix_timestamp = str(int(datetime.datetime.now().timestamp() - 10000))

    generateURL = "https://finnhub.io/api/v1/indicator?symbol=" \
                    + symbol + "&indicator=BBANDS&resolution=" \
                    + resolution + "&from=" \
                    + from_unix_timestamp + "&to=" \
                    + to_unix_timestamp + "&timeperiod=" \
                    + timeperiod + "&nbdevup=" \
                    + nbdevup + "&dbdevdn=" \
                    + nbdevdn + "&token=" \
                    + APIKEY

    try:
        r = requests.post(generateURL, headers=None)
    except:
        print(sys.exc_info()[0])

    response = r.json()
    lowerband = response['lowerband'][len(response['lowerband']) - 1]
    middleband = response['middleband'][len(response['middleband']) - 1]
    upperband = response['upperband'][len(response['upperband']) - 1 ]
    return [lowerband, middleband, upperband]


def Get_Positions(arg1: str, arg2: str, arg3: str, arg4: str) -> dict:
    client = FtxClient(arg1, arg2, arg3)
    positions, _ = client.GetPositions(True)
    i = 0
    if not('result' in positions):
        positions['result'] = []

    while i < len(positions['result']):
        if arg4 == positions['result'][i]['future']:
            return [positions['result'][i]['realizePnl'], positions['result'][i]['unrealizePnl'],
                    positions['result'][i]['netSize'], positions['result'][i]['entryPrice']]
        i += 1
    return [0.0, 0.0, 0.0, 0.0]


def Reservation_Price(arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float) -> dict:
    reservation_price = arg1 - (arg2 * arg3 * pow(arg4, 2))
    aggresive_reservation_price = reservation_price - (arg2 / arg6 * arg5)
    return [reservation_price, aggresive_reservation_price]


def Optimal_Spread(arg1: float, arg2: float, arg3: float) -> float:
    optimal_speed = (arg1 * pow(arg2, 2)) + ((2 / arg1) * (math.log(1 + (arg1 / arg3))))
    return optimal_speed


def Place_Order(arg1: str, arg2: str, arg3: str, arg4: float, arg5: float, arg6: float,
                arg7: float, arg8: bool, arg9: str, arg10: float, arg11: float, arg12: float, arg13: float):
    client = FtxClient(arg1, arg2, arg3)
    bid_price = arg5 - arg6
    ask_price = arg5 + arg6

    if arg8 is True:
        if bid_price > arg10:
            bid_price = arg10
        if ask_price < arg11:
            ask_price = arg11

    if arg13 < -arg12:
        bid_order, _ = client.PlaceOrder(arg9, "buy", bid_price, "limit", arg4, False, False, arg8)
        print("Bid Offer: ", bid_order['info']['price'])
        time.sleep(arg7)

        openOrders, _ = client.GetOpenOrders(arg9)

        if len(openOrders) == 0:
            print("Bid Order Has Been Filled")
        elif len(openOrders) > 4:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled: ", openOrders[i]['side'])
                print(cancel)
                i += 1

            print("Too Many Cancellation Have Failed")
            exit(0)
        else:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled ", openOrders[i]['side'])
                print(cancel)
                i += 1
    elif arg13 > arg12:
        ask_order, _ = client.PlaceOrder(arg9, "sell", ask_price, "limit", arg4, False, False, arg8)
        print("Ask Offer: ", ask_order['info']['price'])

        time.sleep(arg7)

        openOrders, _ = client.GetOpenOrders(arg9)

        if len(openOrders) == 0:
            print("Ask Order Has Been Filled")
        elif len(openOrders) > 4:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled: ", openOrders[i]['side'])
                print(cancel)
                i += 1
            print("Too Many Cancellations Have Filled")
            exit(0)
        else:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled: ", openOrders[i]['side'])
                print(cancel)
                i += 1
    else:
        bid_order = client.PlaceOrder(arg9, "buy", bid_price, "limit", arg4, False, False, arg8)

        print("Ask Offer ", bid_order['info']['price'])

        ask_order, _ = client.PlaceOrder(arg9, "sell", ask_price, "limit", arg4, False, False, arg8)
        time.sleep(arg7)

        openOrders, _ = client.GetOpenOrders(arg9)

        if len(openOrders) == 0:
            print("Batch Orders Have Been Filled")
        elif len(openOrders) > 4:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled: ", openOrders[i]['Side'])
                print(cancel)
                i += 1

            print("Too Many Cancellations Have Failed")
            exit(0)
        else:
            i = 0
            while i < len(openOrders):
                cancel, _ = client.CancelOrder(openOrders[i]['id'])
                print("Order Side Cancelled: ", openOrders[i]['Side'])
                print(cancel)
                i += 1
    return ""


if __name__ == '__main__':
    # api_key = "qAb5nx4b3YEOuKp04FTwKNK3MHDoLgoIOoeERALg"
    # api_secret = "8snnuvYAZLBFom2KpcIQs2CsJEZlw9DdlEdt1eBk"
    # subaccount = "Test1"
    # order_trade_amount = 0.0052
    # aggressive_reserve_price = 3468.7
    # spread = 10.0
    # order_time = 20
    # post_only = True
    # ticker_symbol = "ETH-PERP"
    # best_bid = 3468.9
    # best_ask = 3469.0
    # inventory_cutoff = 0.02
    # target_distance = 0.0259
    # Place_Order(api_key, api_secret, subaccount, order_trade_amount, aggressive_reserve_price, spread,
    #             order_time, post_only, ticker_symbol, best_bid, best_ask, inventory_cutoff, target_distance)

    print('Trading Terminal Has Been Started !!')
    ticker_array = ["ETH-PERP", "BTC-PERP", "UNI-PERP", "LINK-PERP", "MKR-PERP", "DOGE-PERP"]
    print('Please Enter Ticker Symbol')
    print(ticker_array)
    ticker_symbol = input()
    ticker_found = 0
    index = 0
    for ticker in ticker_array:
        if ticker == ticker_symbol:
            ticker_found = 1

    if ticker_found == 0:
        print('Ticker Not Defined Within Data Structure')
        exit(0)

    print('Please Enter Stake Price')
    stake_price = float(input())

    print("Please Enter Upper Threshold")
    upper_threshold = float(input())

    if upper_threshold < stake_price:
        print("Something Went Wrong")
        exit(0)

    print("Please Enter Lower Threshold")
    lower_threshold = float(input())

    if lower_threshold > stake_price:
        print("Something Went Wrong")
        exit(0)

    print("Whats is Position Size")
    position_size = float(input())

    print("Please Enter Stake Multiplier")
    multiplier = float(input())

    print("Please Enter Volatility Time Interval (15, 60, 300)")
    volatility_interval = input()

    if volatility_interval != "15" and volatility_interval != "60" and volatility_interval != "300":
        print("Something Went Wrong")
        exit(0)

    print("Please Enter Order book Depth")
    order_book_depth = int(input())

    if order_book_depth < 10:
        print('Order Book Depth Too Small')
        exit(0)

    print("Please Enter Risk Aversion Parameter")
    print("Please Note: Gamma Must Exist Within The Set (0, 1)")
    gamma = float(input())

    if gamma >= 1 or gamma <= 0:
        print("The Parameter Entered For Gamma Is Incorrect")
        print("Trading Terminal Has Been Shut Down")
        exit(0)

    print("Please Enter Trade Amount")
    max_trade_amount = float(input())
    # order_trade_amount

    if max_trade_amount < 0.001:
        print("The Parameter Entered For Max Trade Amount Is Incorrect")
        print("Trading Terminal Has Been Shut Down")
        exit(0)
    print("Please Enter Order Refresh Time In Seconds")
    order_time = int(input())

    print("Please Enter Minimum Spread")
    minimum_spread = float(input())

    print("Please Enter Price Aggressor Multiplier")
    price_aggressor = float(input())

    print("Post Only?")
    print("0 For False, 1 For True")
    taker_binary = int(input())

    post_only = False

    if taker_binary == 0:
        post_only = False
    elif taker_binary == 1:
        post_only = True
    else:
        print("Something Went Wrong")
        exit(0)

    print("Please Enter Inventory Cutoff (ABSOLUTE VALUE TARGET DISTANCE)")
    inventory_cutoff = float(input())

    print("Enter timeperiod for BBands (in minutes):")
    timeperiod = input()

    print("Enter nbdevup for Upper BBands:")
    nbdevup = input()

    print("Enter nbdevdn for Lower BBands:")
    nbdevdn = input()

    lowerband, middleband, upperband = getBollinger("BINANCE:ETHUSDT", "1", timeperiod, nbdevdn, nbdevup)
    print("Lowerband: ", lowerband)
    print("Middleband: ", middleband)
    print("Upperband: ", upperband)
    print("\n")

    api_key = "qAb5nx4b3YEOuKp04FTwKNK3MHDoLgoIOoeERALg"
    api_secret = "8snnuvYAZLBFom2KpcIQs2CsJEZlw9DdlEdt1eBk"
    subaccount = "Test1"

    last_vol = 0.0
    inventory_target = 0.0

    i = 0

    while True:
        sigma = round(Sigma(ticker_symbol, volatility_interval, api_key, api_secret, subaccount, last_vol) * 100) / 100
        print("Sigma: ", sigma)

        last_vol = sigma

        midpoint, weighted_midpoint, kappa, best_bid, best_ask = Kappa(order_book_depth, ticker_symbol)
        print("Kappa: ", kappa)

        midpoint = round(midpoint * 100) / 100
        print("Midpoint Price: ", midpoint)

        weighted_midpoint = round(weighted_midpoint * 100) / 100
        print("Weighted Midpoint Price: ", weighted_midpoint)

        realized_pnl, unrealized_pnl, current_inventory, entry_price = Get_Positions(api_key, api_secret, subaccount,
                                                                                     ticker_symbol)
        print("Current Inventory: ", current_inventory)
        print("Realized Profit & Loss: ", realized_pnl)
        print("Unrealized Profit & Loss: ", unrealized_pnl)
        print("Entry Price: ", entry_price)

        if weighted_midpoint >= upper_threshold:
            inventory_target = position_size * multiplier
        elif weighted_midpoint <= lower_threshold:
            inventory_target = -(position_size * multiplier)
        elif weighted_midpoint < stake_price:
            inventory_target = (((weighted_midpoint - stake_price) / (
                    stake_price - lower_threshold)) * position_size * multiplier)
        elif weighted_midpoint == stake_price:
            inventory_target = 0
        elif weighted_midpoint > stake_price:
            inventory_target = (((weighted_midpoint - stake_price) / (
                    upper_threshold - stake_price)) * position_size * multiplier)

        inventory_target = round(inventory_target * 10000) / 10000
        print("Inventory Target:", inventory_target)

        target_distance = round((current_inventory - inventory_target) * 10000) / 10000
        print("Target Distance: ", target_distance)

        order_trade_amount = min(max_trade_amount, abs(target_distance / 5))
        order_trade_amount = round(order_trade_amount * 10000) / 10000
        print("Trade Amount: ", order_trade_amount)

        reserve_price, aggressive_reserve_price = Reservation_Price(weighted_midpoint, target_distance, gamma, sigma,
                                                                    price_aggressor, position_size)

        reserve_price = round(reserve_price * 100) / 100
        aggressive_reserve_price = round(aggressive_reserve_price * 100) / 100

        spread = round(Optimal_Spread(gamma, sigma, kappa) * 100) / 100

        if spread < minimum_spread:
            spread = minimum_spread

        print("Reservation Price: ", reserve_price)
        print("Aggressive Reservation Price: ", aggressive_reserve_price)
        print("Optimal Spread: ", spread)

        Place_Order(api_key, api_secret, subaccount, order_trade_amount, aggressive_reserve_price, spread,
                order_time, post_only, ticker_symbol, best_bid, best_ask, inventory_cutoff, target_distance)

        # if weighted_midpoint >= upper_threshold and current_inventory >= inventory_target:
        #     print("weighted_midpoint >= upper_threshold && current_inventory >= inventory_target, stop placing orders.")
        # elif weighted_midpoint <= lower_threshold and current_inventory >= inventory_target:
        #     print("weighted_midpoint <= lower_threshold && current_inventory >= inventory_target, stop placing orders.")
        # elif weighted_midpoint <= upperband and weighted_midpoint >= lowerband:
        #     print("price within bollinger band, stop placing orders.")
        # else:
        #     Place_Order(api_key, api_secret, subaccount, order_trade_amount, aggressive_reserve_price, spread,
        #                 order_time, post_only, ticker_symbol, best_bid, best_ask, inventory_cutoff, target_distance)
