#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def flatten(text):
    # Accept streams with banner lines; extract the first JSON object
    s = text
    i = s.find('{')
    j = s.rfind('}')
    if i != -1 and j != -1 and j > i:
        s = s[i:j+1]
    return json.loads(s)


def extract_core(results):
    # Build core read metrics table {framework: {read_one, read_many}}
    core = {}
    def grab(name, key_ro, key_rm):
        lst = results.get(name) or []
        ro = rm = None
        for item in lst:
            n = item.get('name', '')
            qps = float(item.get('qps', 0))
            if n.endswith(key_ro):
                ro = qps
            if n.endswith(key_rm):
                rm = qps
        return ro, rm

    ro, rm = grab('oxen', 'read_one', 'read_many')
    if ro is not None or rm is not None:
        core['Oxen'] = {'read_one': ro or 0.0, 'read_many': rm or 0.0}
    ro, rm = grab('sqlalchemy', 'read_one', 'read_many')
    if ro is not None or rm is not None:
        core['SQLAlchemy'] = {'read_one': ro or 0.0, 'read_many': rm or 0.0}
    ro, rm = grab('tortoise', 'read_one', 'read_many')
    if ro is not None or rm is not None:
        core['Tortoise'] = {'read_one': ro or 0.0, 'read_many': rm or 0.0}
    ro, rm = grab('django', 'read_one', 'read_many')
    if ro is not None or rm is not None:
        core['Django'] = {'read_one': ro or 0.0, 'read_many': rm or 0.0}
    return core


def extract_extended(results):
    # Build extended metrics table {metric: {framework: qps}}
    ext = {}
    def fill(section, mapping):
        for item in (results.get(section) or []):
            name = item.get('name', '')
            qps = float(item.get('qps', 0))
            for metric, substr in mapping.items():
                if name.endswith(substr):
                    ext.setdefault(metric, {})
                    label = section.split('_')[0].capitalize()
                    if section.startswith('sqlalchemy'):
                        label = 'SQLAlchemy'
                    if section.startswith('tortoise'):
                        label = 'Tortoise'
                    if section.startswith('django'):
                        label = 'Django'
                    ext[metric][label] = qps
    mapping = {
        'bulk_insert_200': 'bulk_insert_200',
        'bulk_update_all': 'bulk_update_all',
        'join': 'join',
        'window_count': 'window_count',
        'aggregate_count': 'aggregate_count',
    }
    for sec in ('oxen_ext', 'sqlalchemy_ext', 'tortoise_ext', 'django_ext'):
        fill(sec, mapping)
    return ext


def extract_models(results):
    # Models-only read metrics across Oxen, SQLAlchemy, Django
    models = {}
    # Oxen: explicit models labels
    ox = results.get('oxen') or []
    ro = rm = None
    for item in ox:
        n = item.get('name', '')
        qps = float(item.get('qps', 0))
        if n.endswith('read_one_models'):
            ro = qps
        if n.endswith('read_many_models'):
            rm = qps
    if ro is not None or rm is not None:
        models['Oxen'] = {'read_one_models': ro or 0.0, 'read_many_models': rm or 0.0}

    # SQLAlchemy and Django core reads are model hydration paths already
    def grab(section):
        lst = results.get(section) or []
        _ro = _rm = None
        for item in lst:
            n = item.get('name', '')
            qps = float(item.get('qps', 0))
            if n.endswith('read_one'):
                _ro = qps
            if n.endswith('read_many'):
                _rm = qps
        return _ro or 0.0, _rm or 0.0

    ro, rm = grab('sqlalchemy')
    if ro or rm:
        models['SQLAlchemy'] = {'read_one_models': ro, 'read_many_models': rm}
    ro, rm = grab('django')
    if ro or rm:
        models['Django'] = {'read_one_models': ro, 'read_many_models': rm}
    return models


def to_csv_models(models):
    lines = ["framework,read_one_models_qps,read_many_models_qps"]
    for fw, vals in models.items():
        lines.append(f"{fw},{vals.get('read_one_models', 0)},{vals.get('read_many_models', 0)}")
    return "\n".join(lines) + "\n"


def to_csv_core(core):
    lines = ["framework,read_one_qps,read_many_qps"]
    for fw, vals in core.items():
        lines.append(f"{fw},{vals.get('read_one', 0)},{vals.get('read_many', 0)}")
    return "\n".join(lines) + "\n"


def to_csv_extended(ext):
    # Rows: metric, then frameworks as columns present
    frameworks = sorted({fw for m in ext.values() for fw in m.keys()})
    header = ["metric", *frameworks]
    lines = [",".join(header)]
    for metric, m in ext.items():
        row = [metric]
        for fw in frameworks:
            row.append(str(m.get(fw, 0)))
        lines.append(",".join(row))
    return "\n".join(lines) + "\n"


def main():
    data = sys.stdin.read()
    results = flatten(data)

    out_dir = Path('benchmarks')
    out_dir.mkdir(exist_ok=True)

    # Save normalized JSON
    (out_dir / 'normalized_results.json').write_text(json.dumps(results, indent=2))

    # Extract and save CSVs
    core = extract_core(results)
    (out_dir / 'core_qps.csv').write_text(to_csv_core(core))

    ext = extract_extended(results)
    (out_dir / 'extended_qps.csv').write_text(to_csv_extended(ext))

    models = extract_models(results)
    (out_dir / 'models_qps.csv').write_text(to_csv_models(models))

    print("Saved: benchmarks/normalized_results.json, core_qps.csv, extended_qps.csv, models_qps.csv")


if __name__ == '__main__':
    main()


