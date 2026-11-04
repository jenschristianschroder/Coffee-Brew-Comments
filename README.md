# Coffee Brew Comments

A small Docker service that turns a coffee type and date-time into a short,
sarcastic comment for your office coffee machine. Send the returned text to the
Raspberry Pi's existing text-to-speech setup.

The generator supports **black coffee, cappuccino, and espresso**, with **300
original punchlines, ten setups, and directly assigned sampling weights**.
Coffee type and time of day determine which lines fit. Each coffee/time-of-day
combination has 118 applicable punchlines and 1,180 wording combinations, before
counting different clock times. Different setups are wording variations; the
300 punchlines are the actual joke bank.
It needs no training, GPU, model download, or external API. This is a conditional
phrase generator: it combines authored text rather than inventing arbitrary text
with a neural language model.

## Start on the Pi

With Docker Engine and the Compose plugin installed, run from this directory:

```bash
docker compose up -d --build
```

The service runs on port 8080, uses Copenhagen local time, and saves recent
punchline history in a Docker volume. The image uses the official multi-platform
Python base, with no architecture-specific paths. Use 64-bit Raspberry Pi OS on
the Pi 5. The build downloads the base image and Python packages; runtime
generation is offline.

## Request a comment

```bash
curl -sS http://localhost:8080/comment \
  -H 'Content-Type: application/json' \
  -d '{"coffee_type":"espresso","datetime":"2026-11-04T16:30:00+01:00"}'
```

One possible response:

```json
{
  "comment": "An espresso at 4:30 p.m. Bold strategy for someone who enjoys sleeping."
}
```

Each request samples a compatible comment. It excludes the last **60 punchlines**,
prefers less-used jokes, and avoids the last **two opening styles**, including
across container restarts. That history is shared by requests to this instance.
Starting with fresh history, repeatedly requesting the same coffee/time period
uses all 118 applicable jokes before any punchline repeats. When contexts vary,
usage counts are shared so frequently heard generic jokes give way to other material.
Repeating a request generates another comment; this endpoint does not deduplicate
brew events or play audio itself.

| Endpoint | Behavior |
| --- | --- |
| `POST /comment` | Accepts `coffee_type` and `datetime`; returns `{"comment": "..."}`. |
| `GET /coffee-types` | Returns supported coffee type identifiers and configured timezone. |
| `GET /health` | Returns `{"status":"ok"}` when the process is responding. |
| `GET /docs` | Interactive API documentation. |

`datetime` must be an ISO 8601 string with `Z` or a UTC offset, for example
`2026-11-04T15:30:00Z`. The service converts that instant to `COFFEE_TIMEZONE`
before selecting jokes and displaying the time. Offsets make daylight-saving
ambiguities explicit. Missing offsets, invalid dates, unknown drinks, and extra
request fields return HTTP 422. `coffee_type` is case-insensitive; spaces,
underscores, and hyphens are normalized.

Supported types are exactly `black`, `cappuccino`, and `espresso`. Black coffee
also accepts `black coffee`, `coffee`, and `regular coffee`. The existing
`expresso` alias is accepted for espresso. Other beverages, including latte,
decaf, filter, and double espresso, return HTTP 422.

## Call it from your brew handler

This Python example uses only the standard library:

```python
from datetime import datetime, timezone
import json
from urllib.request import Request, urlopen

def coffee_comment(coffee_type: str) -> str:
    request = Request(
        "http://127.0.0.1:8080/comment",
        data=json.dumps({
            "coffee_type": coffee_type,
            "datetime": datetime.now(timezone.utc).isoformat(),
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=3) as response:
        return json.load(response)["comment"]

comment = coffee_comment("cappuccino")
print(comment)  # Pass this string to your existing text-to-speech function.
```

The provided Compose file binds the port to the Pi's loopback address. A script
on that Pi can call `http://127.0.0.1:8080`. Another service in the same Compose
network can call `http://coffee-snark:8080`. To accept requests from another
machine on your LAN, change the port mapping to `"8080:8080"` and use the Pi's IP.
The service has no authentication and is intended for a local deployment.

## Tune the humor and timing

`weights.json` is the complete phrase model. Each punchline has an identifier,
text, a positive relative `weight`, and optional context restrictions. The model
filters by coffee and time, excludes the last 60 punchlines, and finds the
least-used remaining jokes. It then samples among those according to their
weights. A high weight gives a joke earlier priority without letting it crowd
out the rest of the bank. Ten opening styles are sampled independently, excluding
the two most recently heard styles.

If a custom model has too few choices for a repeat window, the generator reuses
the least recent applicable choice. The supplied 118-joke pools are large enough
to maintain the full 60-punchline exclusion window.

Change the JSON and rebuild the container to update it. The authored joke bank is
in `phrases.py`; `write_weights.py` assigns contexts, setups, and weights. After
editing those source files, run `python write_weights.py` to regenerate
`weights.json`, then rebuild the container. Keep existing joke IDs stable when
editing a running installation; append new lines to a group to preserve its IDs.

| Period | Local hours |
| --- | --- |
| Early | 00:00–05:59 |
| Morning | 06:00–09:59 |
| Midday | 10:00–13:59 |
| Afternoon | 14:00–16:59 |
| Evening | 17:00–23:59 |

Set `COFFEE_TIMEZONE` in `compose.yaml` to another IANA timezone if required.
The jokes are in English. They target the beverage, the clock, and office life.
They do not use anyone's name or personal information. History stores the last
100 pairs of punchline/opener identifiers, plus a usage counter for each
punchline that has been heard. Existing history databases are upgraded in place;
usage counters start from their retained history. Keep the existing volume when
updating with `docker compose up -d --build`.

## Test and develop

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8080
```

In another terminal, `python tests/smoke_http.py` exercises the live endpoint.
For container tests:

```bash
docker build --target test -t coffee-snark-test .
docker run --rm coffee-snark-test
```

GitHub Actions builds and tests the container on both x86-64 and ARM64 runners,
then checks the production HTTP endpoint. The tests cover time zones and DST,
coffee aliases and unsupported drinks, comment length, repetition history,
fair use of the joke bank, database upgrades, concurrent requests, input
validation, and the HTTP contract.

Useful maintenance commands:

```bash
docker compose logs -f
docker compose down
docker compose up -d --build
```

## Implementation references

- [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Official Python Docker image](https://hub.docker.com/_/python)
- [Docker Compose services](https://docs.docker.com/reference/compose-file/services/)
- [Pydantic date-time validation](https://docs.pydantic.dev/latest/api/standard_library_types/#datetimes)
