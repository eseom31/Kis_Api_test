import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List
from copy import deepcopy
from datetime import datetime

class EconomicIndicators:
    def __init__(self):
        pass
    
    def day_revenue(self):
        '''날짜별 수익'''
        pass
    
    def month_revenue(self):
        '''월평균수익'''
        pass
    
    def quarter_revenue(self):
        '''분기별수익'''
        pass
    
    def year_revenue(self):
        '''년도별수익'''
        pass
    
    def calc_mdd(self, 
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

    def calc_sharp_index(self):
        '''샤프지수 계산'''
        pass
    
    def calc_winning_rate(self):
        '''승률 계산'''
        pass
    
    
    
class logSystem:
    def __init__(self):
        self.ECONO_INFORM = pd.DataFrame(columns=['날짜','매수총합','매도총합','매매비용','실현손익'])
        self.JOUNAL = pd.DataFrame(columns=['날짜', '종목코드', '체결단가', '체결수량', '매매비용', '매매구분'])
        self.ASSET_INFM = {}
        
    def upsert_asset_infm(self,
                    code,
                    amount,
                    sales_class,
                    price=None):
        if not code in self.ASSET_INFM.keys():  
            self.ASSET_INFM[code] = {'평단가': price, '수량': amount}
        elif sales_class == '매수':
            self.ASSET_INFM[code]['평단가'] = ((self.ASSET_INFM[code]['평단가'] * self.ASSET_INFM[code]['수량']) + (price * amount)) / (self.ASSET_INFM[code]['수량'] + amount)
            self.ASSET_INFM[code]['수량'] += amount
        else:
            self.ASSET_INFM[code]['수량'] -= amount
        self.ASSET_INFM = {key: val for key, val in self.ASSET_INFM.items() if val['수량'] != 0}
    
    def write_jounal(self, 
                    inform: 'List[pd.DatetimeIndex, str, int, int, int, str]'):
        '''BackTesting 클래스 내 존재하는 JOUNAL 속성에 일지를 작성합니다'''
        buf = {col: val for col, val in zip(self.JOUNAL.columns, inform)}
        self.JOUNAL = pd.concat([self.JOUNAL, pd.Series(buf).to_frame().T], ignore_index=True)
    
    def update_information(self):
        '''Jounal Data 전체를 이용하여 portfolio를 갱신합니다'''
        for date in self.JOUNAL['날짜'].unique():
            contents = self.JOUNAL[self.JOUNAL['날짜'] == date]
            tot_buy = contents[contents['매매구분']=='매수'][['체결단가', '체결수량']].apply(lambda x: x.prod(), axis=1).sum()
            tot_sell = contents[contents['매매구분']=='매도'][['체결단가', '체결수량']].apply(lambda x: x.prod(), axis=1).sum()
            deviation = contents[contents['매매구분']=='매도'].apply(lambda x: (x['체결단가'] * x['체결수량']) - (self.ASSET_INFM[x['종목코드']]['평단가'] * self.ASSET_INFM[x['종목코드']]['수량']), axis=1).sum()  
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
        
    def upsert_asset(self,
                code,
                amount,
                sales_class,
                price=None):
        if not code in self.ASSET.keys():  
            self.ASSET[code] = {'평단가': price, '수량': amount}
        elif sales_class == '매수':
            self.ASSET[code]['평단가'] = (self.ASSET[code]['평단가'] * self.ASSET[code]['수량']) + (price * amount) / (self.ASSET[code]['수량'] + amount)
            self.ASSET[code]['수량'] += amount
        else:
            self.ASSET[code]['수량'] -= amount
        self.ASSET = {key: val for key, val in self.ASSET.items() if val['수량'] != 0}

                    
    def buy_sell(self,
                df: 'pd.DataFrame',
                buy: 'str',
                sell: 'str'):
        hd = deepcopy(df)        
        for (day, buy, sell), group_df in hd.groupby(['날짜', buy, sell], sort=True):
            
                if sell == True:                
                    for _, data in group_df.iterrows():
                        if data['코드'] in self.ASSET:
                            inform = [data['날짜'],
                                    str(data['코드']).zfill(6),
                                    data['종가'],
                                    self.ASSET[str(data['코드']).zfill(6)]['수량'],
                                    round(data['종가'] * self.ASSET[str(data['코드']).zfill(6)]['수량'] * 0.00140527, 0),  
                                    '매도']
                            self.write_jounal(inform=inform)    
                            self.MONEY += data['종가'] * self.ASSET[str(data['코드']).zfill(6)]['수량'] - round(data['종가'] * self.ASSET[str(data['코드']).zfill(6)]['수량'] * 0.00140527, 0)
                            self.upsert_asset(code=str(data['코드']).zfill(6), amount=self.ASSET[str(data['코드']).zfill(6)]['수량'], sales_class='매도')     
                if buy == True:
                    tot_price = 0
                    for _, data in group_df.iterrows():
                        tot_price += data['종가'] * data['구매수량']
                    if tot_price < self.MONEY:        
                        for _, data in group_df.iterrows():
                            inform = [data['날짜'],
                                    str(data['코드']).zfill(6),
                                    data['종가'],
                                    data['구매수량'],
                                    round(data['종가'] * data['구매수량'] * 0.00140527, 0),  
                                    '매수']
                            self.write_jounal(inform=inform)    
                            self.MONEY -= data['종가'] * data['구매수량'] + round(data['종가'] * data['구매수량'] * 0.00140527, 0)
                            self.upsert_asset(code=str(data['코드']).zfill(6), amount=data['구매수량'], sales_class='매수', price=data['종가'])       
            
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
            if len(buf) == 2:
                duf_copy = deepcopy(buf)
                dates.append(duf_copy)
                buf.clear()
            if not buf:
                if row['매매구분'] == '매수':
                    buf.append(row['날짜'])
            if row['매매구분'] == '매도':
                buf.append(row['날짜'])
        return dates
            
    def making_mt_plot(self,
                    handle_data: 'pd.DataFrame',
                    code: 'str',
                    jounal: 'pd.DataFrame' = None):
        '''data plotting'''
        handle_data_copy = deepcopy(handle_data) 
        hd = handle_data_copy[handle_data_copy['코드'] == code]
        jounal_copy = deepcopy(jounal)
        dates = self.deduplication_dates(code=code, jounal=jounal_copy)
        # hd['날짜'] = hd['날짜'].apply(lambda x : datetime.strftime(x, '%Y-%m-%d'))
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