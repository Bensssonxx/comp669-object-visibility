"""Check the final PPTX against saved CSVs, notes, and source hashes."""
import csv
import hashlib
import json
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/occlusion_completion'
DECK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'final/COMP669_Occlusion_Final_v3.pptx'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def read(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))


def main():
    data = json.loads((ROOT / 'final/slide_data.json').read_text())
    for name, expected in data['source_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    summary, bins, pairs = [read(name) for name in
                           ['accuracy_summary.csv', 'foreground_bins.csv', 'pair_measurements.csv']]
    pct = lambda x: f'{float(x)*100:.1f}%'
    pp = lambda x: f'{float(x)*100:.1f}'
    normalize = lambda value: ' '.join(value.split())

    def stat(cohort, fraction, pattern, model, fill=128):
        return float(next(r['estimate'] for r in summary if r['cohort'] == cohort
                          and float(r['fraction']) == fraction and r['pattern'] == pattern
                          and r['metric'] == model and int(r['fill']) == fill))

    def pair(cohort, model):
        return next(r for r in pairs if r['cohort'] == cohort and r['model'] == model
                    and r['pair_type'] == 'head_contrast' and r['fill'] == '128')

    checks = []
    with zipfile.ZipFile(DECK) as z:
        slide_names = [n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
        assert len(slide_names) == 14
        slides = {i: ET.fromstring(z.read(f'ppt/slides/slide{i}.xml')) for i in range(1, 15)}
        assert [i for i, s in slides.items() if s.attrib.get('show') == '0'] == [13, 14]
        checks.append('12 visible slides and two hidden backups')

        def text(i):
            return ' '.join(t.text or '' for t in slides[i].findall('.//a:t', NS))

        def table(i):
            ts = slides[i].findall('.//a:tbl', NS)
            assert len(ts) == 1, i
            return [[''.join(t.text or '' for t in cell.findall('.//a:t', NS))
                     for cell in row.findall('a:tc', NS)] for row in ts[0].findall('a:tr', NS)]

        with (ROOT/'results/patch_relocation/summary.csv').open() as f:
            patch_results = list(csv.DictReader(f))
        expected = [[{'aimv2':'AIMv2','dinov2':'DINOv2'}[r['metric']],pct(r['center_acc']),pct(r['relocated_acc'])]
                    for r in patch_results if r['cohort']=='primary' and r['metric']!='interaction']
        assert table(7)[1:] == expected
        loss = next(r for r in read('clean_loss.csv') if r['cohort']=='primary' and r['pattern']=='random'
                    and float(r['fraction'])==.75 and r['fill']=='128')
        assert all(pp(loss[m+'_loss'])+' pp' in text(8) for m in ['aimv2','dinov2'])
        expected = []
        for f in [.25, .5, .75]:
            for pat in ['center', 'random']:
                expected.append([f'{int(f*100)}%', pat,
                                 pct(stat('new_head', f, pat, 'aimv2')),
                                 pct(stat('new_head', f, pat, 'dinov2'))])
        assert table(10)[1:] == expected
        expected = []
        for model in ['aimv2', 'dinov2']:
            r = pair('new_head', model)
            expected.append(['AIMv2' if model == 'aimv2' else 'DINOv2',
                             pct(r['accuracy_a']), pct(r['accuracy_b']), pp(r['difference'])])
        assert table(11)[1:] == expected
        for slide, cohort in [(9, 'auxiliary_head'), (11, 'new_head')]:
            r = pair(cohort, 'aimv2')
            for field in ['object_visibility', 'head_visibility', 'body_visibility', 'background_visibility']:
                for role in ['a', 'b']:
                    assert pct(r[field + '_' + role]) in text(slide), (slide, field, role)
        expected = []
        for f in [.25, .5, .75]:
            for pat in ['prefix', 'suffix', 'center', 'random']:
                expected.append([f'{int(f*100)}%', pat, *[pct(stat('primary', f, pat, m, fill))
                                for fill in [128, 0] for m in ['aimv2', 'dinov2']]])
        assert table(13)[1:] == expected
        checks.append('Displayed new-cohort, region, and full-budget tables match CSVs')

        def charts(i):
            rels = ET.fromstring(z.read(f'ppt/slides/_rels/slide{i}.xml.rels'))
            targets = {r.attrib['Id']: r.attrib['Target'] for r in rels}
            result = []
            for c in slides[i].findall('.//c:chart', NS):
                target = targets[c.attrib['{' + NS['r'] + '}id']]
                filename = posixpath.normpath(posixpath.join('ppt/slides', target)).lstrip('/')
                result.append(ET.fromstring(z.read(filename)))
            return result

        def check_series(chart, expected_y, expected_x=None):
            series = chart.findall('.//c:ser', NS)
            assert len(series) == len(expected_y)
            for j, s in enumerate(series):
                axis = 'yVal' if expected_x is not None else 'val'
                actual = [float(v.text) for v in s.findall(f'c:{axis}//c:pt/c:v', NS)]
                assert len(actual) == len(expected_y[j]), (actual, expected_y[j])
                assert all(abs(a-b) <= .000501 for a, b in zip(actual, expected_y[j]))
                if expected_x is not None:
                    xs = [float(v.text) for v in s.findall('c:xVal//c:pt/c:v', NS)]
                    assert len(xs) == len(expected_x[j])
                    assert all(abs(a-b) <= .000501 for a, b in zip(xs, expected_x[j]))

        check_series(charts(5)[0], [[100*stat('primary', .25, pat, model)
                                    for pat in ['center', 'random']] for model in ['aimv2', 'dinov2']])
        for chart, pat in zip(charts(6), ['center', 'random']):
            cells = [[r for r in bins if r['cohort'] == 'primary' and float(r['fraction']) == .25
                      and r['fill'] == '128' and r['pattern'] == pat and r['metric'] == model
                      and float(r['bin_width']) == .2 and r['convention'] == 'image_average'
                      and r['estimable'] == 'True'] for model in ['aimv2', 'dinov2']]
            cells = [sorted(rows, key=lambda r: int(r['fg_bin'])) for rows in cells]
            check_series(chart, [[100*float(r['estimate']) for r in rows] for rows in cells],
                         [[100*float(r['foreground_mean']) for r in rows] for rows in cells])
        for chart, fill in zip(charts(8), [128, 0]):
            check_series(chart, [[100*stat('primary', f, pat, 'aim_minus_dino', fill)
                                  for f in [.25, .5, .75]] for pat in ['center', 'random']],
                         [[25., 50., 75.], [25., 50., 75.]])
        assert [len(charts(i)) for i in [5, 6, 8]] == [1, 2, 2]
        checks.append('All five editable chart caches match saved point estimates and x coordinates')

        notes_file = (ROOT / 'final/SPEAKER_NOTES_EN.md').read_text()
        for i, s in enumerate(data['slides'], 1):
            notes = ' '.join(ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml')).itertext())
            assert normalize(s['note']) in normalize(notes), i
            assert normalize(s['note']) in normalize(notes_file), i
            assert s['source'] in notes
        assert not re.search(r'[\u4e00-\u9fff]', ''.join(text(i) for i in slides) + notes_file)
        assert 'Codex' in text(12) and 'pending' not in text(12)
        assert 'https://github.com/Bensssonxx/comp669-object-visibility' in z.read('ppt/slides/_rels/slide12.xml.rels').decode()
        checks.append('English embedded notes match the external script; disclosure and link retained')
    words = sum(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", s['note'])) for s in data['slides'])
    assert words == data['word_count'] and words / 90 * 60 + 40 < 720
    result = dict(passed=True, deck_sha256=hashlib.sha256(DECK.read_bytes()).hexdigest(), checks=checks,
                  spoken_words=words, estimated_minutes_at_90wpm_with_pauses=words / 90 + 40 / 60,
                  scope='Source/content checks; timing is estimated, not a rehearsal. Visual review is separate.')
    (ROOT / 'final/CONTENT_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
