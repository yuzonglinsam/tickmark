"""Bounded arithmetic on explicit SEC metric/period references. Never eval model code."""
from __future__ import annotations

import math
import re

VERSION = 'answer-checks-v1'
SCALES = {'units': 1, 'k': 1e3, 'm': 1e6, 'bn': 1e9, 'tn': 1e12, '萬': 1e4, '億': 1e8}


def catalog(doc):
    out = {}
    for group in ('facts', 'extended', 'metrics'):
        for period, rows in doc.get(group, {}).items():
            for key, row in rows.items():
                if not isinstance(row, dict):
                    continue
                value = row.get('value')
                sources = row.get('evidence', row.get('sources', []))
                unit = row.get('unit', doc['issuer']['currency'])
                kind = 'ratio' if unit in ('ratio', 'x') else 'money'
                out[f'{period}/{key}'] = {'value': value, 'kind': kind,
                    'currency': doc['issuer']['currency'] if kind == 'money' else None,
                    'sources': sources, 'period': period, 'metric': key}
    return out


def calculate(spec, doc, derived=None):
    """Return canonical labels/formula; model labels and numeric outputs are never trusted."""
    if not isinstance(spec, dict):
        raise ValueError('Calculation must be an object')
    op, refs = spec.get('operation'), spec.get('refs')
    limits = {'value': (1, 1), 'sum': (2, 8), 'difference': (2, 2), 'ratio': (2, 2), 'percent': (1, 2)}
    if op not in limits or not isinstance(refs, list) or not limits[op][0] <= len(refs) <= limits[op][1]:
        raise ValueError('Unsupported operation or operand count')
    if not all(isinstance(r, str) for r in refs) or len(set(refs)) != len(refs):
        raise ValueError('Invalid or duplicate references')
    pool = {**catalog(doc), **(derived or {})}
    if any(r not in pool for r in refs):
        raise ValueError('Unknown metric or fiscal period')
    rows = [pool[r] for r in refs]
    for row in rows:
        v = row['value']
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('An operand is missing or non-finite')
        if not row['sources'] or any(s not in doc.get('sources', {}) for s in row['sources']):
            raise ValueError('An operand lacks resolvable SEC sources')
    kinds = {r['kind'] for r in rows}
    if len(kinds) != 1 or len({r['currency'] for r in rows}) != 1:
        raise ValueError('Incompatible units or currencies')
    if op in ('sum', 'ratio', 'percent') and (len({r['period'] for r in rows}) > 1 or any(r['period'] is None for r in rows)):
        raise ValueError('This operation requires a common fiscal period; use difference for cross-period changes')
    values = [r['value'] for r in rows]
    kind = rows[0]['kind']
    if op == 'value':
        value, symbol = values[0], ''
    elif op == 'sum':
        value, symbol = sum(values), ' + '
    elif op == 'difference':
        value, symbol = values[0] - values[1], ' − '
    elif len(values) == 2:
        if values[1] == 0:
            raise ValueError('Division by zero')
        value, symbol, kind = values[0] / values[1], ' ÷ ', 'ratio'
    else:
        if kind != 'ratio':
            raise ValueError('A percentage needs a ratio or two compatible operands')
        value, symbol = values[0], ''
    if not math.isfinite(value):
        raise ValueError('Non-finite calculation result')
    scale = spec.get('scale', 'units')
    if scale not in SCALES or (kind == 'ratio' and scale != 'units'):
        raise ValueError('Unsupported unit conversion')
    currency = doc['issuer']['currency'] if kind == 'money' else None
    if spec.get('currency', currency) != currency:
        raise ValueError('Currency conversion is not supported')
    decimals = spec.get('decimals', 3)
    if type(decimals) is not int or not 0 <= decimals <= 6:
        raise ValueError('Precision must be an integer from zero to six')
    factor = 100 if op == 'percent' else 1 / SCALES[scale]
    display = value * factor
    unit = '%' if op == 'percent' else 'x' if kind == 'ratio' else f'{currency} {scale}'
    result = f'{display:,.{decimals}f} {unit}'
    terms = [f'{r.get("expression", ref)} ({r["value"]:,.15g} {r["currency"] or "ratio"})' for ref, r in zip(refs, rows)]
    formula = symbol.join(terms)
    if op == 'percent':
        formula = f'({formula}) × 100'
    elif scale != 'units':
        formula = f'({formula}) ÷ {SCALES[scale]:,.0f}'
    sources = sorted({s for r in rows for s in r['sources']})
    return {'text': result, 'verified': True, 'matched': f'{op}: ' + ', '.join(refs),
            'formula': formula + ' = ' + result, 'value': value, 'unit': unit, 'sources': sources,
            'kind': kind, 'currency': currency, 'period': rows[0]['period'] if len({r['period'] for r in rows}) == 1 else None,
            'expression': '(' + symbol.join(r.get('expression', ref) for ref, r in zip(refs, rows)) + ')'}


def render_answer(payload, doc):
    """Keep free prose unverified; append server-rendered, explicitly labelled arithmetic."""
    if not isinstance(payload, dict) or not isinstance(payload.get('answer'), str):
        raise ValueError('Invalid answer schema')
    answer = re.sub(r'\s?\[(?:S|P)\d+(?:,\s?(?:S|P)\d+)*\]', '', payload['answer']).strip()
    specs = payload.get('calculations', [])
    if not isinstance(specs, list) or len(specs) > 8:
        raise ValueError('Expected up to eight calculations')
    # Free prose is never promoted to verified just because a matching number exists.
    checks = [{'text': m.group(), 'verified': False, 'matched': 'Unbound prose; analyst review required'}
              for m in re.finditer(r'[+−-]?\d[\d,.]*(?:\s?(?:%|x|bn|mn|m|億|萬|倍))?', answer)]
    if checks or re.search(r'[零〇一二三四五六七八九十百千萬億两兩]+[點点零〇一二三四五六七八九十百千萬億两兩]*\s*(?:億|萬|元|倍|%|percent|billion|million)', answer, re.I):
        answer = 'Unbound numerical prose withheld. Review the labelled calculations below; their scope is shown explicitly.'
        checks = []
    sources, calculations, derived = set(), [], {}
    for index, spec in enumerate(specs):
        try:
            check = calculate(spec, doc, derived)
        except (ValueError, TypeError, OverflowError) as exc:
            calculations.append({'verified': False, 'reason': str(exc)})
            answer += '\n\nCalculation unavailable: ' + str(exc) + '.'
            continue
        calculations.append(check)
        derived[f'calc:{index}'] = check
        sources.update(check['sources'])
        # The canonical metric labels make the binding visible independently of AI prose.
        answer += '\n\n' + check['formula']
    return {'answer': answer, 'numbers': checks, 'calculations': calculations,
            'calculation_sources': sorted(sources), 'verification_version': VERSION}
