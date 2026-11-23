exec(open('01_main_analysis.py').read().split('res = {}')[0])
import math
files = glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv')
d, win, cl = load(files)
out = {}
# --- 1) sample flow (regular worlds), by period
w = win[win.world.isin(REG)].copy()
wf = w.world_first_seen.fillna('').replace(ALIAS)
w['reason'] = np.select(
    [wf == '', wf.str.startswith('버닝'), w.date_first_seen.fillna('9') >= '2024-02-22', wf != w.world],
    ['no_history', 'burning_first', 'seen_after_leaf', 'moved_later'], 'confirmed')
w['period'] = np.where(w.dc < L1, 'pre', np.where(w.dc == L1, 'lift_day', 'post'))
w['grp'] = np.where(w.world.isin(TREAT), 'treat', np.where(w.world.isin(LARGE), 'large', 'small'))
tab = pd.crosstab([w.grp, w.period], w.reason)
print(tab); out['flow'] = {str(k): v for k, v in tab.to_dict(orient='index').items()}
rate = w.groupby(['grp','period']).apply(lambda g: (g.reason=='confirmed').mean())
print(rate); out['conf_rate'] = {str(k): float(v) for k, v in rate.items()}
# confirmation rate DID check: logit-ish simple diff
# --- 2) relaxed confirmation: first-seen general world before 2/22, regardless of current world
REGSET = set(REG + REBOOT)
wf_all = win.world_first_seen.fillna('').replace(ALIAS)
relax = win[(wf_all.isin(REGSET)) & (win.date_first_seen.fillna('9') < '2024-02-22')].copy()
relax['world'] = wf_all[relax.index]   # assign to world where first seen
C2 = cube(relax, REG + REBOOT, {**cl})
out['relaxed_main'] = Model(C2, cl, REG, {'D': TREAT}, L1, [L1]).run(999)
print('relaxed', out['relaxed_main'], len(relax[relax.world.isin(REG)]))
# --- 3) Jan-25 split
conf = win[win.confirmed]
C = cube(conf, REG + REBOOT, cl)
class Split(Model):
    pass
m = Model(C, cl, REG, {'D': TREAT}, L1, [L1])
T = pd.Series(np.tile(ALLDAYS[m.mask], len(REG))); W = np.repeat(REG, m.mask.sum())
X = m.X.drop(columns=['D']).copy()
tr = np.isin(W, TREAT)
X['D_early'] = (tr & (T > L1) & (T < L2)).values.astype(float)
X['D_late'] = (tr & (T >= L2)).values.astype(float)
def fitsplit(idx=None):
    return sm.GLM(m.y(idx), X, family=sm.families.Poisson()).fit().params[['D_early','D_late']].values
est = fitsplit(); bs = np.array([fitsplit({w_: rng.integers(0, len(cl[w_]), len(cl[w_])) for w_ in REG}) for _ in range(999)])
out['split'] = {n: dict(b=float(est[j]), lo=float(np.percentile(bs[:,j],2.5)), hi=float(np.percentile(bs[:,j],97.5)), p=float(min(1.0, 2*min((bs[:,j]<=0).mean(), (bs[:,j]>=0).mean()))), se=float(bs[:,j].std(ddof=1))) for j,n in enumerate(['D_early','D_late'])}
print('split', {k:(round(math.exp(v['b']),3),round(math.exp(v['lo']),3),round(math.exp(v['hi']),3)) for k,v in out['split'].items()})
# window ending 1/24
drop = [L1] + list(ALLDAYS[ALLDAYS >= L2])
out['pre_0125'] = Model(C, cl, REG, {'D': TREAT}, L1, drop).run(999)
print('pre_0125', out['pre_0125'])
# --- 4) permutation two-sided & studentized-free
vals = {}
for pair in itertools.combinations(REG, 2):
    vals[pair] = float(Model(C, cl, REG, {'D': list(pair)}, L1, [L1]).fit()[0])
a = vals[tuple(TREAT)]
out['perm_one'] = sum(v >= a for v in vals.values()) / len(vals)
out['perm_two'] = sum(abs(v) >= abs(a) for v in vals.values()) / len(vals)
big = ['스카니아','루나','엘리시움','크로아','베라','오로라']
sub = {p: v for p, v in vals.items() if p[0] in big and p[1] in big}
out['perm_large6'] = dict(rank=sum(v >= a for v in sub.values()), n=len(sub))
print('perm', out['perm_one'], out['perm_two'], out['perm_large6'])
# --- 5) absolute extra (sample units): treated post obs vs counterfactual
for t in TREAT:
    r_ = Model(C, cl, [t] + CTRL, {'D': [t]}, L1, [L1]).fit()[0]
    post_obs = C[t].sum(0)[ALLDAYS > L1].sum(); pre_obs = C[t].sum(0)[ALLDAYS < L1].sum()
    out['abs_' + t] = dict(irr=float(math.exp(r_)), post_obs=int(post_obs), pre_obs=int(pre_obs), extra=float(post_obs * (1 - math.exp(-r_))), clusters=len(cl[t]))
    print(t, out['abs_' + t])
json.dump(out, open(OUTD + 'results_review.json', 'w'), ensure_ascii=False, indent=1, default=float)
