import os
import pandas as pd, numpy as np, json, glob, itertools, warnings
import statsmodels.api as sm
warnings.filterwarnings('ignore')
rng = np.random.default_rng(2026)
OUTD = os.environ.get('MAPLE_OUT', './')
U = os.environ.get('MAPLE_DATA', './data/')
ALIAS = {'리부트': '에오스', '리부트2': '핼리오스'}
REG = ['스카니아', '루나', '엘리시움', '크로아', '베라', '제니스', '유니온', '이노시스', '레드', '오로라', '아케인', '노바']
TREAT = ['스카니아', '루나']; REBOOT = ['에오스', '핼리오스']; LARGE = ['엘리시움', '크로아']
CTRL = [w for w in REG if w not in TREAT]
START, END = pd.Timestamp('2023-12-21'), pd.Timestamp('2024-02-21')
L1, L2 = pd.Timestamp('2024-01-12'), pd.Timestamp('2024-01-25')
ALLDAYS = pd.date_range(START, END)

def load(files):
    d = pd.concat([pd.read_csv(f, dtype=str) for f in files], ignore_index=True)
    ok = d[d.status == 'ok'].copy(); ok['dc'] = pd.to_datetime(ok.date_create)
    win = ok[(ok.dc >= START) & (ok.dc <= END)].copy()
    wf = win.world_first_seen.fillna('').replace(ALIAS)
    win['confirmed'] = (wf != '') & ~wf.str.startswith('버닝') & (win.date_first_seen.fillna('9') < '2024-02-22') & (wf == win.world)
    clusters = {w: sorted(d.loc[d.world == w, 'cluster'].unique()) for w in d.world.unique()}
    return d, win, clusters

def cube(sample, worlds, clusters):
    return {w: pd.crosstab(sample[sample.world == w].cluster, sample[sample.world == w].dc).reindex(index=clusters[w], columns=ALLDAYS, fill_value=0).values for w in worlds}

class Model:
    def __init__(self, c, clusters, worlds, terms, lift, drop, kmin=-3):
        self.c, self.cl, self.worlds, self.terms = c, clusters, worlds, terms
        self.mask = ~ALLDAYS.isin(drop); days = ALLDAYS[self.mask]
        W = np.repeat(worlds, len(days)); T = pd.Series(np.tile(days, len(worlds)))
        X = pd.get_dummies(pd.Series(W), prefix='w', drop_first=True, dtype=float).join(pd.get_dummies(T.dt.strftime('%m%d'), prefix='d', drop_first=True, dtype=float))
        if isinstance(terms, dict):
            post = (T > lift).values.astype(float)
            for k, g in terms.items(): X[k] = np.isin(W, g) * post
            self.names = list(terms)
        else:   # event study: terms = treated list; weekly bins relative to lift+1
            rel = (T - (lift + pd.Timedelta(days=1))).dt.days.values
            k = np.maximum(np.where(rel >= 0, rel // 7, -((-rel - 1) // 7) - 1), kmin)   # -1 = 7 days before; earliest bin pooled
            self.bins = [b for b in sorted(set(k)) if b != -1]
            tr = np.isin(W, terms)
            for b in self.bins: X[f'E{b}'] = (tr & (k == b)).astype(float)
            self.names = [f'E{b}' for b in self.bins]
        self.X = sm.add_constant(X)
    def y(self, idx=None):
        return np.concatenate([(self.c[w] if idx is None else self.c[w][idx[w]]).sum(0)[self.mask] for w in self.worlds])
    def fit(self, idx=None):
        return sm.GLM(self.y(idx), self.X, family=sm.families.Poisson()).fit().params[self.names].values
    def run(self, B=999):
        est = self.fit(); bs = np.array([self.fit({w: rng.integers(0, len(self.cl[w]), len(self.cl[w])) for w in self.worlds}) for _ in range(B)])
        return {n: dict(b=float(est[j]), lo=float(np.percentile(bs[:, j], 2.5)), hi=float(np.percentile(bs[:, j], 97.5)), p=float(min(1.0, 2 * min((bs[:, j] <= 0).mean(), (bs[:, j] >= 0).mean()))), se=float(bs[:, j].std(ddof=1))) for j, n in enumerate(self.names)}

def perm(c, clusters, worlds, actual_pair, lift, drop):
    vals = {}
    for pair in itertools.combinations(worlds, 2):
        vals['|'.join(pair)] = float(Model(c, clusters, worlds, {'D': list(pair)}, lift, drop).fit()[0])
    a = vals['|'.join(actual_pair)]; rank = sum(v >= a for v in vals.values())
    return dict(actual=a, rank=rank, n=len(vals), p=rank / len(vals))

res = {}
samples = {
    'recent': glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv'),
    'early': glob.glob(U + 'maple_main_v5/records_2024-11-06_*.csv'),
}
for sname, files in samples.items():
    d, win, cl = load(files); conf = win[win.confirmed]
    R = res[sname] = {'n_records': len(d), 'n_window': len(win), 'n_confirmed': int(win.confirmed.sum()),
                      'by_world': conf.groupby('world').size().to_dict()}
    C = cube(conf, REG + REBOOT, cl)
    R['main'] = Model(C, cl, REG, {'D': TREAT}, L1, [L1]).run(999)
    R['subst'] = Model(C, cl, REG, {'D': TREAT, 'L': LARGE}, L1, [L1]).run()
    R['subst_bera'] = Model(C, cl, REG, {'D': TREAT, 'L': LARGE + ['베라']}, L1, [L1]).run()
    R['reboot'] = Model(C, cl, REBOOT + CTRL, {'D': REBOOT}, L2, [L1, L2]).run()
    R['perm_main'] = perm(C, cl, REG, TREAT, L1, [L1])
    R['perm_reboot'] = perm(C, cl, REBOOT + CTRL, REBOOT, L2, [L1, L2])
    print(sname, {k: R[k] for k in ['n_window', 'n_confirmed', 'main', 'subst', 'reboot', 'perm_main', 'perm_reboot']}, flush=True)
    if sname == 'recent':
        for t in TREAT:
            R[f'only_{t}'] = Model(C, cl, [t] + CTRL, {'D': [t]}, L1, [L1]).run()
        R['vs_small'] = Model(C, cl, TREAT + [w for w in CTRL if w not in LARGE], {'D': TREAT}, L1, [L1]).run()
        R['vs_large'] = Model(C, cl, TREAT + LARGE, {'D': TREAT}, L1, [L1]).run()
        Ca = cube(win[win.world.isin(REG + REBOOT)], REG + REBOOT, cl)
        R['all_main'] = Model(Ca, cl, REG, {'D': TREAT}, L1, [L1]).run()
        R['all_reboot'] = Model(Ca, cl, REBOOT + CTRL, {'D': REBOOT}, L2, [L1, L2]).run()
        m = Model(C, cl, REG, TREAT, L1, [L1]); R['es_main'] = {'bins': m.bins, 'est': m.run()}
        m2 = Model(C, cl, REBOOT + CTRL, REBOOT, L2, [L1, L2], kmin=-5); R['es_reboot'] = {'bins': m2.bins, 'est': m2.run()}
        print('extra', {k: R[k] for k in ['only_스카니아', 'only_루나', 'vs_small', 'vs_large', 'all_main', 'all_reboot']}, flush=True)
        print('es_main', R['es_main'], flush=True); print('es_reboot', R['es_reboot'], flush=True)
json.dump(res, open(OUTD + 'results_v5.json', 'w'), ensure_ascii=False, indent=1, default=float)
print('DONE')
