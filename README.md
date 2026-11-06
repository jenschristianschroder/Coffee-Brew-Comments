# Coffee Brew Comments

A small Docker service that turns a coffee type and date-time into a short,
sarcastic comment for your office coffee machine. Send the returned text to the
Raspberry Pi's existing text-to-speech setup.

The generator supports **black coffee, cappuccino, espresso, and `other`** for
unidentified machine activity. Version 2 defaults to the **large** model, combining
complete jokes with authored sentence structures and typed phrase fragments.
It needs no training, GPU, model download, or external API. It is a rule-based
sentence composer, not a neural language model.

| Model data | Classic | Large (default) |
| --- | ---: | ---: |
| File size | 93,489 bytes (93.5 KB) | 569,347 bytes (569.3 KB) |
| Complete punchlines | 420 | 1,000 |
| Opening styles | 20 | 60 |
| Sentence families | 0 | 100 |
| Sentence patterns | 0 | 400 |
| Typed fragments | 0 | 2,000 |
| Sampling weights | 440 | 3,460 |
| Learned parameters | 0 | 0 |

The large bank contains **750 coffee jokes and 250 mystery-event jokes**, including
all original material. Its weekday-specific jokes use the local date in the
configured timezone. Each of 100 sentence families has four introductions; each
of 20 vocabulary banks combines five compatible modifiers with 20 base phrases.
Those 2,000 lexical variations are not 2,000 separate jokes.

For a fixed coffee, weekday, and time period, the large model offers roughly
28.8–62.4 million selectable combinations. This is a structural count, not that
many distinct jokes or a claim of general language ability. The classic model has
1,180 combinations per recognized coffee/time period and 1,040 for `other`.
Counts exclude varying the clock time. All shipped large combinations are bounded
to 220 characters. The model file sizes exclude the service, Docker image, and history.

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

Each request samples a compatible comment. It excludes the last **60 joke premises**,
prefers less-used jokes, and avoids the last **two opening styles**, including across
restarts. All four introductions of a sentence family share one history key, so
changing the introduction cannot bypass the repeat window. Fragments are also
selected from the least-used eligible choices, using persistent usage counters.

With a fixed context, every eligible complete joke or sentence family is used before
any premise is reused. Counts are shared across coffee types and time periods.
Repeating a request generates another comment; the service does not deduplicate
brew events or play audio itself.

| Endpoint | Behavior |
| --- | --- |
| `POST /comment` | Accepts `coffee_type` and `datetime`; returns `{"comment": "..."}`. |
| `POST /generate` | rpiCoffee contract: accepts `coffee_label` and `timestamp`; returns `response` and `elapsed_s`. |
| `GET /manifest` | Describes the `coffee-comments` service for rpiCoffee's service registry. |
| `GET /model` | Reports the active variant, exact file size, component counts, and combination range without generating text. |
| `GET /settings` | Returns the active model selector with `classic` / `large` choices. |
| `PATCH /settings` | Switches models immediately and saves the choice across restarts. |
| `GET /coffee-types` | Returns supported coffee type identifiers and configured timezone. |
| `GET /health` | Returns `{"status":"ok"}` when the process is responding. |
| `GET /docs` | Interactive API documentation. |

`datetime` must be an ISO 8601 string with `Z` or a UTC offset, for example
`2026-11-04T15:30:00Z`. The service converts that instant to `COFFEE_TIMEZONE`
before selecting jokes and displaying the time. Offsets make daylight-saving
ambiguities explicit. Missing offsets, invalid dates, unsupported type values, and extra
request fields return HTTP 422. `coffee_type` is case-insensitive; spaces,
underscores, and hyphens are normalized.

Supported types are `black`, `cappuccino`, `espresso`, and `other`. Black coffee
also accepts `black coffee`, `coffee`, and `regular coffee`. The existing
`expresso` alias is accepted for espresso. The aliases `unknown`, `unrecognized`,
and `unrecognised` map to `other`. Unsupported beverages, including latte,
decaf, filter, and double espresso, return HTTP 422.

## Unrecognized or unexplained activity

