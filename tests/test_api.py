from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from app import create_app


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.client = TestClient(create_app(history_db=Path(self.temp.name) / 'history.db'))
        self.addCleanup(self.client.close)
        self.payload = {'coffee_type': 'espresso', 'datetime': '2026-11-04T16:30:00+01:00'}

    def test_comment_has_small_json_contract(self):
        result = self.client.post('/comment', json=self.payload)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(set(result.json()), {'comment'})
        self.assertIn('espresso', result.json()['comment'])
        self.assertIn('4:30 p.m.', result.json()['comment'])

    def test_utc_input_and_alias(self):
        result = self.client.post('/comment', json={'coffee_type': 'BLACK COFFEE', 'datetime': '2026-11-04T15:30:00Z'})
        self.assertEqual(result.status_code, 200)
        self.assertIn('black coffee', result.json()['comment'].lower())
        self.assertIn('4:30 p.m.', result.json()['comment'])

    def test_invalid_inputs_are_422(self):
        for update in [{'coffee_type': 'tea'}, {'coffee_type': ''}, {'coffee_type': ' '},
                       {'coffee_type': 'latte'}, {'coffee_type': 'double_espresso'}, {'coffee_type': 'decaf'},
                       {'coffee_type': 3}, {'coffee_type': None}, {'coffee_type': ['espresso']},
                       {'datetime': '2026-11-04T16:30:00'}, {'datetime': '2026-02-30T16:30:00Z'},
                       {'datetime': 'yesterday'}, {'datetime': 1793800000}, {'extra': True}]:
            with self.subTest(update=update):
                self.assertEqual(self.client.post('/comment', json={**self.payload, **update}).status_code, 422)
        for payload in [{}, [], {'coffee_type': 'cappuccino'}]:
            self.assertEqual(self.client.post('/comment', json=payload).status_code, 422)

    def test_bad_json_is_rejected(self):
        self.assertEqual(self.client.post('/comment', content='{', headers={'Content-Type': 'application/json'}).status_code, 422)

    def test_health_types_and_openapi(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok'})
        types = self.client.get('/coffee-types').json()
        self.assertEqual(types['coffee_types'], ['black', 'cappuccino', 'espresso'])
        self.assertEqual(types['timezone'], 'Europe/Copenhagen')
        schema = self.client.get('/openapi.json').json()
        self.assertIn('/comment', schema['paths'])
        self.assertIn('datetime', schema['components']['schemas']['BrewRequest']['properties'])

    def test_method_and_path_contract(self):
        self.assertEqual(self.client.get('/comment').status_code, 405)
        self.assertEqual(self.client.get('/missing').status_code, 404)


if __name__ == '__main__':
    unittest.main()
