"""Author the Coffee Snark phrase model directly. No training or external data."""
import json
from pathlib import Path


def build():
    coffees = {
        'espresso': {'label': 'An espresso', 'aliases': ['expresso'], 'caffeine': True},
        'double_espresso': {'label': 'A double espresso', 'aliases': ['double espresso', 'doppio', 'double shot'], 'caffeine': True},
        'americano': {'label': 'An Americano', 'aliases': [], 'caffeine': True},
        'filter': {'label': 'Filter coffee', 'aliases': ['filter coffee', 'drip', 'drip coffee', 'batch brew'], 'caffeine': True},
        'cappuccino': {'label': 'A cappuccino', 'aliases': [], 'caffeine': True},
        'latte': {'label': 'A latte', 'aliases': ['cafe latte', 'caffe latte'], 'caffeine': True},
        'flat_white': {'label': 'A flat white', 'aliases': ['flat white'], 'caffeine': True},
        'decaf': {'label': 'Decaf', 'aliases': ['decaffeinated', 'decaf coffee', 'decaf espresso', 'decaf latte'], 'caffeine': False},
        'mocha': {'label': 'A mocha', 'aliases': ['caffe mocha', 'cafe mocha'], 'caffeine': True},
        'cortado': {'label': 'A cortado', 'aliases': [], 'caffeine': True},
        'macchiato': {'label': 'A macchiato', 'aliases': ['espresso macchiato'], 'caffeine': True},
        'ristretto': {'label': 'A ristretto', 'aliases': [], 'caffeine': True},
        'lungo': {'label': 'A lungo', 'aliases': [], 'caffeine': True},
        'coffee': {'label': 'Coffee', 'aliases': ['black coffee', 'regular coffee'], 'caffeine': True},
    }
    jokes = []

    def add(prefix, lines, *, drinks=None, periods=None, caffeine=None, weight=1.0):
        for i, text in enumerate(lines, 1):
            item = {'id': f'{prefix}_{i:02d}', 'text': text, 'weight': weight}
            if drinks is not None:
                item['coffees'] = drinks
            if periods is not None:
                item['periods'] = periods
            if caffeine is not None:
                item['caffeine'] = caffeine
            jokes.append(item)

    add('office', [
        'Liquid optimism. Results may vary.',
        'Another cup for the task we are still not starting.',
        'The machine has done its part. Awkwardly, the rest is up to us.',
        'A very convincing impression of progress.',
        'At least one thing in this office has finished brewing.',
        'This meeting could have been a coffee. And now it is.',
        'A small ceremony for a very large to-do list.',
        'The spreadsheet is going to be so impressed.',
        'Productivity has been notified. No response yet.',
        'One more beverage between us and the actual task.',
        'Finally, an office process that produces something useful.',
        'Another successful meeting with the coffee machine.',
        'The most reliable member of the team strikes again.',
        'A bold investment in the appearance of being busy.',
        'Please allow three to five business sips for motivation.',
        'The coffee is ready. The plan remains under review.',
    ])
    add('early', [
        'Even the coffee machine thinks this is a bit much.',
        'The sun has not clocked in. Expectations seem high.',
        'An impressive commitment to being awake against our better judgment.',
        'Apparently the day needed a prequel.',
        'The office plants are still asleep. Sensible of them.',
    ], periods=['early'], weight=3.0)
    add('morning', [
        'The official start of pretending to be a morning person.',
        'Breakfast for the part of the day that has deadlines.',
        'A warm-up for opening the inbox and immediately regretting it.',
        'The first item on the to-do list that stood a chance.',
        'Optimism, before the calendar has its say.',
        'The day has barely started and already requires a beverage strategy.',
    ], periods=['morning'], weight=3.0)
    add('midday', [
        'A perfectly respectable way to postpone lunch decisions.',
        'The morning has submitted its resignation.',
        'Halfway to lunch. Already negotiating terms.',
        'The second half of the morning requires additional paperwork.',
        'A brief intermission in the ongoing production of looking busy.',
    ], periods=['midday'], weight=3.0)
    add('afternoon', [
        'The afternoon slump has requested a meeting.',
        'Lunch has left the chat. Motivation never joined.',
        'A small appeal against the verdict of the afternoon.',
        'The day is now running on extensions and good intentions.',
        'Another attempt to turn the last meeting into a productive one.',
    ], periods=['afternoon'], weight=3.0)
    add('evening', [
        'The office is closing. The plot is apparently thickening.',
        'A bold interpretation of winding down.',
        'The calendar says after hours. The mug has other plans.',
        'Apparently going home needed a side quest.',
        'The day has asked for a sequel. Nobody approved the budget.',
    ], periods=['evening'], weight=3.0)
    add('late_caffeine', [
        'Bold strategy for someone who enjoys sleeping.',
        'Bedtime has been moved to the backlog.',
        'Tomorrow would like a word about this decision.',
        'An excellent way to give tonight a surprise agenda.',
    ], periods=['afternoon', 'evening'], caffeine=True, weight=3.0)
    add('espresso', [
        'A whole productivity strategy in a very small cup.',
        'Small cup. Ambitious expectations.',
        'Finally, a meeting that can be finished in one sip.',
        'All the drama, none of the volume.',
    ], drinks=['espresso', 'ristretto'], weight=4.0)
    add('double', [
        'Two shots. Still only one inbox.',
        'Because one shot left room for doubt.',
        'The calendar has clearly made an enemy.',
        'A double espresso for a single remaining thread of patience.',
    ], drinks=['double_espresso'], weight=4.0)
    add('americano', [
        'Espresso with enough water to attend the entire meeting.',
        'A tiny coffee given a very generous operating budget.',
        'All the ambition of espresso, with more time to reconsider.',
    ], drinks=['americano'], weight=4.0)
    add('filter', [
        'No foam. No ceremony. Just an unreasonable amount of faith.',
        'A classic choice for a problem that is definitely not new.',
        'The spreadsheet of coffees. Dependable, and everywhere.',
    ], drinks=['filter', 'coffee'], weight=4.0)
    add('latte', [
        'The milk has brought a little coffee to work.',
        'Coffee wearing a very comfortable disguise.',
        'Caffeine has arrived in business casual.',
        'A warm glass of plausible productivity.',
    ], drinks=['latte'], weight=4.0)
    add('cappuccino', [
        'Foam on top. Unfinished work underneath.',
        'A little hat for the coffee. Very professional.',
        'Productivity, but make it frothy.',
        'An impressive amount of presentation for such a small deliverable.',
    ], drinks=['cappuccino'], weight=4.0)
    add('flatwhite', [
        'Minimalist foam. Maximalist expectations.',
        'A latte that has read the style guide.',
        'Quietly judging the cappuccino. As usual.',
    ], drinks=['flat_white'], weight=4.0)
    add('mocha', [
        'Dessert has successfully impersonated an office supply.',
        'Chocolate with a very convincing job title.',
        'The expense report will simply say coffee.',
    ], drinks=['mocha'], weight=4.0)
    add('cortado', [
        'A carefully negotiated truce between espresso and milk.',
        'Small, balanced, and more organized than the calendar.',
        'A coffee with excellent boundaries. Aspirational.',
    ], drinks=['cortado'], weight=4.0)
    add('macchiato', [
        'Espresso with just enough milk to call it collaboration.',
        'A coffee that delegated one tiny task to the milk.',
        'The foam contribution has been noted in the minutes.',
    ], drinks=['macchiato'], weight=4.0)
    add('lungo', [
        'An espresso that stayed for the follow-up meeting.',
        'The coffee equivalent of one more quick question.',
        'Apparently even the espresso needed an extension.',
    ], drinks=['lungo'], weight=4.0)
    add('decaf', [
        'All the ritual, with the drama turned down.',
        'Coffee has joined the meeting on mute.',
        'A very diplomatic relationship with the coffee machine.',
        'An excellent cup of plausible deniability.',
        'The office ritual, now in low-power mode.',
    ], drinks=['decaf'], weight=4.0)
    add('decaf_late', [
        'A rare beverage decision that remembers tomorrow exists.',
        'Someone has actually read the bedtime agenda.',
        'At last, a plot twist that respects office hours.',
    ], drinks=['decaf'], periods=['afternoon', 'evening'], weight=6.0)
    add('double_late', [
        'Two shots, and apparently no plans to count sheep.',
        'Bedtime has just been escalated to management.',
    ], drinks=['double_espresso'], periods=['afternoon', 'evening'], weight=6.0)
    add('milk_morning', [
        'Breakfast has outsourced its personality to the milk frother.',
        'An ambitious attempt to make the morning feel like a cafe.',
    ], drinks=['latte', 'cappuccino', 'flat_white'], periods=['morning'], weight=5.0)

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
            {'text': '{coffee} at {clock}.', 'weight': 5.0},
            {'text': '{coffee} at {clock}?', 'weight': 2.0},
            {'text': 'Ah, {coffee_lower} at {clock}.', 'weight': 1.0},
        ],
        'punchlines': jokes,
    }


if __name__ == '__main__':
    path = Path(__file__).resolve().parent / 'weights.json'
    payload = build()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {len(payload["punchlines"])} punchlines and their direct weights to {path.name}. Training steps: 0.')
