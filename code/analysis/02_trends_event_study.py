exec(open('01_main_analysis.py').read().split("res = {}")[0])
import statsmodels.api as sm
class TrendModel(Model):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        days = ALLDAYS[self.mask]; t = np.tile(np.arange(len(days)) / len(days), len(self.worlds)); W = np.repeat(self.worlds, len(days))
        for w in self.worlds[1:]: self.X[f'tr_{w}'] = (W == w) * t
out = {}
d, win, cl = load(glob.glob(U + 'maple_main_v4/records_*.csv') + glob.glob(U + 'maple_main_v5/records_2026-10-28_*.csv'))
conf = win[win.confirmed]; C = cube(conf, REG + REBOOT, cl)
m = Model(C, cl, TREAT + LARGE, TREAT, L1, [L1]); out['es_vs_large'] = dict(bins=[int(b) for b in m.bins], est=m.run(999))
SMALL = [w for w in CTRL if w not in LARGE]
m = Model(C, cl, TREAT + SMALL, TREAT, L1, [L1]); out['es_vs_small'] = dict(bins=[int(b) for b in m.bins], est=m.run(999))
out['main_trend'] = TrendModel(C, cl, REG, {'D': TREAT}, L1, [L1]).run(999)
out['reboot_trend'] = TrendModel(C, cl, REBOOT + CTRL, {'D': REBOOT}, L2, [L1, L2]).run(999)
# pre-period dynamics: share of small-world creations in leaf-event window vs after
out['leaf_window_main'] = Model(C, cl, REG, {'D': TREAT}, L1, list(pd.date_range('2023-12-21', '2024-01-04')) + [L1]).run(999)
print(json.dumps(out, ensure_ascii=False, default=float, indent=0))
json.dump(out, open(OUTD + 'results_v5b.json', 'w'), ensure_ascii=False, default=float)
