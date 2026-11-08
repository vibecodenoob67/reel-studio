# Self-check for the cutting rules: py -3.12 tools/test_pace.py (prints ok)
from pace import remap, retakes


def words(*ts, gaps=()):
    return [{'w': t, 's': i + (0.8 if i in gaps else 0), 'e': i + 0.5} for i, t in enumerate(ts)]


assert retakes(words('Walt', "doesn't", 'know', 'that.', 'Walt', "doesn't", 'know', 'that.')) == {0, 1, 2, 3}
assert retakes(words('the', 'best', 'way', 'the', 'best', 'way', 'to', 'win.')) == {0, 1, 2}  # false start mid-sentence
assert retakes(words('So', 'the', 'best.', 'So', 'the', 'best', 'way', 'is', 'this.')) == {0, 1, 2}  # restarted sentence
assert retakes(words('really', 'really', 'good.')) == set()  # emphasis, not a retake
assert retakes(words('I', 'went', 'home.', 'I', 'slept.')) == set()  # only one word in common
# a word whose start Whisper put in the cut pause still survives; a dropped word does not
w = [{'w': 'a', 's': 0, 'e': 0.5}, {'w': 'b', 's': 1, 'e': 1.5}, {'w': 'I', 's': 1.9, 'e': 2.4}]
assert [x['w'] for x in remap(w, {1}, [(0, 0.6), (2.1, 2.6)])] == ['a', 'I']
assert remap(w, {1}, [(0, 0.6), (2.1, 2.6)])[1]['s'] == 0.6
print('ok')
