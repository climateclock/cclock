"""Client for the Climate Clock API.  Main entry point is load().

See: https://docs.climateclock.world/climate-clock-docs/climate-clock-api
"""

import cctime
import gc
import json
from collections import namedtuple


Config = namedtuple('Config', ('device_id', 'module_ids', 'display', 'langs'))
Display = namedtuple('Display', ('deadline', 'lifeline', 'timer'))
Palette = namedtuple('Palette', ('primary',))
Item = namedtuple('Item', ('pub_millis', 'headline', 'source'))
Timer = namedtuple('Timer', ('id', 'type', 'flavor', 'unit_labels', 'labels', 'full_width_labels', 'ref_millis'))
Newsfeed = namedtuple('Newsfeed', ('id', 'type', 'flavor', 'labels', 'full_width_labels', 'items'))
Value = namedtuple('Value', ('id', 'type', 'flavor', 'labels', 'full_width_labels', 'initial', 'ref_millis', 'growth', 'rate', 'decimals', 'shift', 'bias', 'unit_labels', 'count_up_millis'))
Defn = namedtuple('Defn', ('config', 'module_dict', 'modules'))

# Remove this when the API file is updated to include language names.
LANGUAGE_NAMES = {
    'de': 'Deutsch',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'pt': 'Português'
}


def load_config(data):
    gc.collect()
    langs = data.get('langs', {'en': 'English'})
    if isinstance(langs, list):
        langs = {code: LANGUAGE_NAMES.get(code, code) for code in langs}
    return Config(
        data.get('device'),
        data.get('modules'),
        load_display(data.get('display') or {}),
        langs
    )


def load_display(data):
    gc.collect()
    return Display(
        load_palette(data.get('deadline') or {}),
        load_palette(data.get('lifeline') or {}),
        data.get('timer')
    )


def load_palette(data):
    gc.collect()
    return Palette(
        parse_css_color(data.get('color_primary') or None)
    )


def parse_css_color(color):
    gc.collect()
    color = (color or '').replace('#', '')
    if len(color) == 6:
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def load_timer(id, data, timer_config):
    gc.collect()
    return Timer(
        id,
        data.get('type'),
        data.get('flavor'),
        timer_config.get('unit_labels', {}),
        data.get('labels'),
        data.get('full_width_labels'),
        cctime.try_isoformat_to_millis(data, 'timestamp') or 0
    )


def load_newsfeed(id, data):
    gc.collect()
    return Newsfeed(
        id,
        data.get('type'),
        data.get('flavor'),
        data.get('labels'),
        data.get('full_width_labels'),
        [load_item(item) for item in data.get('newsfeed', [])]
    )


def load_item(data):
    gc.collect()
    return Item(
        cctime.try_isoformat_to_millis(data, 'date'),
        data.get('headline') or '',
        data.get('source') or '',
    )


def load_value(id, data):
    decimals = data.get('decimals')
    if decimals is None:
        res = data.get('resolution') or 1
        decimals = 0
        while res < 0.9:  # allow for precision error in CircuitPython floats
            res, decimals = res * 10, decimals + 1

    initial = data.get('shifted_initial')
    rate = data.get('shifted_rate')
    shift = data.get('shift') or 0
    if initial is not None and rate is not None:  # treat these as bigints
        initial = int(initial)
        rate = int(rate)
    else:  # fall back to the old API, with floats
        initial = data.get('initial') or 0
        rate = data.get('rate') or 0
        initial_sign = -1 if initial < 0 else 1
        rate_sign = -1 if rate < 0 else 1
        initial = abs(initial)
        rate = abs(rate)
        # CircuitPython only has single-precision floats with 22 bits of
        # precision, which is about 6.5 decimal places.
        while 0 < initial < 10000000 or 0 < rate < 10000000:
            initial *= 10
            rate *= 10
            shift += 1
        initial = int(initial) * initial_sign
        rate = int(rate) * rate_sign

    while shift <= decimals:
        initial *= 10
        rate *= 10
        shift += 1
    # The bias is the amount to add so that the last digit is rounded correctly.
    bias = 5
    for i in range(decimals + 1, shift):
        bias *= 10

    return Value(
        id,
        data.get('type'),
        data.get('flavor'),
        data.get('labels'),
        data.get('full_width_labels'),
        initial,
        cctime.try_isoformat_to_millis(data, 'timestamp') or 0,
        data.get('growth') or 'linear',
        rate,
        decimals,
        shift,
        bias,
        data.get('unit_labels'),
        int(data.get('count_up_duration', 0) * 1000)
    )


def load_defn(data):
    gc.collect()
    config = load_config(data.get('config', {}))
    gc.collect()
    module_dict = {}
    for module_id, value in data.get('modules', {}).items():
        if value['type'] == 'timer':
            module = load_timer(module_id, value, config.display.timer)
        elif value['type'] == 'newsfeed':
            module = load_newsfeed(module_id, value)
        elif value['type'] == 'value':
            module = load_value(module_id, value)
        gc.collect()
        module_dict[module_id] = module
    return Defn(
        config,
        module_dict,
        [module_dict[module_id] for module_id in config[1]]
    )


def load(file):
    return load_defn(json.load(file)['data'])
