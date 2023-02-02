import requests
import json
import pymysql
import pandas as pd

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
    
class DB_Handle():
    def __init__(self, db_name:str):
        self.DB_NAME = db_name
        self.CONN = pymysql.connect(host='localhost',
                                    user='root',
                                    password='sp_1234',
                                    db=self.DB_NAME,
                                    charset='utf8')
        self.CUR = self.CONN.cursor()
        # self.COLUMNS = """(code, dates, clpr, oppr, hgpr, lwpr, volume, acpr)"""
        self.COLUMNS = ['code', 'dates', 'clpr', 'oppr', 'hgpr', 'lwpr', 'volume', 'acpr']
        print('good')
    
    def create_table(self, table_name):
        '''우리 프로젝트에 맞는 테이블을 생성합니다.'''
        sql = f"""CREATE TABLE {table_name} (
            code CHAR(6),
            dates CHAR(8) NOT NULL PRIMARY KEY, 
            clpr VARCHAR(45),
            oppr VARCHAR(45),
            hgpr VARCHAR(45),
            lwpr VARCHAR(45),
            volume VARCHAR(45),
            acpr VARCHAR(45));"""
        self.CUR.execute(sql)
        self.commit()
        
    def insert(self, table_name: str, telegram: list):
        vals = tuple(telegram)
        sql = f"""INSERT INTO {table_name} ({str(', '.join(self.COLUMNS))}) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        self.CUR.execute(sql, vals)
        self.commit()

    def fetch(self, sql: str):
        '''sql 형식에 맞춰 DB data를 fetch합니다.
        **args
        -sql: DB DML언어(posco BI matrix sql문과 같습니다)
        **return
        -pd.DataFrame형식의 객체'''
        self.CUR.execute(sql)
        df = pd.DataFrame(columns=self.COLUMNS, data=self.CUR.fetchall(), dtype='Int64')
        df['dates'] = pd.to_datetime(df['dates'], format='%Y%m%d')
        return df

    def commit(self):
        self.CONN.commit()
    
class DataHandle():
    def __init__(self):
        pass
    
    def moving_average(self, data:pd.DataFrame, column: str, samples=20):
        '''data의 종가 기준 단순이동평균을 구하여 column을 추가한 df객체를 return합니다.
        **args
        -data: 말안해도 알쥬?
        -column: 설정할 열이름
        -samples: 이동평균할 sample 개수 (default=20)
        **return
        -pd.DataFrame형식의 객체'''
        data[column] = data['clpr'].rolling(samples).mean()
        data.dropna(inplace=True)
        data.reset_index(inplace=True, drop=True)
        return data