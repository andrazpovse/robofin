from enum import Enum


class RiskTollerance(Enum):
    """ 
        If a person scores 'High' on RiskTollerance, it means he/she does like to 
        take risks and thus accepts higher volatility.
    """
    VeryLow = 1
    Low = 2
    Medium = 3
    High = 4
    VeryHigh = 5
    Extreme = 6

class Risk:
    """
        Risk class contains risk profile based on risk score, which is proveded by completing the survey.

        It limits some metrics like maximum volatility and maximum amount of cash in portfolio.
    """
    def __init__(self, score):
        self.score = score
        
        data = self.get_risk_profile(score)

        self.risk_tollerance = data['risk_tollerance']
        self.cagr_target = data['cagr_target']
        self.max_volatility = data['max_volatility']
        self.max_drawdown = data['max_drawdown']
        self.max_cash = data['max_cash']
        self.allowed_tactical_change = data['allowed_tactical_change']
        self.max_crypto = data['max_crypto']

    def scale(self, val, src, dst):
        """
            Scale the given value from the scale of src to the scale of dst.
        """
        return (((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0])


    def get_risk_profile(self, score):
        data = {}
        # TODO; kako vem da je to dober score, kako dolocit te utezi, nas predlog, pregled literature,
        # backtesting, evalvacija  na vec korakih. Ali splogh so razlike? Ali so vsi isti outputi ne glede na input
        # pokazemo da upostevamo neke razlike, da so portfelji razlinci glede na uporanbika.

        # TODO izvedemo neko simulacijo ki vsebuje vse score in rezultate, ki jih dobimo. Tako 
        # lahko pokazemo, da so meje smiselne glede na prejete metrike.

        

        if score < 6:
            raise Exception('Risk score provided is {x}, but it can not be below 7.'.format(x=score)) 
        if 6 <= score <= 14:
            data['risk_tollerance'] = RiskTollerance.VeryLow
            # 2-3% cagr
            data['cagr_target'] = self.scale(score, (6,14), (2,3)) / 100
            data['max_volatility'] = self.scale(score, (6,14), (0.04, 0.06))
            data['max_drawdown'] = -0.1
            data['max_cash'] = 0.0
            # spremeni na malo visje, eksponentno raste tacitcal change
            data['allowed_tactical_change'] = self.scale(score, (6,14), (0.02, 0.03))
            data['max_crypto'] = self.scale(score, (6,14), (0.01, 0.03))
        elif 14 < score <= 25:
            data['risk_tollerance'] = RiskTollerance.Low
            # 3-5% cagr
            data['cagr_target'] = self.scale(score, (15,25), (3,5)) / 100
            data['max_volatility'] = self.scale(score, (15,25), (0.06,0.09))
            data['max_drawdown'] = -0.15
            data['max_cash'] = 0.0
            data['allowed_tactical_change'] = self.scale(score, (15,25), (0.03,0.05))
            data['max_crypto'] = self.scale(score, (15,25), (0.03, 0.05))
        elif 25 < score <= 40:
            data['risk_tollerance'] = RiskTollerance.Medium
            # 5-8% cagr
            data['cagr_target'] = self.scale(score, (26,40), (5,8)) / 100
            data['max_volatility'] = self.scale(score, (26,40), (0.09,0.15))
            data['max_drawdown'] = -0.2
            data['max_cash'] = 0.0
            data['allowed_tactical_change'] = self.scale(score, (26,40), (0.05,0.15))
            data['max_crypto'] = self.scale(score, (26,40), (0.05, 0.1))
        elif 40 < score <= 55:
            data['risk_tollerance'] = RiskTollerance.High
            # 9-10% cagr
            data['cagr_target'] = self.scale(score, (40,55), (9,10)) / 100
            data['max_volatility'] = self.scale(score, (40,55), (0.15,0.22))
            data['max_drawdown'] = -0.35
            data['max_cash'] = 0
            data['allowed_tactical_change'] = self.scale(score, (40,55), (0.15,0.25))
            data['max_crypto'] = self.scale(score, (40,55), (0.1, 0.15))
        elif 55 < score <= 60:
            data['risk_tollerance'] = RiskTollerance.VeryHigh
            data['cagr_target'] = self.scale(score, (55,60), (10,25)) / 100
            data['max_volatility'] = self.scale(score, (55,60), (0.22,0.3))
            data['max_drawdown'] = -0.5
            data['max_cash'] = 0
            data['allowed_tactical_change'] = self.scale(score, (56,60), (0.25,0.45))
            data['max_crypto'] = self.scale(score, (55,60), (0.15, 0.60))
        elif 60 < score:
            # Extreme Risk PF
            data['risk_tollerance'] = RiskTollerance.Extreme
            data['cagr_target'] = self.scale(score, (60,63), (25,40)) / 100
            data['max_volatility'] = self.scale(score, (60,63), (0.4,0.6))
            data['max_drawdown'] = -0.8
            data['max_cash'] = 0
            data['allowed_tactical_change'] = 1
            data['max_crypto'] = 1
        return data
