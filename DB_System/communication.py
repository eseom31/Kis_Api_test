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
    
class DB_Handle:
    def __init__(self, db_name: 'str'):
        self.DB_NAME = db_name
        self.CONN = pymysql.connect(host='localhost',
                                    user='root',
                                    password='sp_1234',
                                    db=self.DB_NAME,
                                    charset='utf8')
        self.CUR = self.CONN.cursor()
        # self.COLUMNS = """(code, dates, clpr, oppr, hgpr, lwpr, volume, acpr)"""
        self.COLUMNS = ['code', 'dates', 'clpr', 'oppr', 'hgpr', 'lwpr', 'volume', 'acpr']
    
    def read_json(self, path:str):
        with open(path, 'r', encoding='utf-8') as file:
            res = json.load(file)
        return res
    
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

    def fetch_base(self, sql: str):
        '''sql 형식에 맞춰 DB data를 fetch합니다.
        **args
        -sql: DB DML언어(posco BI matrix sql문과 같습니다)
        **return
        tuple of tuple'''
        self.CUR.execute(sql)
        return self.CUR.fetchall()    

    def commit(self):
        self.CONN.commit()
    
class DataHandle(DB_Handle):
    def __init__(self, db_name: 'str'):
        super().__init__(db_name=db_name)
        self.KOSPI_CODES = self.read_json('./SRC/kospi_codes.json')['회사명']
        self.KODAQ_CODES = self.read_json('./SRC/kosdaq_codes.json')['회사명']
    
    def __call__(self, src: tuple):
        '''fetch된 데이터를 활용해 dataframe객체를 생성합니다.
        **args
        -src: fetch된 data
        **return
        -pd.dataframe 객체'''
        rawcols = ['코드', '날짜', '종가', '시가', '최고가', '최저가', '누적거래량', '누적거래대금']
        df = pd.DataFrame(columns=rawcols, data=src, dtype='Int64')
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        return df
    
    def test(self, src: tuple):
        '''fetch된 데이터를 활용해 dataframe객체를 생성합니다.
        **args
        -src: fetch된 data
        **return
        -pd.dataframe 객체'''
        rawcols = ['코드', '날짜', '종가', '시가', '최고가', '최저가', '누적거래량', '누적거래대금']
        df = pd.DataFrame(columns=rawcols, data=src, dtype='Int64')
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        return df
    
    def read_json(self, path:str):
        with open(path, 'r', encoding='utf-8') as file:
            res = json.load(file)
        return res

    def get_data_for_pjt(self,
                    period: 'str' = None, 
                    start: 'str' = None,
                    end: 'str' = None,
                    companys: 'str | list' = 'all'):
        '''우리 project에 맞춰 DB에서 data를 fetch합니다.
        **args
        -market: 'kospi'와 'kosdaq'중 db연결 설정에 맞춰 입력합니다.
        -period: 파라미터에 'all'을 설정시 database에 저장된 회사별 최장기간이 자동으로 설정됩니다
        -start: datetime형식으로 시작 날짜 입니다 예)'20200101'
        -end: datetime형식으로 종료 날짜 입니다 예)'20200131'
        -codes: 전체 회사 설정하고 싶을때 'all'입력하고, 개별적으로 설정시 list형식으로 회사이름를 기재하여 입력합니다.
        **return
        -pd.DataFrame 객체
        '''
        results = []
        buf_companys = list(self.read_json(path=f'./SRC/{self.DB_NAME[:-4]}_codes.json')['회사명'].values()) if companys == 'all' else companys
        buf_period = '*' if period == 'all' else None
        for company in buf_companys:
            sql = f'''select {buf_period} from {company} '''
            res = self.fetch_base(sql)
            results.append(self.__call__(res))
        return pd.concat(results)

    def moving_average(self, data:pd.DataFrame, colname: str, utilname: str,samples=20):
        '''data 내 원하는 정보를 활용해 단순이동평균을 구하여 column을 추가한 df객체를 return합니다.
        **args
        -data: 말안해도 알쥬?
        -colname: 설정할 열이름
        -utilname: 이동평균할 열 이름
        -samples: 이동평균할 sample 개수 (default=20)
        **return
        -pd.DataFrame형식의 객체'''
        data[colname] = data[utilname].rolling(samples).mean()
        data.dropna(inplace=True)
        data.reset_index(inplace=True, drop=True)
        return data