Send `"coffee_type": "other"` when the upstream prediction cannot recognize a
drink, the vibration pattern is unrecognizable, the machine is being cleaned or
serviced, or an event simply defies explanation. This service does not infer the
actual cause: its comments play with possibilities, from confused sensors and
cleaning cycles to office ghosts and unsolicited interdimensional firmware.

```bash
curl -sS http://localhost:8080/comment \
  -H 'Content-Type: application/json' \
  -d '{"coffee_type":"other","datetime":"2026-11-04T10:15:00+01:00"}'
```

One possible response:

```json
{
  "comment": "Unidentified machine activity at 10:15 a.m. Could be a cleaning cycle. Could be a seance with excellent plumbing."
}
```

`other` has dedicated openings and punchlines that do not announce a completed
coffee, assume a drink exists, or identify a real maintenance fault. Its caffeine
metadata is unknown (`null`). Known coffee types keep their own joke pools.
The caller should map its unrecognized events to `other`; arbitrary unsupported
strings do not silently become this category.

## Use with rpiCoffee

The service implements the [rpiCoffee service manifest contract](https://github.com/jenschristianschroder/rpiCoffee/blob/main/docs/manifest-spec.md).
`GET /manifest` advertises the service name `coffee-comments`, the required
`coffee_label` and `timestamp` inputs, the `response` and `elapsed_s` outputs,
`POST /generate` for execution, `GET /health` for health checks, and
`GET /settings` / `PATCH /settings` for runtime model selection.

rpiCoffee's native app already uses host port 8080. Start this container on 8004:

```bash
COFFEE_PORT=8004 docker compose up -d --build
curl -sS http://127.0.0.1:8004/manifest
curl -sS http://127.0.0.1:8004/generate \
  -H 'Content-Type: application/json' \
  -d '{"coffee_label":"espresso","timestamp":"2026-11-04T16:30:00+01:00"}'
```

One possible response (generation time varies):

```json
{
  "response": "An espresso at 4:30 p.m. Bold strategy for someone who enjoys sleeping.",
  "elapsed_s": 0.002
}
```

Put `COFFEE_PORT=8004` in a local `.env` file to retain the port choice for future
Compose commands. The default host port remains 8080; the container always
listens on 8080. Keep the existing history volume when updating.

In rpiCoffee's service registry, register `coffee-comments` with endpoint
`http://127.0.0.1:8004` when its main app runs on the same Pi. If the caller runs
in a container on the same Docker network, use `http://coffee-snark:8080` instead.

The generation step's input mapping is:

```json
{
  "coffee_label": "$classifier.label",
  "timestamp": "$sensor.timestamp"
}
```

Wire the TTS and remote-save `text` inputs to `$coffee-comments.response`.
The manifest supports the `skip` and `halt` failure policies; a 3-second
per-step timeout is a reasonable starting point for this local service.
rpiCoffee also bundles this service's source. If using that bundled version, follow
[its setup instructions](https://github.com/jenschristianschroder/rpiCoffee/tree/main/services/coffee-comments)
and avoid starting a second container on the same port. Registration and pipeline
selection remain manual; the service does not change your saved pipeline.

`/generate` and `/comment` use the same generator, timezone, aliases, and persistent
repetition history. `unknown`, `unrecognized`, and `unrecognised` produce `other`
machine-activity comments. Invalid requests return HTTP 422 without consuming
history. `timestamp` follows the same offset-required validation as `datetime`.
Each successful call consumes one comment; retries are not deduplicated.

This is the structured coffee-generation contract, not a raw-prompt LLM API.
Send only `coffee_label` and `timestamp`: `prompt`, `system`, `max_tokens`, and
other extra fields are rejected. `elapsed_s` measures generation including the
history update. Neural token counts and token rates are not reported.

In rpiCoffee, select the model under **Admin → Service Settings → coffee-comments →
Model variant** and save. For an existing registration, click **Refresh manifest**
(circular arrow) in **Service Registry** once after upgrading so the app discovers
the new settings endpoints. This does not change the saved pipeline. The bundled
rpiCoffee update includes dropdown support for the advertised choices.

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

## Select a model and inspect its size

Use the settings API or rpiCoffee's admin dropdown to select `classic` or `large`:

```bash
curl -sS http://127.0.0.1:8080/settings
curl -sS -X PATCH http://127.0.0.1:8080/settings \
  -H 'Content-Type: application/json' \
  -d '{"settings":{"COFFEE_MODEL_VARIANT":"classic"}}'
```

Use `large` to switch back. The change takes effect immediately for both generation
endpoints, without restarting or consuming repetition history. The service saves
the choice atomically in `/data/settings.json` in the existing data volume. It
validates and saves before changing the running model; a failed update keeps the
previous selection. Flat `{"COFFEE_MODEL_VARIANT":"large"}` bodies are also accepted.
Invalid variants, missing values, and unknown keys return HTTP 422.

`COFFEE_MODEL_VARIANT` in `.env` sets the initial default only. Startup precedence is
an explicit `WEIGHTS_PATH` override, saved selection, the environment variable,
then `large`. The Docker service runs one worker to keep runtime selection consistent.
Other service configuration remains in the environment. Both model files are bundled in the image.
The classic `weights.json` is byte-for-byte unchanged. Existing generation request
and response fields, aliases, service name, and endpoints remain compatible.

```bash
curl -sS http://127.0.0.1:8080/model
```

`GET /model` reports the selected file's exact bytes, 0 learned parameters,
sampling-weight count, complete jokes, patterns, families, fragments, and the range
of selectable combinations for fixed contexts. Neither this endpoint nor health
checks consume repetition history.

A supplied `WEIGHTS_PATH` overrides the variant selector, retaining custom-model
support. The settings descriptor then shows `custom` as read-only, and updates
return HTTP 409. Remove the override and restart to enable selection again; any
previously saved variant is retained. Format 1 files still work. Format 2 adds
`patterns`, `slots`, and optional weekday restrictions on complete jokes.
An invalid active variant or malformed saved settings file fails startup clearly.

## Tune the humor and timing

The complete classic phrase model is `weights.json`. The large model is
`weights-large.json`. Every selectable opener, joke, pattern, or fragment has a
positive relative sampling weight. The generator filters by context, avoids recent
joke premises, and prefers the least-used remaining premises before applying weights.
Weights influence selection order; they are not learned neural parameters.

The source files are:

- `phrases.py` and `write_weights.py`: the original joke bank and model builder.
- `large_phrases.py`: 580 additional complete punchlines.
- `large_grammar.py`: vocabulary banks, sentence families, and additional openings.
- `write_large_weights.py`: combines the original and additional material.

Regenerate and rebuild after editing:

```bash
python write_weights.py
python write_large_weights.py
docker compose up -d --build
```

Keep existing identifiers stable by appending within groups. The large builder
checks group sizes; intentionally expanding a group requires updating its expected
count. The tests verify that the committed JSON matches its authored source and that
all possible shipped combinations fit the length bound. Invalid slot references,
weights, duplicate text, and invalid weekday restrictions are rejected.

| Period | Local hours |
| --- | --- |
| Early | 00:00–05:59 |
| Morning | 06:00–09:59 |
| Midday | 10:00–13:59 |
| Afternoon | 14:00–16:59 |
| Evening | 17:00–23:59 |

Set `COFFEE_TIMEZONE` to another IANA timezone in `.env` if required. Dates are
converted before both weekday and time-period selection, including daylight-saving
transitions. The jokes are in English and target drinks, the clock, machine mysteries,
and office life.

The history database stores the last 100 joke-family/opener pairs, plus usage
counters for joke premises and fragments. Existing databases upgrade in place.
Switching between large and classic retains their history. Keep the history volume
when updating; no model download or training takes place at startup.

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
then checks the production HTTP endpoints for both variants using the same history volume. The tests cover time zones and DST,
coffee aliases and unsupported drinks, isolation of mystery-event material,
manifest-driven generation, shared history across both API routes and restarts,
comment length, repetition history,
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
