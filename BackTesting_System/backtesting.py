import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List
from copy import deepcopy
from datetime import datetime
from tqdm import tqdm

    
def day_revenue():
    '''날짜별 수익'''
    pass

def month_revenue():
    '''월평균수익'''
    pass

def quarter_revenue():
    '''분기별수익'''
    pass

def year_revenue():
    '''년도별수익'''
    pass

def calc_mdd( 
    src: 'pd.DataFrame',
    start: 'str',
    end: 'str' ,
    code: 'str'):
    '''MDD(Maximum Drawdown) 계산을 실시합니다.
    MDD 계산 수식: (조회기간 내 최고가격 - 조회기간 내 최저가격) / 조회기간 내 최고가격 * 100.0
    **args
    -start: 조회 시작 일자
    -end: 조회 종료 일자
    -code: 회사 코드
    **return
    -flaot  객체를 반환합니다'''
    condition = (src['날짜'] > pd.to_datetime(start)) & (src['날짜'] < pd.to_datetime(end)) & (src['코드'] == code)
    return round(((src[condition].max()['종가'] - src[condition].min()['종가']) / src[condition].max()['종가']) * 100.0, 2)

def calc_sharp_index():
    '''샤프지수 계산'''
    pass

def calc_winning_rate():
    '''승률 계산'''
    pass



class logSystem:
    def __init__(self):
        self.ECONO_INFORM = pd.DataFrame(columns=['날짜','매수총합','매도총합','매매비용','실현손익'])
        self.JOUNAL = pd.DataFrame(columns=['날짜', '종목코드', '체결단가', '체결수량', '매매비용', '매매구분'])
        self.ASSET_INFM = {}
        
    def upsert_asset_infm(self,
                    code: 'str',
                    amount: 'int',
                    sales_class: 'str',
                    price = None):
        '''Log System Class 속성인 ASSET_INFM을 args에 맞춰 평단가, 수량을 갱신 및 추가합니다
        **args
        -code: string 형식으로 종목코드 ex)'005490'
        -amount: int형식으로 해당 종목코드의 체결 수량을 의미 
        -sales_class: string 형식으로 매매구분을 의미
        -price: 체결단가를 의미
        **return
        -None
        '''
        if not code in self.ASSET_INFM.keys():  
            self.ASSET_INFM[code] = {'평단가': price, '수량': amount}
        elif sales_class == '매수':
            self.ASSET_INFM[code]['평단가'] = ((self.ASSET_INFM[code]['평단가'] * self.ASSET_INFM[code]['수량']) + (price * amount)) / (self.ASSET_INFM[code]['수량'] + amount)
            self.ASSET_INFM[code]['수량'] +=  amount
        else:
            self.ASSET_INFM[code]['수량'] -=  amount
        self.ASSET_INFM = {key: val for key, val in self.ASSET_INFM.items() if val['수량'] != 0}
    
    def write_jounal(self, 
                    inform: 'List[pd.DatetimeIndex, str, int, int, int, str]'):
        '''BackTesting 클래스 내 존재하는 JOUNAL 속성에 일지를 작성합니다
        **args
        -inform: List형식으로 Jounal 양식에 맞는 데이터를 의미
        **return
        -None'''
        buf = {col: val for col, val in zip(self.JOUNAL.columns, inform)}
        self.JOUNAL = pd.concat([self.JOUNAL, pd.Series(buf).to_frame().T], ignore_index=True)
    
    def update_information(self):
        '''Jounal Data 전체를 이용하여 portfolio를 갱신합니다
        **args
        -None
        **return
        -None'''
        self.ASSET_INFM.clear()
        self.ECONO_INFORM.drop(self.ECONO_INFORM.index, inplace=True, errors='ignore')
        for date in self.JOUNAL['날짜'].unique():
            contents = self.JOUNAL[self.JOUNAL['날짜'] == date]
            tot_buy = contents[contents['매매구분']=='매수'][['체결단가', '체결수량']].apply(lambda x: x.prod(), axis=1).sum()
            tot_sell = contents[contents['매매구분']=='매도'][['체결단가', '체결수량']].apply(lambda x: x.prod(), axis=1).sum()
            deviation = contents[contents['매매구분']=='매도'].apply(lambda x: ((x['체결단가'] - self.ASSET_INFM[x['종목코드']]['평단가']) * x['체결수량']) - x['매매비용'], axis=1).sum()  
            real_profit = deviation if '매도' in list(contents['매매구분']) else 0.0
            buf = pd.Series({
                '날짜': date,
                '매수총합': tot_buy,
                '매도총합': tot_sell,
                '매매비용': contents['매매비용'].sum(),
                '실현손익': real_profit})
            self.ECONO_INFORM = pd.concat([self.ECONO_INFORM, buf.to_frame().T], ignore_index=True)
            for sales_class in ['매도', '매수']:    
                for _, row in contents[contents['매매구분']==sales_class].iterrows():
                    self.upsert_asset_infm(code=row['종목코드'], amount=row['체결수량'], sales_class=sales_class, price=row['체결단가'])
                    
                    
