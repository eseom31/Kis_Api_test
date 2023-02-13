import pandas as pd
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
    
    
    
class BackTesting:
    def __init__(self):
        self.portfolio = pd.DataFrame(columns=['날짜','매수총합','매도총합','매매비용','실현손익'])
        self.jounal = pd.DataFrame(columns=['날짜', '종목코드', '체결단가', '체결수량', '매매비용', '매매구분'])
        self.asset = 0
        
    def buy(self,
            handle_data: 'pd.DataFrame'):
        '''handle_data를 활용해 BackTesting 클래스 내 존재하는 jounal 속성에 일지를 작성합니다'''
        hd = deepcopy(handle_data)
        res = hd[hd['condition'] == True]
        self.jounal['날짜'] = res['날짜']
        self.jounal['종목코드'] = res['코드']
        self.jounal['체결단가'] = res['종가']
        self.jounal['체결수량'] = 1
        self.jounal['매매비용'] = 0
        self.jounal['매매구분'] = '매수'
        
    
    def sell(self):
        pass
    
    def update_portfolio(self):
        for date in self.jounal['날짜'].unique():
            contents = self.jounal[self.jounal['날짜'] == date]
            buf = pd.Series({
                '날짜': date,
                '매수총합': contents[contents['매매구분']=='매수']['체결단가'].sum(),
                '매도총합': contents[contents['매매구분']=='매도']['체결단가'].sum(),
                '매매비용': contents['매매비용'].sum(),
                '실현손익': contents[contents['매매구분']=='매수']['체결단가'].sum() - contents[contents['매매구분']=='매도']['체결단가'].sum()})
            self.portfolio = pd.concat([self.portfolio, buf.to_frame().T], ignore_index=True)
    
    
class Utls():
    def __init__(self):
        pass
    
    def plot(self):
        '''data plotting'''
        pass