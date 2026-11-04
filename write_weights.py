"""Write the Coffee Snark phrase model directly. No training or external data."""
import json
from pathlib import Path

from phrases import COFFEE_JOKES, CONTEXT_JOKES, GENERAL, PERIOD_JOKES


def build():
    coffees = {
        'black': {'label': 'Black coffee', 'aliases': ['black coffee', 'coffee', 'regular coffee'], 'caffeine': True},
        'cappuccino': {'label': 'A cappuccino', 'aliases': [], 'caffeine': True},
        'espresso': {'label': 'An espresso', 'aliases': ['expresso'], 'caffeine': True},
    }
    jokes = []

    def add(prefix, lines, *, drinks=None, periods=None, weight=1.0):
        for i, text in enumerate(lines, 1):
            item = {'id': f'{prefix}_{i:02d}', 'text': text, 'weight': weight}
            if drinks is not None:
                item['coffees'] = drinks
            if periods is not None:
                item['periods'] = periods
            jokes.append(item)

    # Preserve identifiers for the existing office jokes and coffee/period groups.
    add('office', GENERAL)
    for coffee, lines in COFFEE_JOKES.items():
        add(coffee, lines, drinks=[coffee], weight=3.0)
    for period, lines in PERIOD_JOKES.items():
        add(period, lines, periods=[period], weight=2.0)
    for coffee, periods in CONTEXT_JOKES.items():
        for period, lines in periods.items():
            add(f'{coffee}_{period}', lines, drinks=[coffee], periods=[period], weight=4.0)

    return {
        'format_version': 1,
        'name': 'Coffee Snark',
        'model_type': 'conditional weighted phrase grammar',
        'training_steps': 0,
        'description': 'Original hand-written phrases and relative sampling weights; no learned or pretrained weights.',
        'coffee_types': coffees,
        'periods': [
            {'id': 'early', 'start_hour': 0, 'end_hour': 6},
            {'id': 'morning', 'start_hour': 6, 'end_hour': 10},
            {'id': 'midday', 'start_hour': 10, 'end_hour': 14},
            {'id': 'afternoon', 'start_hour': 14, 'end_hour': 17},
            {'id': 'evening', 'start_hour': 17, 'end_hour': 24},
        ],
        'openers': [
            {'id': 'order', 'text': '{coffee} at {clock}.', 'weight': 1.5},
            {'id': 'question', 'text': '{coffee} at {clock}?', 'weight': 1.0},
            {'id': 'ah', 'text': 'Ah, {coffee_lower} at {clock}.', 'weight': 1.0},
            {'id': 'it_is', 'text': "It's {clock}. {coffee} it is.", 'weight': 1.0},
            {'id': 'apparently', 'text': '{coffee}. At {clock}, apparently.', 'weight': 1.0},
            {'id': 'reporting', 'text': '{coffee}, reporting for duty at {clock}.', 'weight': 1.0},
            {'id': 'machine', 'text': 'At {clock}, the machine presents {coffee_lower}.', 'weight': 1.0},
            {'id': 'strategy', 'text': "Today's {clock} strategy: {coffee_lower}.", 'weight': 1.0},
            {'id': 'chat', 'text': '{coffee} has entered the chat at {clock}.', 'weight': 1.0},
            {'id': 'plan', 'text': "It's {clock}, and {coffee_lower} is the plan.", 'weight': 1.0},
        ],
        'punchlines': jokes,
    }


if __name__ == '__main__':
    path = Path(__file__).resolve().parent / 'weights.json'
    payload = build()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {len(payload["punchlines"])} punchlines and {len(payload["openers"])} openers. Training steps: 0.')
