import requests
import json

from DB_System.communication import StockConnection


class Trading(StockConnection):
    def __init__(self,
                simulate: 'bool' = False):
        '''추후개발예정'''
        self.simulate = simulate
        super().__init__(simulate=self.simulate)
        pass
        
    def stock_order(self,
                    code,
                    amount,
                    sales_calss):
        '''국내주식주문(현금) 메서드  ******보완 필요 데이터 설계가 제대로 안됨'''
        buf = 'TTC0802U' if sales_calss == '매수' else 'TTC0801U'
        tr_id = 'T' + buf if self.simulate == False else 'V' + buf 
        path = 'uapi/domestic-stock/v1/trading/order-cash'
        url = f"{self.URL_BASE}/{path}"
        body = {
            "CANO" : "__", #계좌번호 체계(8-2)의 앞자리 8자리
            "ACNT_PRDT_CD" : "__", #계좌번호 체계(8-2)의 뒤자리 2자리
            "PDNO" : code,
            "ORD_DVSN" : "06", #장후 시간외 
            "ORD_QTY" : amount,
            "ORD_UNPR" : "0" #장전 시간외, 장후 시간외, 시장가의 경우 1주당 가격 공란을 비우지 않음 "0"으로 입력 권고
        }
        header = {"Content-Type" : "application/json", 
                "authorization" : f"Bearer {self.TOKEN}",
                "appKey" : self.APP_KEY,
                "appSecret" : self.APP_SECRET,
                "custtype" : "P", #개인 
                "tr_id" : tr_id,
                "hashkey":self.capsulation_for_trading(body) ## 보완 필요
            }
        res = requests.post(url, headers=header, data=json.dumps(body))
        print(res.json())
        
    def market_timing(self):
        '''market timing'''
        pass
    
    def filter_by_volume(self):
        '''거래대금 필터링'''
        pass
    
    def trend_fllowing(self):
        '''추세전략'''
        pass