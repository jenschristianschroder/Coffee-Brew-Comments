"""Exercise a running server over a real HTTP socket; standard library only."""
import json
import os
import time
import urllib.error
import urllib.request


base = os.environ.get('BASE_URL', 'http://127.0.0.1:8080').rstrip('/')
for attempt in range(100):
    try:
        with urllib.request.urlopen(base + '/health', timeout=1) as response:
            assert json.load(response) == {'status': 'ok'}
        break
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        if attempt == 99:
            raise
        time.sleep(0.2)

payload = {'coffee_type': 'espresso', 'datetime': '2026-11-04T16:30:00+01:00'}
request = urllib.request.Request(base + '/comment', data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(request, timeout=5) as response:
    assert response.status == 200
    result = json.load(response)
    assert set(result) == {'comment'}
    assert 'espresso' in result['comment'] and '4:30 p.m.' in result['comment']
    print(json.dumps(result))

request = urllib.request.Request(base + '/comment', data=b'{"coffee_type":"espresso","datetime":"invalid"}',
                                 headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(request, timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 422
else:
    raise AssertionError('Invalid date-time was accepted.')
print('HTTP smoke checks passed.')
