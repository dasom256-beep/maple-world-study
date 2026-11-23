exec(open('01_main_analysis.py').read().split("res = {}")[0])
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files)
w = win[win.world.isin(REG)].copy()
w['grp'] = np.where(w.world.isin(TREAT), 'treat', np.where(w.world.isin(LARGE), 'large', 'small'))
wf = w.world_first_seen.fillna('').replace(ALIAS)
w['cat'] = np.select([w.confirmed, wf == '', w.date_first_seen.fillna('9') >= '2024-02-22'], ['conf', 'nohist', 'late'], 'other')
rel = (w.dc - (L1 + pd.Timedelta(days=1))).dt.days
k = np.where(rel >= 0, rel // 7, -((-rel - 1) // 7) - 1); k = np.maximum(k, -3); k[w.dc == L1] = 99
w['wk'] = k
t = w.groupby(['wk', 'grp']).cat.value_counts().unstack(fill_value=0)
t['n'] = t.sum(1); t['nohist%'] = (100 * t.nohist / t.n).round(1); t['late%'] = (100 * t.late / t.n).round(1); t['conf%'] = (100 * t.conf / t.n).round(1)
print(t[['n', 'conf%', 'nohist%', 'late%']].unstack('grp').to_string())
c = w[w.confirmed].copy(); c['lag'] = (pd.to_datetime(c.date_first_seen) - c.dc).dt.days
print('lag dist confirmed (%):', (c.lag.value_counts(normalize=True).sort_index().head(8) * 100).round(1).to_dict())
print('lag by grp share lag==1:', c.groupby('grp').lag.apply(lambda s: round(100 * (s == 1).mean(), 1)).to_dict())
print('lag median/90pct by grp:', c.groupby('grp').lag.describe(percentiles=[.5, .9])[['50%', '90%', 'max']].to_dict())
nh = w[w.cat == 'nohist']
print('nohist level band now (top):', nh.groupby('grp').level_band_now.agg(lambda s: s.value_counts().head(3).to_dict()).to_dict())
print('nohist creation weekday share in week -3 (12.21-29):', nh.groupby('grp').apply(lambda g: round(100 * (g.wk == -3).mean(), 1)).to_dict())
print('first_seen_world values (non-empty, non-current):', (wf[(wf != '') & (wf != w.world)]).value_counts().head().to_dict())
# aggregate ratio check
pre = (w.dc < L1); post = (w.dc > L1)
def rate(g, m): s = w[(w.grp.isin(g)) & m]; return s.confirmed.mean()
ct, cc = [rate(['treat'], pre), rate(['treat'], post)], [rate(['large', 'small'], pre), rate(['large', 'small'], post)]
print('conf rates treat pre/post', ct, 'ctrl pre/post', cc, 'ratio', (ct[1] / ct[0]) / (cc[1] / cc[0]))
lt = w[w.cat == 'late'].copy(); lt['lag'] = (pd.to_datetime(lt.date_first_seen) - lt.dc).dt.days
print('late n', len(lt), 'created 2.21 share', round((lt.dc == END).mean() * 100, 1))
x = lt[lt.dc < END]
print('late excl 2.21 lag pct:', x.lag.describe(percentiles=[.1, .5, .9]).round(0).to_dict())
print('late first seen date min/mode:', x.date_first_seen.min(), x.date_first_seen.value_counts().head(3).to_dict())
print('created 2.21: n', (w.dc == END).sum(), 'late share by grp', w[w.dc == END].groupby('grp').apply(lambda g: round(100 * (g.cat == 'late').mean(), 1)).to_dict())
