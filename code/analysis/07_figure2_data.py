import pandas as pd, numpy as np, glob, json
exec(open('01_main_analysis.py').read().split('def cube')[0])
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files); c = win[win.confirmed & win.world.isin(REG) & (win.dc != L1)].copy()
rel = (c.dc - (L1 + pd.Timedelta(days=1))).dt.days
c['bin'] = np.maximum(np.where(rel >= 0, rel // 7, -((-rel - 1) // 7) - 1), -3)
c['grp'] = np.where(c.world.isin(TREAT), 'T', 'C')
days = pd.Series(ALLDAYS[ALLDAYS != L1]); r = (days - (L1 + pd.Timedelta(days=1))).dt.days
nd = pd.Series(np.maximum(np.where(r >= 0, r // 7, -((-r - 1) // 7) - 1), -3)).value_counts().sort_index()
t = c.groupby(['bin', 'grp']).size().unstack().reindex(nd.index).div(nd, axis=0)
idx = t / t.loc[-1] * 100
out = pd.DataFrame({'n_days': nd, 'T_perday': t['T'].round(2), 'C_perday': t['C'].round(2), 'T_idx': idx['T'].round(1), 'C_idx': idx['C'].round(1), 'ratio': (idx['T'] / idx['C']).round(3)})
print(out); print('n', len(c), c.grp.value_counts().to_dict())
out.to_json('fig2.json', orient='index')
