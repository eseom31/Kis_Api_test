import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List
from copy import deepcopy

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
            deviation = tot_sell - tot_buy
            buf = pd.Series({
                '날짜': date,
                '매수총합': tot_buy,
                '매도총합': tot_sell,
                '매매비용': contents['매매비용'].sum(),
                '실현손익': deviation if deviation > 0 else 0})
            self.ECONO_INFORM = pd.concat([self.ECONO_INFORM, buf.to_frame().T], ignore_index=True)

class BackTesting(logSystem):
    def __init__(self):
        super().__init__()
        self.ASSET = {}
        self.MONEY = 0
    
    def upsert_asset(self,
                    code,
                    amount,
                    sales_class):
        if not code in self.ASSET.keys():  
            self.ASSET[code] = amount
        elif sales_class == '매수':
            self.ASSET[code] += amount
        else:
            self.ASSET[code] -= amount
        self.ASSET = {key: val for key, val in self.ASSET.items() if val != 0}
        ##만약 남은 개수 0이면 목록에서 삭제프로그램 추가해야함
            
    def buy(self,
            df: 'pd.DataFrame',
            target: 'str'):
        '''asset 관리
        money 갱신만 실시
        위탁수수료 0.0140527%로 계산 ##선민이형 확인 필요'''
        hd = deepcopy(df)
        tot_price = 0
        for (_, trg), group_df in hd.groupby(['날짜', target], sort=True):
            if trg == True:
                for _, data in group_df.iterrows():
                    tot_price += data['종가'] * data['구매수량']
                if tot_price < self.MONEY:        
                    for _, data in group_df.iterrows():
                        inform = [data['날짜'],
                                    data['코드'],
                                    data['종가'],
                                    data['구매수량'],
                                    round(data['종가'] * data['구매수량'] * 0.00140527, 0),  
                                    '매수']
                        self.write_jounal(inform=inform)    
                        self.MONEY -= data['종가'] * data['구매수량']
                        self.upsert_asset(code=data['코드'], amount=data['구매수량'], sales_class='매수')
                        
    
    def sell(self,
            df: 'pd.DataFrame',
            target: 'str'):
        '''asset 관리
        money 갱신만 실시
        위탁수수료 0.0140527%로 계산 ##선민이형 확인 필요'''
        hd = deepcopy(df)
        for (_, trg), group_df in hd.groupby(['날짜', target], sort=True):
            if trg == True:                
                for _, data in group_df.iterrows():
                    inform = [data['날짜'],
                                data['코드'],
                                data['종가'],
                                self.ASSET[data['코드']],
                                round(data['종가'] * self.ASSET[data['코드']] * 0.00140527, 0),  
                                '매도']
                    self.write_jounal(inform=inform)    
                    self.MONEY += data['종가'] * self.ASSET[data['코드']]
                    self.upsert_asset(code=data['코드'], amount=self.ASSET[data['코드']], sales_class='매도')
                    
            
    
class Utils:
    def __init__(self):
        pass
    
    def making_mt_plot(self,
                    handle_data: 'pd.DataFrame',
                    code: 'str',
                    jounal: 'pd.DataFrame' = None):
        '''data plotting'''
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=handle_data['날짜'], 
                                y=handle_data[handle_data['코드'] == code]['종가'],
                                mode='markers',
                                name='종가'))
        return fig