from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger
import numpy as np
import pandas as pd
from datetime import datetime as dt
from time import sleep
from datetime import datetime,timedelta
from requests.exceptions import ReadTimeout  # Add this import for handling ReadTimeout

def Connect_Server():
    api_key = ' '
    secret_key=''
    username = ''
    pwd = ''
    smartApi = SmartConnect(api_key)#'GGWZRKYY4MSIBZTGQNIA4QSNSM'
    try:
        token = ''
        totp = pyotp.TOTP(token).now()
    except Exception as e:
        logger.error("Invalid Token: The provided token is not valid.")
        raise e
    
    correlation_id = "abcde"
    data = smartApi.generateSession(username, pwd, totp)
    
    if data['status'] == False:
        logger.error(data)
        
    else:
        # login api call
        # logger.info(f"You Credentials: {data}")
        authToken = data['data']['jwtToken']
        refreshToken = data['data']['refreshToken']
        # fetch the feedtoken
        feedToken = smartApi.getfeedToken()
        # fetch User Profile
        res = smartApi.getProfile(refreshToken)
        smartApi.generateToken(refreshToken)
        res=res['data']['exchanges']
        print(res)
    return(smartApi)


def Start_Trading(stock_symbol_name='MASTEK-EQ',exchange="NSE",Quantity=1,SL_pct=-1,TP_pct=3,update_sl_tp=False,current_pos=False,smartApi=Connect_Server(),print_data=True,wait_sleep=15):
    open_position=current_pos
    srch=smartApi.searchScrip(exchange,stock_symbol_name)['data'][0]
    symbol=srch['tradingsymbol']
    symbol_token=srch['symboltoken']
    dd = (datetime.now())
    SL=SL_pct
    TP=TP_pct
    max_pl=0
    pl=0
    if print_data:
        print(f"{dd} Symbol: {symbol} symbol_token: {symbol_token} QNT: {Quantity} SL: {SL} TP: {TP} ")
    formatted_now = (dd+timedelta(days=15)).strftime("%Y-%m-%d")
    
    formatted_last=(dd-timedelta(days=4)).strftime("%Y-%m-%d")
    
    
    hp={
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": formatted_last+" 09:00", 
        "todate": (formatted_now+" 16:00")
        }
    
    hp2={
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": "ONE_MINUTE",
        "fromdate": formatted_last+" 09:00", 
        "todate": formatted_now+ " 16:00"
        }
    last=0
    net_qnt=0
    count=0
    a=smartApi.getCandleData(hp)
    d=pd.DataFrame(a['data'])
    d.set_index(0,inplace=True)
    d.index=pd.to_datetime(d.index)
    d.rename(columns={1:"Open",2:"High",3:"Low",4:"Close",5:'Volume'},inplace=True)
    d['6ma']=d.Close.rolling(6).mean()
    d['14ma']=d.Close.rolling(14).mean()
    d=d.iloc[:-1]
    pos=smartApi.position()
    order_book=smartApi.orderBook()
    if pos['data']!=None:
        if order_book['data'][-1]['transactiontype']=="BUY":
            buy_price=float(order_book['data'][-1]['averageprice'])
        else:
            buy_price=None
    try:
        while True:

            dd = (datetime.now())
            try:
                if (dd.strftime('%H:%M')>="09:14")and (dd.strftime('%H:%M')<="15:30") and ((dd.isoweekday()!=6) or (dd.isoweekday()!=7)) :#and:
                        
                    pos=smartApi.position()
                    if (dd.strftime('%H:%M')=="09:15"):
                        max_pl=0
                        smartApi=Connect_Server()
                        last=0
                        net_qnt=0
                        count=0
                        SL=SL_pct
                        TP=TP_pct
                        a=smartApi.getCandleData(hp)
                        d=pd.DataFrame(a['data'])
                        d.set_index(0,inplace=True)
                        d.index=pd.to_datetime(d.index)
                        d.rename(columns={1:"Open",2:"High",3:"Low",4:"Close",5:'Volume'},inplace=True)
                        d['6ma']=d.Close.rolling(6).mean()
                        d['14ma']=d.Close.rolling(14).mean()
                        d=d.iloc[:-1]
                        unrealized=0
                        buy_price=None
                        # pos=smartApi.position()

                    
                    if (dd.strftime('%H:%M')=="15:30"):
                        print(f"is_pos_open:{open_position}")
                        if pos['data']!=None:
                            print(f"realized_pl:{pos['data'][0]['realised']}")
                        
                    if (open_position) and  (pos['data']==None):
                        orderparams = {
                                "variety": "NORMAL",
                                "tradingsymbol": symbol,
                                "symboltoken": symbol_token,
                                "transactiontype": "BUY",
                                "exchange": exchange,
                                "ordertype": "MARKET",
                                "producttype": "INTRADAY",
                                "duration": "DAY",
                                "price": "0",
                                "squareoff": "0",
                                "stoploss": "0",
                                "quantity": Quantity
                                }
                        smartApi.placeOrder(orderparams)
                        buy_price=float(smartApi.orderBook()['data'][-1]['averageprice'])
                        SL=SL_pct
                        TP=TP_pct
                        max_pl=0
                        count+=1
                    
                        pos=smartApi.position()
                        if print_data:
                            print(dd,f" Purchased:{buy_price} entered without signal:")
  
                    
                    if pos['data']!=None:
                        for i in pos['data']:
                            if(i['symboltoken']==symbol_token):
                                
                                net_qnt=int(i['netqty'])
                                
                                if net_qnt!=0:#smartApi.orderBook()['data'][-1]['transactiontype']=="BUY":
                                    # buy_price=float(smartApi.orderBook()['data'][-1]['averageprice'])
                                    pl=round(((float(i['ltp'])-float(buy_price))*100/(float(buy_price))),3)
                                unrealized=(i['unrealised'])#pl*net_qnt*buy_price
                            
                    if  (dd.minute%15==0):
                    
                
                        a=smartApi.getCandleData(hp)
                        d=pd.DataFrame(a['data'])
                        d.set_index(0,inplace=True)
                        d.index=pd.to_datetime(d.index)
                        d.rename(columns={1:"Open",2:"High",3:"Low",4:"Close",5:'Volume'},inplace=True)
                        d=d.iloc[-100:]
                        d['6ma']=d.Close.rolling(6).mean()
                        d['14ma']=d.Close.rolling(14).mean()
            
            
            
                    if len(d)!=0:
                        df=pd.DataFrame(smartApi.getCandleData(hp2)['data']).iloc[-10:]
                        df.set_index(0,inplace=True)
                        df.index=pd.to_datetime(df.index)
                        new=df.index[-1]
                        
                      
                    if new!=last:
                        # print(df.iloc[-1:])
                        last=new
                   
                        df.rename(columns={1:"Open",2:"High",3:"Low",4:"Close",5:'Volume'},inplace=True)
                        last=df.index[-1]
                        if print_data:
                            print(last,"total_trades:",count,"ltp",round(df.iloc[-1].Close,2),f"ma6:{round(d.iloc[-1]['6ma'],2)} ma14: {round(d.iloc[-1]['14ma'],2)} max_pl:{max_pl} sl:{SL} tp={TP}")            
                        if (net_qnt==0) and (d.iloc[-2]['14ma']>df.iloc[-2]['Close'] ) &( d.iloc[-2]["14ma"]>d.iloc[-2]["6ma"]) & (d.iloc[-2]["6ma"]>df.iloc[-2]['Close']) & (d.iloc[-1]['6ma']<df.iloc[-1]['Close']):
                            orderparams = {
                                    "variety": "NORMAL",
                                    "tradingsymbol": symbol,
                                    "symboltoken": symbol_token,
                                    "transactiontype": "BUY",
                                    "exchange": exchange,
                                    "ordertype": "MARKET",
                                    "producttype": "INTRADAY",
                                    "duration": "DAY",
                                    "price": "0",
                                    "squareoff": "0",
                                    "stoploss": "0",
                                    "quantity": Quantity
                                    }
                            smartApi.placeOrder(orderparams)
                            buy_price=float(smartApi.orderBook()['data'][-1]['averageprice'])
                            SL=SL_pct
                            TP=TP_pct
                            max_pl=0
                            count+=1
                            if (dd.strftime('%H:%M')>"13:00"):
                                open_position=True
                            if print_data:
                                print(dd," Purchased: ",buy_price)
                            
                    
                    if (net_qnt!=0):
                        
                        if print_data:
                            print("net qnt",net_qnt,"p&l:",pl,"%","Unrealized Value(Rs.): ", unrealized )
        
                        if (max_pl<pl) and (update_sl_tp) :#(pl>TP) and (update_sl_tp) :
                            max_pl=pl
                            if (SL!=(int(max_pl)-1)+(1+SL)):#-0.9 !=-1 (0.5-1)+(1-0.9)
                                TP=TP+2
                                SL=SL+1#(max_pl-int(max_pl))
                                if print_data:
                                    print(f"Stop_loss % and Target_price % Changed new sl {SL} new TP {TP}")
                                
                        if (pl>TP) or (pl<SL):
                            
                            orderparams = {
                                "variety": "NORMAL",
                                "tradingsymbol":symbol,
                                "symboltoken": symbol_token,
                                "transactiontype": "SELL",
                                "exchange": exchange,
                                "ordertype": "MARKET",
                                "producttype": "INTRADAY",
                                "duration": "DAY",
                                "price": "0",
                                "squareoff": "0",
                                "stoploss": "0",
                                "quantity": Quantity
                                }
                            
                            smartApi.placeOrder(orderparams)
                            open_position=False
                            
                            
                            if print_data:
                                print(dd," Position Closed :",net_qnt,"p&l :",round(pl,2),"%")
                sleep(wait_sleep)
                
                                
            except NameError as e:
                print('##'*50)
                print(f"{dd} 11 Caught an error: {e}")
            except ReadTimeout as e:
                print('##'*50)
                logger.error(f"Read timeout error: {e}. Retrying in {wait_sleep} seconds...")
                continue
        
            except Exception as e:
                print('##'*50)
                logger.error(f"An unexpected error occurred: {e}")
                continue


    
    except KeyboardInterrupt:
        pass
    
        
            
            
