import requests
import json

class StockConnection:
    def __init__(self):
        self.APP_KEY = "PSWteYi8gYUyChnKTEvcNXLqguNIRUoFbNfP"
        self.APP_SECRET = 'ZnEPFAvBPKC09eFObRJ1hWqzwRH8tTKTxB4xkCBKBsnUkfROZJ2N4SrwsGj/sKqieHqLJnQWFZyT47K385TBhXDm8toY2tLDRK3dLo10f6B6+CYIqv89crgltD+pxenjfMu1tbivV0UHEEOID42XGoDFpuzD9BjEJ5/95OAr7NkNUVc8v1w='
        self.URL_BASE = "https://openapivts.koreainvestment.com:29443"
        self.TOKEN = self.get_key_for_monitor()
        
    def get_key_for_monitor(self):
        '''보안인증키 발급 메서드
        *보안인증키는 정보 조회시 사용'''
        headers = {"content-type":"application/json"}
        body = {"grant_type":"client_credentials", "appkey":self.APP_KEY, "appsecret":self.APP_SECRET}
        url = self.URL_BASE + '/' + 'oauth2/tokenP'
        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res.json()['access_token']
    
    def get_key_for_trading(self, data:dict):
        '''hashkey발급 메서드
        *hashkey는 거래 체결시 사용'''
        headers = {"content-type":"application/json", "appkey":self.APP_KEY, "appsecret":self.APP_SECRET}
        url = self.URL_BASE + '/' + 'uapi/hashkey'
        print(url)
        res = requests.post(url, headers=headers, data=json.dumps(data))
        return res.json()["HASH"]
    
    #### 국내주식 기간별 시세 (일/주/원/년) 최대 100건 조회가능 
    def date_price(self, no:str, start:str, end:str, period:str):
        '''국내주식기간별시세 조회 메서드
        **input**
        - no: 종목코드 ex)삼성전자->005930
        - start: 입력날짜(시작) ex)20220501
        - end: 입력날짜(종료) ex)20220530
        - period: 기간분류코드 ex) 일봉->D, 주봉->W, 월봉->M, 년봉->Y
        
        ※ 제한: 1회 호출당 최대 100건까지 조회가능
        '''
        path = 'uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
        url = f"{self.URL_BASE}/{path}"
        headers = {"Content-Type":"application/json", 
                "authorization": f"Bearer {self.TOKEN}",
                "appKey":self.APP_KEY,
                "appSecret":self.APP_SECRET,
                "tr_id":"FHKST03010100",
            }
        params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_date_1": start,
                "fid_input_date_2": end,
                "fid_input_iscd": no,
                "fid_org_adj_prc": "0",
                "fid_period_div_code":period}

        res = requests.get(url, headers=headers, params=params)
        return res.json()