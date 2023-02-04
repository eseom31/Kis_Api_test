import pandas as pd

class EconomicIndicators:
    def __init__(self):
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

class Utls():
    def __init__(self):
        pass
    
    def plot(self):
        '''data plotting'''
        pass
    