class BackTesting(logSystem):
    def __init__(self):
        super().__init__()
        self.MONEY = 0
        self.ASSET = {}
    
    def calc_tax(self,
            price: 'float',
            sales_class: 'str',
            used_slippage: 'bool' = False):
        '''세금 및 수수료를 계산하는 메서드입니다
        매수시 계산 공식 : 단가금액 * (위탁수수료 + 유관기관수수료)
        매도시 계산 공식(Slipage X) : 단가금액 * (위탁수수료 + 유관기관수수료 + 증권거래세)
        매도시 계산 공식(Slipage O) : 단가금액 * (위탁수수료 + 유관기관수수료 + 증권거래세 + Slippage loss)
        
        위탁수수료: 0.0140527%, 유관기관수수료: 0.0036396%, 증권거래세: 0.2%, Slippage loss: 1.0%  
        
        **args
        -price: float 형식으로 단가금액을 의미
        -sales_class: string 형식으로 매매구분을 의미
        -used_slippage: bool 형식으로 True이면 Slippage Risk 반영됩니다.(0.1%) default=False
        **return
        float 형식의 최종 계산 값'''
        commission = 0.0140527 * 0.01 #위탁 수수료
        gov_fee = 0.0036396 * 0.01 #유관기관 수수료
        tax = 0.2 * 0.01  #증권거레세
        slippage = 1.0 * 0.01
        if sales_class == '매수':
            res = price * (commission + gov_fee)
        elif sales_class == '매도':
            res = price * (commission + gov_fee + tax) if used_slippage == False else price * (commission + gov_fee + tax + slippage)
        return round(res, 0)

    def upsert_asset(self,
                code: 'str',
                amount: 'int',
                sales_class: bool,
                price = None):
        '''Backtesting System Class 속성인 ASSET을 args에 맞춰 평단가, 수량을 갱신 및 추가합니다
        **args
        -code: string 형식으로 종목코드 ex)'005490'
        -amount: int형식으로 해당 종목코드의 체결 수량을 의미 
        -sales_class: string 형식으로 매매구분을 의미
        -price: 체결단가를 의미
        **return
        -None
        '''
        if not code in self.ASSET.keys():  
            self.ASSET[code] = {'평단가': price, '수량': amount}
        elif sales_class == '매수':
            self.ASSET[code]['평단가'] = ((self.ASSET[code]['평단가'] * self.ASSET[code]['수량']) + (price * amount)) / (self.ASSET[code]['수량'] + amount)
            self.ASSET[code]['수량'] += amount
        else:
            self.ASSET[code]['수량'] -= amount
        self.ASSET = {key: val for key, val in self.ASSET.items() if val['수량'] != 0}

    def buy_sell(self,
                df: 'pd.DataFrame',
                buy: 'str',
                sell: 'str',
                use_slippage: 'bool' = False):
        '''df에 맞춰 가상 테스트를 실시하는 메서드 입니다
        진입기준: df 내 buy로 등록된 열의 command 신호에 따라 매수합니다
        익절매 기준: df 내 buy로 등록된 열의 command 신호에 따라 매도합니다
        손절매 기준: 종가가 평단가*2*ATR 낮으면 매도합니다 '''
        hd = deepcopy(df)  
        self.ASSET.clear()
        self.JOUNAL.drop(self.JOUNAL.index, inplace=True, errors='ignore')  
        for (day, buy), group_df in tqdm(hd.groupby(['날짜', buy], sort=True)):
            if buy != True:
                for _, data in group_df.iterrows():                
                    if data['코드'] in self.ASSET:
                        if (data[sell] == True) or (self.ASSET[data['코드']]['평단가'] - 2 * data['ATR'] > data['종가']):
                            tot_fee = self.calc_tax(price=data['종가'] * self.ASSET[str(data['코드']).zfill(6)]['수량'], sales_class='매도', used_slippage=use_slippage)                    
                            inform = [data['날짜'],
                                    str(data['코드']).zfill(6),
                                    data['종가'],
                                    self.ASSET[str(data['코드']).zfill(6)]['수량'],
                                    tot_fee,  
                                    '매도']
                            self.write_jounal(inform=inform)    
                            self.MONEY +=  (data['종가'] * self.ASSET[str(data['코드']).zfill(6)]['수량'] - tot_fee)
                            self.upsert_asset(code=str(data['코드']).zfill(6), amount=self.ASSET[str(data['코드']).zfill(6)]['수량'], sales_class='매도')     
            if buy == True:
                available_price = deepcopy(self.MONEY)
                sep_money = available_price / 10
                risk_by_1 = sep_money * 0.01
                price_by_unit = {code: price * (risk_by_1 / atr) for code, price, atr in zip(group_df['코드'], group_df['종가'], group_df['ATR'])}
                price_by_unit = dict(sorted(price_by_unit.items(), key=lambda x:x[1]))
                availabel_codes = {}
                for k, v in price_by_unit.items():
                    if (available_price - v >= 0) and (group_df[group_df['코드']==k]['종가'].iloc[0] < v):
                        nums = int(v / group_df[group_df['코드']==k]['종가'].iloc[0])
                        availabel_codes[k] = nums
                        available_price -= v
                for _, data in group_df.iterrows():
                    if data['코드'] in list(availabel_codes.keys()): 
                        tot_fee = self.calc_tax(price=data['종가'] * availabel_codes[data['코드']], sales_class='매수')
                        inform = [data['날짜'],
                                str(data['코드']).zfill(6),
                                data['종가'],
                                availabel_codes[data['코드']],
                                tot_fee,  
                                '매수']
                        self.write_jounal(inform=inform)    
                        self.MONEY -=  (data['종가'] * availabel_codes[data['코드']] + tot_fee)
                        self.upsert_asset(code=str(data['코드']).zfill(6), amount=availabel_codes[data['코드']], sales_class='매수', price=data['종가'])       
            
            
