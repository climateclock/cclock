"""Functions for formatting and constructing the Climate Clock display."""

import cctime
from displayio import Bitmap
import math
from microfont import large, small


def calc_countdown(deadline_module, now_millis):
    deadline = cctime.millis_to_tm(deadline_module.ref_millis)
    now = cctime.millis_to_tm(now_millis)
    next_anniversary = (now[0],) + deadline[1:]
    if next_anniversary < now:
        next_anniversary = (now[0] + 1,) + deadline[1:]
    y = deadline[0] - next_anniversary[0]
    t = (cctime.tm_to_millis(next_anniversary) - now_millis)//1000
    s, t = t % 60, t // 60
    m, t = t % 60, t // 60
    h, d = t % 24, t // 24
    return y, d, h, m, s


def to_bigint(f, scale):
    mantissa, exponent = math.frexp(f)
    # CircuitPython floats have 22 bits of mantissa
    scaled = int(mantissa * (1 << 22)) * scale
    if exponent > 0:
        scaled = scaled * (1 << exponent)
    else:
        scaled = scaled // (1 << -exponent)
    return scaled // (1 << 22)


def format_value(module, now_millis):
    elapsed = now_millis - module.ref_millis
    if module.growth == 'linear':
        scale = module.scale * 10000000  # 22 bits = about 7 decimal places
        decimals = module.decimals + 7

        scaled_initial = to_bigint(module.initial, scale)
        scaled_rate = to_bigint(module.rate, scale)
        scaled_value = scaled_initial + scaled_rate * elapsed // 1000
        str_value = str(scaled_value)
        if len(str_value) > decimals:
            whole_part = str_value[:-decimals]
        else:
            whole_part = '0'
            str_value = str(scaled_value + scale)
        fractional_part = str_value[-decimals:-7]
        return whole_part + '.' + fractional_part
    return ''


def render_deadline_module(bitmap, y, module, pi, lang='en'):
    yr, d, h, m, s = calc_countdown(module, cctime.get_millis())
    texts = {
        'de': f'{yr} Jahre {d} Tage {h:02d}:{m:02d}:{s:02d}',
        'en': f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}',
        'es': f'{yr} años {d} días {h:02d}:{m:02d}:{s:02d}',
        'fr': f'{yr} ans {d} jours {h:02d}:{m:02d}:{s:02d}',
        'is': f'{yr} ár {d} dagar {h:02d}:{m:02d}:{s:02d}'
    }
    text = texts.get(lang, texts['en'])
    large.draw(text, bitmap, 1, y, pi)


def render_lifeline_module(bitmap, y, module, pi, lang='en'):
    if module.type == 'value':
        render_value_module(bitmap, y, module, pi, lang)
    if module.type == 'newsfeed':
        render_newsfeed_module(bitmap, y, module, pi, lang)


def render_value_module(bitmap, y, module, pi, lang='en'):
    value_text = format_value(module, cctime.get_millis())
    for label_text in module.labels:
        label_w = small.measure(label_text)
        for unit_text in module.unit_labels:
            value_w = large.measure(value_text + unit_text)
            if value_w + label_w < bitmap.width:
                break
        if value_w + label_w < bitmap.width:
            break
    x = 1
    x = large.draw(value_text + unit_text, bitmap, x, y, pi)
    small.draw(label_text, bitmap, x + 4, y + 5, pi)


DISPLAY_WIDTH = 192
last_newsfeed_module = None
newsfeed_x = DISPLAY_WIDTH
newsfeed_index = 0
headline_label = None
headline_width = None


def reset_newsfeed():
    global last_newsfeed_module
    last_newsfeed_module = None


def format_item(item):
    headline = item.headline.strip()
    return f'{headline} ({item.source.strip()})' if item.source else headline


def render_newsfeed_module(bitmap, y, module, pi, lang='en'):
    global newsfeed_x
    global newsfeed_index
    global headline_label
    global headline_width
    global last_newsfeed_module

    if not module.items:
        print('Newsfeed contains no items.')
        return
    if module != last_newsfeed_module:
        headline_label = None
        last_newsfeed_module = module

    i = newsfeed_index
    n = len(module.items)
    item = module.items[i % n]

    if n == 1:
        if not headline_label:
            text = format_item(item)
            headline_width = large.measure(text)
            if headline_width <= DISPLAY_WIDTH:
                headline_label = Bitmap(headline_width, large.h, 2)
                large.draw(text, headline_label)
            else:
                text = format_item(item) + ' \xb7 '
                headline_width = large.measure(text)
                headline_label = Bitmap(headline_width * 2, large.h, 2)
                large.draw(text + text, headline_label)
        if headline_label.width <= DISPLAY_WIDTH:
            # There is only one headline and it fits entirely; do not scroll.
            x = (DISPLAY_WIDTH - headline_label.width) // 2
            bitmap.freeblit(x, y, headline_label, dest_value=pi)
            return

    if not headline_label:
        text = format_item(item) + ' \xb7 '
        headline_width = large.measure(text)

        text_with_trail = text
        for attempt in range(3):
            i = (i + 1) % n
            item = module.items[i]
            trail = format_item(item) + ' \xb7 '
            text_with_trail += trail
            text_with_trail_width = large.measure(text_with_trail)
            if text_with_trail_width >= headline_width + DISPLAY_WIDTH:
                headline_label = Bitmap(text_with_trail_width, large.h, 2)
                large.draw(text_with_trail, headline_label)
                break

    bitmap.freeblit(newsfeed_x, y, headline_label, dest_value=pi)

    if newsfeed_x + headline_width < 0:
        newsfeed_x += headline_width
        newsfeed_index = (i + 1) % n
        headline_label = None
    else:
        newsfeed_x -= 2
