# crypto_calibration.py
BINS = [(60,0.58),(70,0.62),(80,0.67),(88,0.72),(93,0.75),(97,0.78),(99,0.80)]

def prob_from_score(score:int)->float:
    B = BINS
    if score <= B[0][0]: return B[0][1]
    for i in range(1, len(B)):
        if score <= B[i][0]:
            s0,p0 = B[i-1]; s1,p1 = B[i]
            w = (score - s0)/(s1 - s0)
            return p0 + w*(p1 - p0)
    return B[-1][1]

def expectancy(p_win:float, rr:float)->float:
    return p_win*rr - (1.0 - p_win)*1.0