import json, math
from statistics import NormalDist
J = lambda f: json.load(open(f))
v5, v5b, v5c, rv = J('results_v5.json'), J('results_v5b.json'), J('results_v5c.json'), J('results_review.json')
R, E = v5['recent'], v5['early']
def st(p): return '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
def fp(p): return '<0.001' if p < 0.001 else f'{p:.3f}'
def cells(v, bold=False, p=None):
    b, se = v['b'], v['se']; irr = math.exp(b)
    if p is None: p = 2 * (1 - NormalDist().cdf(abs(b / se)))
    s = f'{irr:.2f}{st(p)}'
    pass
    return [s, f'{irr * se:.2f}', fp(p)], p, v.get('p')
chk = []
def row(lab, v, **k):
    c, p, pb = cells(v, **k); chk.append((lab, p, pb)); return '| ' + ' | '.join(lab + c) + ' |'
T = {}
T[1] = '\n'.join(['| 모형 | 처치 | exp(β) | 표준오차 | p값 |', '|---|---|---|---|---|',
    row(['주 분석', '스카니아 + 루나'], R['main']['D'], bold=True), row(['월드별', '스카니아(제한 약 6개월)'], R['only_스카니아']['D']), row(['월드별', '루나(제한 30일)'], R['only_루나']['D'])])
es = R['es_main']['est']
lab2 = {'E-3': ['해제 3주 전 이전', '12.21~12.29'], 'E-2': ['해제 2주 전', '12.30~1.5'], 'E0': ['해제 후 1주', '1.13~1.19'], 'E1': ['해제 후 2주', '1.20~1.26'], 'E2': ['해제 후 3주', '1.27~2.2'], 'E3': ['해제 후 4주', '2.3~2.9'], 'E4': ['해제 후 5주', '2.10~2.16'], 'E5': ['해제 후 6주(5일)', '2.17~2.21']}
r2 = ['| 구간 | 기간 | exp(β) | 표준오차 | p값 |', '|---|---|---|---|---|', row(lab2['E-3'], es['E-3']), row(lab2['E-2'], es['E-2']), '| 해제 직전 주(기준) | 1.6~1.11 | 1 | – | – |']
r2 += [row(lab2[k], es[k]) for k in ['E0', 'E1', 'E2', 'E3', 'E4', 'E5']]
T[2] = '\n'.join(r2)
T[3] = '\n'.join(['| 모형 | 항목 | exp(β) | 표준오차 | p값 |', '|---|---|---|---|---|',
    row(['대체지 모형', '대형 비교 월드 × 해제 후(소형 대비)'], R['subst']['L']), row(['베라를 대형으로 분류', '대형 비교 월드 × 해제 후'], R['subst_bera']['L']),
    row(['이른 표본', '대형 비교 월드 × 해제 후'], E['subst']['L']), row(['소형 월드 8개만 비교', '처치 × 해제 후'], R['vs_small']['D']), row(['대형 월드 2개만 비교', '처치 × 해제 후'], R['vs_large']['D'])])
T[4] = '\n'.join(['| 현재 레벨 | 캐릭터 수 | exp(β) | 표준오차 | p값 |', '|---|---|---|---|---|',
    row(['200 미만', '2,340'], v5c['band_lt200']['D'], bold=True), row(['200~209', '2,859'], v5c['band_b200_209']['D']), row(['210 이상', '1,741'], v5c['band_ge210']['D']), row(['(210 이상 중) 260 이상', '598'], v5c['band_ge260']['D'])])
def row5(lab, v, note, **k):
    c, p, pb = cells(v, **k); chk.append((lab, p, pb)); return f'| {lab} | {c[0]} | {c[1]} | {c[2]} | {note} |'
cw = v5c['cluster_world_t1']
r5 = ['| 검증 | exp(β) | 표준오차 | p값 | 비고 |', '|---|---|---|---|---|',
 row5('주 분석(참고)', R['main']['D'], ''), row5('월드별 선형 추세 통제', v5b['main_trend']['D'], '대안적 추세 가정'),
 row5('12.21~1.4 기간 제외', v5b['leaf_window_main']['D'], '월드 리프 기간 제외(저점 주 대부분 포함)'),
 row5('해제 후 1.13~1.24', rv['split']['D_early'], '업데이트 737 이전(해제 후 기간 분할)'), row5('해제 후 1.25 이후', rv['split']['D_late'], '업데이트 737 이후(해제 후 기간 분할)'),
 row5('분석 기간 1.24까지', rv['pre_0125']['D'], '업데이트 737 이전 기간만 사용'),
 row5('위약 해제일 12.28', v5c['placebo_2023-12-28']['D'], '해제 전 기간만'), row5('위약 해제일 12.31', v5c['placebo_2023-12-31']['D'], '해제 전 기간만'), row5('위약 해제일 1.4', v5c['placebo_2024-01-04']['D'], '해제 전 기간만'),
 row5('생성 월드 판별 불가 포함', R['all_main']['D'], '미확정 캐릭터를 현재 월드 생성으로 간주'), row5('첫 관측 월드 조건 제외', rv['relaxed_main']['D'], '이 조건으로 제외된 캐릭터 없음'),
 row5('이른 표본(2024.11.6 랭킹)', E['main']['D'], f"순열 검정 66쌍 중 {E['perm_main']['rank']}위(p = {E['perm_main']['p']:.3f})"),
 f"| 순열 검정(일반 월드 12개) | {math.exp(R['perm_main']['actual']):.2f}{st(R['perm_main']['p'])} | – | {R['perm_main']['p']:.3f} | 66쌍 중 {R['perm_main']['rank']}위 |",
 f"| 순열 검정(대형 월드 6개) | {math.exp(R['perm_main']['actual']):.2f}{st(rv['perm_large6']['rank'] / rv['perm_large6']['n'])} | – | {rv['perm_large6']['rank'] / rv['perm_large6']['n']:.3f} | 15쌍 중 1위(가능한 최소값) |",
 f"| 월드 클러스터 표준오차 | {math.exp(cw['b']):.2f}{st(cw['p'])} | {math.exp(cw['b']) * cw['se']:.2f} | {fp(cw['p'])} | 집단 수가 적어 신뢰성 제한, 참고용 |"]
T[5] = '\n'.join(r5)
json.dump({str(k): v for k, v in T.items()}, open('tables_md.json', 'w'), ensure_ascii=False)
for k, v in T.items(): print(f'--- 표 {k}\n{v}')
print('--- star check (z-based p vs bootstrap percentile p)')
for lab, p, pb in chk:
    if pb is not None and st(p) != st(pb): print('DIFF', lab, round(p, 3), round(pb, 3))
