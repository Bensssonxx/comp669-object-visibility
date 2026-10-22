"""Check final PPTX numbers, notes, hidden backups and source binding."""
import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results/extension_v2"
DECK = ROOT / "milestone/COMP669_Object_Visibility_Milestone_v6.pptx"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}

def read(name):
    with (DATA / name).open() as f:
        return list(csv.DictReader(f))

summary, contrasts, pairs = read("summary.csv"), read("primary_contrasts.csv"), read("paired_summary.csv")
data = json.loads((ROOT / "milestone/slide_data_v6.json").read_text())
for name, expected in data["evidence_sha256"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
checks = []
P = lambda x: f"{float(x)*100:.1f}%"
PP = lambda x: f"{float(x)*100:.1f}"

def stat(model, fill, pattern):
    return next(r for r in summary if r["cohort"] == "primary" and r["model"] == model and int(r["fill"]) == fill and r["pattern"] == pattern)

def family(pattern, fill):
    r = next(r for r in contrasts if r["contrast"] == f"aim_minus_dino_{pattern}_fill{fill}")
    return f"{'+' if float(r['estimate'])>=0 else ''}{PP(r['estimate'])} [{PP(r['familywise_ci_low'])}, {PP(r['familywise_ci_high'])}]"

def paired(model, kind):
    return next(r for r in pairs if r["model"] == model and r["pair_type"] == kind and r["fill"] == "128")

with zipfile.ZipFile(DECK) as z:
    slides = {i: ET.fromstring(z.read(f"ppt/slides/slide{i}.xml")) for i in range(1, 15)}
    hidden = [i for i, s in slides.items() if s.attrib.get("show") == "0"]
    assert hidden == [13, 14], hidden
    checks.append("12 visible slides, two hidden backups")

    def text(i):
        return " ".join(slides[i].itertext())

    def table(i):
        ts = slides[i].findall(".//a:tbl", NS)
        assert len(ts) == 1
        return [["".join(c.findall(".//a:t", NS)[j].text or "" for j in range(len(c.findall(".//a:t", NS)))) for c in row.findall("a:tc", NS)] for row in ts[0].findall("a:tr", NS)]

    expected = []
    for fill in [128, 0]:
        for q in ["center", "random"]:
            expected.append(["Gray" if fill == 128 else "Black", q.title(), P(stat("aimv2", fill, q)["estimate"]), P(stat("dinov2", fill, q)["estimate"])])
    assert table(7)[1:] == expected
    checks.append("All four displayed model comparisons match CSVs")
    backup_notes = " ".join(ET.fromstring(z.read("ppt/notesSlides/notesSlide13.xml")).itertext())
    for fill in [128, 0]:
        for q in ["center", "random"]:
            assert family(q, fill) in backup_notes
    assert table(4)[2][1] == "185 (5 per breed)"
    assert "740 different images" in table(4)[3][1]
    checks.append("First and second test sample sizes are explicit; adjusted intervals retained in backup notes")

    expected = []
    for m in ["aimv2", "dinov2"]:
        r = paired(m, "object_contrast")
        expected.append(["AIMv2" if m == "aimv2" else "DINOv2", P(r["accuracy_a"]), P(r["accuracy_b"])])
        assert P(paired(m, "visibility_matched")["correctness_flip_rate"]) in text(9)
    assert table(9)[1:] == expected
    checks.append("Foreground-pair accuracies and correctness-switch rates match CSVs")

    expected = []
    for m in ["aimv2", "dinov2"]:
        r = paired(m, "head_contrast")
        expected.append(["AIMv2" if m == "aimv2" else "DINOv2", P(r["accuracy_a"]), P(r["accuracy_b"]), PP(r["paired_accuracy_difference"])])
    assert table(10)[1:] == expected
    r = paired("aimv2", "head_contrast")
    for key in ["mean_object_visibility_a", "mean_object_visibility_b", "mean_head_visibility_a", "mean_head_visibility_b"]:
        assert P(r[key]) in text(10)
    checks.append("Auxiliary accuracies and foreground/head coverage match CSVs")

    expected = []
    for fill in [128, 0]:
        for m in ["aimv2", "dinov2"]:
            expected.append([f"{'AIMv2' if m=='aimv2' else 'DINOv2'} / {'gray' if fill==128 else 'black'}", P(stat(m, -1, "clean")["estimate"]), *[P(stat(m, fill, q)["estimate"]) for q in ["prefix", "suffix", "center", "random"]]])
    assert table(13)[1:] == expected
    checks.append("Full backup accuracy table matches CSVs")

    def chart_values(name):
        c = ET.fromstring(z.read(name))
        return [[float(v.text) for v in r.findall("c:val/c:numRef/c:numCache/c:pt/c:v", NS)] for r in c.findall(".//c:ser", NS)]

    assert chart_values("ppt/slides/charts/chart1.xml") == [[round(float(stat(m,128,q)["estimate"])*100,1) for q in ["center", "random"]] for m in ["aimv2", "dinov2"]]
    fg = read("foreground_coverage.csv")
    assert chart_values("ppt/slides/charts/chart2.xml") == [[round(float(next(r for r in fg if r["pattern"] == q)["mean"])*100,1) for q in ["prefix", "suffix", "center", "random"]]]
    checks.append("Both editable chart caches match source percentages rounded to one decimal")

    en = (ROOT / "milestone/SPEAKER_NOTES_EN_v6.md").read_text()
    for i, s in enumerate(data["slides"], start=1):
        notes = " ".join(ET.fromstring(z.read(f"ppt/notesSlides/notesSlide{i}.xml")).itertext())
        normalize = lambda value: " ".join(value.split())
        assert normalize(s["note"]) in normalize(notes) and normalize(s["note"]) in normalize(en), i
        assert s["source"] in notes, i
    checks.append("All 12 embedded spoken scripts and citations match the external speaker notes")

    assert "https://github.com/Bensssonxx/comp669-object-visibility" in z.read("ppt/slides/_rels/slide12.xml.rels").decode()
    assert "Codex" in text(12)
    assert "Public repository" in text(12)
    assert "Instructor access still needs arranging" not in text(12)
    assert "cannot isolate which training choice caused a difference" in text(5)
    assert "does not isolate the effect of the head" in text(10)
    assert "75% stays visible" in text(9)
    checks.append("Clickable repository link, visible AI disclosure and interpretation boundaries present")

    assert "All four patterns tested" in text(6)
    for phrase in ["50% and 75% image visibility", "all four patterns", "same 740 images", "mean pooling with max pooling", "clean training data", "validation", "Planned checks", "reuse previously evaluated images"]:
        assert phrase in text(12), phrase
    assert "more remains visible" in data["slides"][10]["note"]
    checks.append("Planned next steps distinguish visibility ratios from four mask patterns and preserve clean fitting and test-reuse scope")


timing = json.loads((ROOT / "milestone/TIMING_v6.json").read_text())
words = sum(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", s["note"])) for s in data["slides"])
assert timing["spoken_word_count"] == words
assert words / 90 * 60 + 40 < 720
checks.append("Script word-rate estimate under 12 minutes at 90 wpm plus 40 seconds of pauses")
review = {"passed": True, "deck_sha256": hashlib.sha256(DECK.read_bytes()).hexdigest(),
          "checks": checks, "spoken_words": words, "scope": "Package/content checks against saved evidence. Timing is estimated, not rehearsed."}
(ROOT / "docs/MILESTONE_V6_CONTENT_REVIEW.json").write_text(json.dumps(review, indent=2) + "\n")
print(json.dumps(review, indent=2))
