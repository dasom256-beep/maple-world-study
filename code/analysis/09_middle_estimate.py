exec(open('01_main_analysis.py').read().split('res = {}')[0])
import json
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files)
w = win[win.world.isin(REG)].copy()
w['grp'] = np.where(w.world.isin(TREAT), 'T', 'C')
# creation week: 7-day bins anchored on the lift (same scheme as the event study)
rel = (w.dc - (L1 + pd.Timedelta(days=1))).dt.days
w['wk'] = np.where(rel >= 0, rel // 7, -((-rel - 1) // 7) - 1)
w.loc[w.dc == L1, 'wk'] = 99   # lift day: own cell (dropped from estimation anyway)
r = w.groupby(['wk', 'grp']).confirmed.agg(['sum', 'count']).unstack()
conf_t, n_t = r[('sum', 'T')], r[('count', 'T')]; conf_c, n_c = r[('sum', 'C')], r[('count', 'C')]
uc_rate_c = 1 - conf_c / n_c                      # comparison-world unconfirmed share by week
unc_t = n_t - conf_t
keep = (uc_rate_c / (1 - uc_rate_c) * conf_t / unc_t).clip(upper=1.0)   # share of treated unconfirmed to keep
print(pd.DataFrame({'treated_unconf_share': (unc_t / n_t).round(3), 'comp_unconf_share': uc_rate_c.round(3), 'keep_frac': keep.round(3)}))
w['wt'] = 1.0
m = (w.grp == 'T') & ~w.confirmed
w.loc[m, 'wt'] = w.loc[m, 'wk'].map(keep).values
def wcube(sample, worlds, clusters):
    return {x: sample[sample.world == x].pivot_table(index='cluster', columns='dc', values='wt', aggfunc='sum').reindex(index=clusters[x], columns=ALLDAYS, fill_value=0).fillna(0).values for x in worlds}
C = wcube(w, REG, cl)
res = Model(C, cl, REG, {'D': TREAT}, L1, [L1]).run(999)
e = {k: round(float(np.exp(v)), 3) for k, v in res['D'].items() if k in ('b', 'lo', 'hi')}
print('middle estimate', e, 'p', res['D']['p'])
pm = perm(C, cl, REG, TREAT, L1, [L1]); print('perm', {k: pm[k] for k in ('rank', 'n', 'p')})
json.dump({'middle': res, 'keep': keep.to_dict(), 'perm': {k: pm[k] for k in ('rank', 'n', 'p')}}, open(OUTD + 'results_middle.json', 'w'), default=float, indent=1)