class Utils:
    def __init__(self):
        pass
    
    def deduplication_dates(self,
                            code,
                            jounal):
        '''dates 중복제거 매수매수 매도'''
        dates = []
        buf = []
        for _, row in jounal[jounal['종목코드'] == code].iterrows():
            if len(buf) == 0:
                if row['매매구분'] == '매수':
                    buf.append(row['날짜'])
            elif len(buf) == 1:
                if row['매매구분'] == '매도':
                    buf.append(row['날짜'])
                    duf_copy = deepcopy(buf)
                    dates.append(duf_copy)
                    buf.clear()
        return dates
            
    def making_mt_plot(self,
                    handle_data: 'pd.DataFrame',
                    code: 'str',
                    jounal: 'pd.DataFrame' = None):
        '''data plotting'''
        handle_data_copy = deepcopy(handle_data) 
        hd = handle_data_copy[handle_data_copy['코드'] == code]
        if jounal is not None:
            jounal_copy = deepcopy(jounal)
            dates = self.deduplication_dates(code=code, jounal=jounal_copy)
        # hd['날짜'] = hd['날짜'].apply(lambda x : datetime.strftime(x, '%Y-%m-%d'))  #for DB structure
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hd['날짜'], 
                                open=hd['시가'],
                                high=hd['최고가'],
                                low=hd['최저가'],
                                close=hd['종가']))
        fig.layout = dict(title='종목명: ' + str(hd['종목명'].unique()) + '  |  코드: ' + code, 
                        xaxis = dict(type="category", 
                        categoryorder='category ascending'))
        fig.update_xaxes(nticks=5)
        fig.update_layout(width=1000, height=500)
        for buy_date, sell_date in dates:
            print(buy_date, sell_date)
            fig.add_vrect(x0=buy_date, x1=sell_date, 
                        fillcolor="gray", opacity=0.25, line_width=0)
        return fig
    
    
        # def buy(self,
    #         df: 'pd.DataFrame',
    #         target: 'str'):
    #     '''asset 관리
    #     money 갱신만 실시
    #     위탁수수료 0.0140527%로 계산 ##선민이형 확인 필요'''
    #     hd = deepcopy(df)
        
    #     for (_, trg), group_df in hd.groupby(['날짜', target], sort=True):
    #         if trg == True:
    #             tot_price = 0
    #             for _, data in group_df.iterrows():
    #                 tot_price += data['종가'] * data['구매수량']
    #             if tot_price < self.MONEY:        
    #                 for _, data in group_df.iterrows():
    #                     inform = [data['날짜'],
    #                                 str(data['코드']).zfill(6),
    #                                 data['종가'],
    #                                 data['구매수량'],
    #                                 round(data['종가'] * data['구매수량'] * 0.00140527, 0),  
    #                                 '매수']
    #                     self.write_jounal(inform=inform)    
    #                     self.MONEY -= data['종가'] * data['구매수량'] + round(data['종가'] * data['구매수량'] * 0.00140527, 0)
    #                     self.upsert_asset(code=str(data['코드']).zfill(6), amount=data['구매수량'], sales_class='매수')
                        

    # def sell(self,
    #         df: 'pd.DataFrame',
    #         target: 'str'):
    #     '''asset 관리
    #     money 갱신만 실시
    #     위탁수수료 0.0140527%로 계산 ##선민이형 확인 필요'''
    #     hd = deepcopy(df)
    #     for (_, trg), group_df in hd.groupby(['날짜', target], sort=True):
    #         if trg == True:                
    #             for _, data in group_df.iterrows():
    #                 inform = [data['날짜'],
    #                             str(data['코드']).zfill(6),
    #                             data['종가'],
    #                             self.ASSET[str(data['코드']).zfill(6)],
    #                             round(data['종가'] * self.ASSET[str(data['코드']).zfill(6)] * 0.00140527, 0),  
    #                             '매도']
    #                 self.write_jounal(inform=inform)    
    #                 self.MONEY += data['종가'] * self.ASSET[str(data['코드']).zfill(6)] - round(data['종가'] * self.ASSET[str(data['코드']).zfill(6)] * 0.00140527, 0)
    #                 self.upsert_asset(code=str(data['코드']).zfill(6), amount=self.ASSET[str(data['코드']).zfill(6)], sales_class='매도')