exec(open('01_main_analysis.py').read().split('res = {}')[0])
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files); conf = win[win.confirmed]
C = cube(conf, REG, cl)
di = {k:list(ALLDAYS).index(pd.Timestamp(k)) for k in ['2024-01-06','2024-01-11','2024-01-12','2024-01-13','2024-01-14','2024-01-18']}
base = slice(di['2024-01-06'], di['2024-01-11']+1)
def ratio(idx, sl):
    t = sum(C[w][idx[w]][:, sl].sum() for w in TREAT); c = sum(C[w][idx[w]][:, sl].sum() for w in CTRL)
    return t/c
full = {w: np.arange(len(cl[w])) for w in REG}
wins = {'day0 (1.12)': slice(di['2024-01-12'], di['2024-01-12']+1), 'day1 (1.13)': slice(di['2024-01-13'], di['2024-01-13']+1),
        '1.12-1.14': slice(di['2024-01-12'], di['2024-01-14']+1), '1.13-1.19': slice(di['2024-01-13'], di['2024-01-18']+2)}
b0 = ratio(full, base)
rng2 = np.random.default_rng(7)
for name, sl in wins.items():
    est = ratio(full, sl)/b0
    bs=[]
    for _ in range(999):
        idx={w: rng2.integers(0,len(cl[w]),len(cl[w])) for w in REG}
        bs.append(ratio(idx, sl)/ratio(idx, base))
    print(name, round(est,2), np.round(np.percentile(bs,[2.5,97.5]),2))
