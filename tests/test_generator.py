from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest

from generator import CoffeeModel, CommentGenerator, WEIGHTS, clock_text


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.model = CoffeeModel()
        self.path = Path(self.temp.name) / 'history.db'
        self.generator = CommentGenerator(self.model, self.path, rng=random.Random(7))

    def history(self):
        with sqlite3.connect(self.path) as connection:
            return [row[0] for row in connection.execute('SELECT punchline FROM history ORDER BY id')]

    def test_aliases_and_unknown_drink(self):
        for raw, expected in [(' Double-Espresso ', 'double_espresso'), ('FLAT_WHITE', 'flat_white'),
                              ('caffè latte', 'latte'), ('decaf latte', 'decaf'), ('drip', 'filter')]:
            self.assertEqual(self.model.canonical_coffee(raw), expected)
        with self.assertRaises(ValueError):
            self.model.canonical_coffee('tomato soup')

    def test_local_time_boundaries(self):
        cases = [(0, 'early'), (5, 'early'), (6, 'morning'), (9, 'morning'),
                 (10, 'midday'), (13, 'midday'), (14, 'afternoon'),
                 (16, 'afternoon'), (17, 'evening'), (23, 'evening')]
        for hour, expected in cases:
            moment = datetime.fromisoformat(f'2026-11-04T{hour:02d}:00:00+01:00')
            self.assertEqual(self.model.context('espresso', moment)[2], expected)

    def test_utc_and_daylight_saving_conversion(self):
        cases = [('2026-11-04T15:30:00+00:00', 16, 1),
                 ('2026-03-29T01:30:00+00:00', 3, 2),
                 ('2026-10-25T00:30:00+00:00', 2, 2),
                 ('2026-10-25T01:30:00+00:00', 2, 1)]
        for stamp, hour, offset_hours in cases:
            local = self.model.context('espresso', datetime.fromisoformat(stamp))[1]
            self.assertEqual(local.hour, hour)
            self.assertEqual(local.utcoffset().total_seconds(), offset_hours * 3600)
        with self.assertRaises(ValueError):
            self.model.context('espresso', datetime(2026, 11, 4, 16))

    def test_clock_is_spoken_friendly(self):
        self.assertEqual(clock_text(datetime(2026, 11, 4, 0)), '12 a.m.')
        self.assertEqual(clock_text(datetime(2026, 11, 4, 12)), '12 p.m.')
        self.assertEqual(clock_text(datetime(2026, 11, 4, 16, 5)), '4:05 p.m.')

    def test_decaf_excludes_caffeine_punchlines(self):
        for period in ['early', 'morning', 'midday', 'afternoon', 'evening']:
            jokes = self.model.candidates('decaf', period)
            self.assertTrue(jokes)
            self.assertFalse(any(joke.get('caffeine') is True for joke in jokes))
            self.assertFalse(any('late_caffeine' in joke['id'] for joke in jokes))

    def test_time_and_drink_specific_jokes_are_restricted(self):
        morning_ids = {j['id'] for j in self.model.candidates('espresso', 'morning')}
        evening_ids = {j['id'] for j in self.model.candidates('espresso', 'evening')}
        self.assertFalse(any(j.startswith('late_caffeine') for j in morning_ids))
        self.assertTrue(any(j.startswith('late_caffeine') for j in evening_ids))
        self.assertFalse(any(j.startswith('latte_') for j in evening_ids))

    def test_all_contexts_have_variety_and_short_complete_comments(self):
        for coffee in self.model.data['coffee_types']:
            for period in self.model.data['periods']:
                jokes = self.model.candidates(coffee, period['id'])
                self.assertGreater(len(jokes), 12)
                moment = datetime(2026, 11, 4, period['start_hour'], 59)
                for joke in jokes:
                    for opener in self.model.data['openers']:
                        text = self.model.compose(coffee, moment, joke, opener)
                        self.assertLessEqual(len(text), 180, text)
                        self.assertNotIn('{', text)
                        self.assertNotIn('..', text)
                        self.assertTrue(text.endswith('.'))

    def test_recent_punchlines_do_not_repeat_and_survive_restart(self):
        moment = datetime.fromisoformat('2026-11-04T16:30:00+01:00')
        for _ in range(12):
            self.generator.comment('espresso', moment)
        previous = self.history()
        self.assertEqual(len(set(previous)), 12)
        restarted = CommentGenerator(self.model, self.path, rng=random.Random(8))
        restarted.comment('espresso', moment)
        self.assertNotIn(self.history()[-1], previous)

    def test_concurrent_generators_share_history_without_repeats(self):
        second = CommentGenerator(self.model, self.path, rng=random.Random(9))
        moment = datetime.fromisoformat('2026-11-04T16:30:00+01:00')
        with ThreadPoolExecutor(max_workers=6) as executor:
            outputs = list(executor.map(lambda i: (self.generator if i % 2 else second).comment('latte', moment), range(12)))
        self.assertEqual(len(outputs), 12)
        self.assertEqual(len(set(self.history())), 12)

    def test_history_is_bounded(self):
        moment = datetime.fromisoformat('2026-11-04T16:30:00+01:00')
        for _ in range(105):
            self.generator.comment('espresso', moment)
        self.assertEqual(len(self.history()), 100)

    def test_invalid_model_is_rejected(self):
        payload = json.loads(WEIGHTS.read_text())
        payload['punchlines'][0]['weight'] = -1
        invalid = Path(self.temp.name) / 'invalid.json'
        invalid.write_text(json.dumps(payload))
        with self.assertRaises(ValueError):
            CoffeeModel(invalid)


if __name__ == '__main__':
    unittest.main()
