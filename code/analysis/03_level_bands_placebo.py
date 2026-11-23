exec(open('01_main_analysis.py').read().split('res = {}')[0])
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files); conf = win[win.confirmed].copy()
conf['lv'] = conf.level_band_now.str.split('-').str[0].astype(float)
res = {}
# 1) level bands
bands = {'lt200': conf.lv < 200, 'b200_209': (conf.lv >= 200) & (conf.lv < 210), 'ge210': conf.lv >= 210, 'ge260': conf.lv >= 260}
for k, m in bands.items():
    C = cube(conf[m], REG, cl)
    res['band_' + k] = Model(C, cl, REG, {'D': TREAT}, L1, [L1]).run(999)
    res['band_' + k]['n'] = int((m & conf.world.isin(REG) & (conf.dc != L1)).sum())
    print(k, res['band_' + k], flush=True)
# 2) placebo lift dates, pre-period only
C = cube(conf, REG, cl)
pre_drop = list(ALLDAYS[ALLDAYS >= L1])
for fake in ['2023-12-28', '2023-12-31', '2024-01-04']:
    res['placebo_' + fake] = Model(C, cl, REG, {'D': TREAT}, pd.Timestamp(fake), pre_drop).run(999)
    print('placebo', fake, res['placebo_' + fake], flush=True)
# 3) world-clustered SE for main model
m = Model(C, cl, REG, {'D': TREAT}, L1, [L1])
groups = np.repeat(np.arange(len(REG)), m.mask.sum())
for use_t in [False, True]:
    f = sm.GLM(m.y(), m.X, family=sm.families.Poisson()).fit(cov_type='cluster', cov_kwds={'groups': groups}, use_t=use_t)
    lo, hi = f.conf_int().loc['D']
    res[f'cluster_world_t{int(use_t)}'] = dict(b=float(f.params['D']), lo=float(lo), hi=float(hi), p=float(f.pvalues['D']), se=float(f.bse['D']))
    print('cluster', use_t, res[f'cluster_world_t{int(use_t)}'], flush=True)
json.dump(res, open(OUTD + 'results_v5c.json', 'w'), ensure_ascii=False, indent=1, default=float)
print('DONE')
