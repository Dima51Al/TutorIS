#!/usr/bin/env python3
"""Воспроизводимые учебные оценки, суммы в рублях. Python 3, без зависимостей."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEIGHTS = {'coverage': .25, 'tco': .20, 'time': .15, 'usability': .10,
           'security': .10, 'integration': .08, 'scale': .07, 'independence': .05}
SCORES = {'A': [2, 5, 5, 3, 2, 1, 2, 5],
          'B': [4, 4, 4, 4, 3, 3, 4, 2],
          'C': [5, 2, 1, 4, 4, 5, 5, 5]}
COSTS = {'A': {'creation': 48000, 'annual': 156000},
         'B': {'creation': 180000, 'annual': 297600},
         'C': {'creation': 1440000, 'annual': 300000}}
ASSUMPTIONS = {'tutors': 20, 'students_per_tutor': 25, 'subscription_monthly': 490,
               'months': 12, 'saved_hours_monthly': 5, 'hour_value': 800,
               'realization_share': .5, 'saved_lessons_monthly': .25,
               'lesson_margin': 1000, 'ramp_months': 6, 'ramp_share': .5}

def weighted(weights):
    return {v: round(sum(w*s for w,s in zip(weights.values(), scores)), 6)
            for v,scores in SCORES.items()}

def sensitivity():
    result = {}
    for delta in (-.05, 0, .05):
        largest = WEIGHTS['coverage'] + delta
        weights = {key: (largest if key == 'coverage' else value*(1-largest)/(1-WEIGHTS['coverage']))
                   for key,value in WEIGHTS.items()}
        result[str(delta)] = {'weights': weights, 'scores': weighted(weights),
                             'winner': max(weighted(weights), key=weighted(weights).get)}
    return result

def effects(hours=5, value=800, realization=.5, lessons=.25):
    time = 20*12*hours*value*realization
    avoided_loss = 20*12*lessons*1000
    return {'time': time, 'avoided_loss': avoided_loss, 'annual': time+avoided_loss}

def business_case(creation, annual, effect):
    tco = creation + annual*3
    first = effect*.75  # 6 месяцев по 50%, затем 6 месяцев по 100%
    benefits = first + effect*2
    balance = -creation
    payback_month = None
    cashflows = []
    for month in range(1, 37):
        multiplier = .5 if month <= 6 else 1
        net = effect/12*multiplier-annual/12
        before = balance
        balance += net
        if payback_month is None and balance >= 0:
            payback_month = month-1 + (-before/net)
        cashflows.append([month, round(effect/12*multiplier,2), round(annual/12,2),round(net,2),round(balance,2)])
    return {'tco_3y': tco, 'effect_y1': first, 'effect_y2': effect, 'effect_y3': effect,
            'effect_3y': benefits, 'net_3y': benefits-tco, 'roi_percent': (benefits-tco)/tco*100,
            'steady_payback_years': creation/(effect-annual) if effect>annual else None,
            'ramp_payback_months': payback_month, 'cashflows': cashflows}

def main():
    assert abs(sum(WEIGHTS.values())-1)<1e-9
    base = effects()
    cases = {key: business_case(**{'creation': COSTS[key]['creation'], 'annual': COSTS[key]['annual'], 'effect': effect})
             for key,effect in [('A',108000),('B',base['annual']),('C',588000)]}
    scenarios = {}
    for key, params in {'pessimistic': (3,600,.3,.1), 'base':(5,800,.5,.25), 'optimistic':(6,900,.6,.4)}.items():
        e=effects(*params)
        scenarios[key] = {'assumptions': params, 'effects': e,
                          'business_case': business_case(180000,297600,e['annual'])}
    result = {'assumptions': ASSUMPTIONS, 'weights': WEIGHTS, 'scores': weighted(WEIGHTS),
              'sensitivity': sensitivity(), 'costs': COSTS, 'effects': base,
              'cases': cases, 'scenarios': scenarios,
              'break_even_realization_3y': ((1072800/2.75)-60000)/960000,
              'break_even_price_3y_monthly': (1485000-180000-3*180000)/(20*36),
              'break_even_tutors_3y': (180000+3*180000)/(74250-17640)}
    (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (HERE/'cashflow_b.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['month','benefit_rub','operation_cost_rub','net_rub','cumulative_after_investment_rub'])
        writer.writerows(cases['B']['cashflows'])
    print(json.dumps({k:v for k,v in result.items() if k not in ['cases','scenarios','assumptions']}, ensure_ascii=False,indent=2))
    print('B', {k:v for k,v in cases['B'].items() if k!='cashflows'})
    for s,v in scenarios.items(): print(s, v['effects']['annual'], v['business_case']['roi_percent'], v['business_case']['ramp_payback_months'])
if __name__ == '__main__': main()
