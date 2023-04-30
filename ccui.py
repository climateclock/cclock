"""Functions for formatting and constructing the Climate Clock display."""

import cctime
from displayio import Bitmap
import math
from microfont import large, small
import prefs
import time


DISPLAY_WIDTH = 192


def calc_countdown(deadline_module, now_millis):
    deadline = cctime.millis_to_tm(deadline_module.ref_millis)
    now = cctime.millis_to_tm(now_millis)
    next_anniversary = (now[0],) + deadline[1:]
    if next_anniversary < now:
        next_anniversary = (now[0] + 1,) + deadline[1:]
    y = deadline[0] - next_anniversary[0]
    # When showing a countdown, round up to the next highest whole second.
    t = (cctime.tm_to_millis(next_anniversary) - now_millis + 999)//1000
    s, t = t % 60, t // 60
    m, t = t % 60, t // 60
    h, d = t % 24, t // 24
    return y, d, h, m, s


def format_value(module, now_millis):
    result = ''
    elapsed = now_millis - module.ref_millis  # integer
    if module.growth == 'linear':
        value = module.initial + module.rate * elapsed // 1000
        value += module.bias if value > 0 else -module.bias  # proper rounding
        str_value = '0'*module.shift + str(abs(value))
        # ccapi.load_value guarantees that shift > decimals.
        negative_sign = '-' if value < 0 else ''
        whole_part = str_value[:-module.shift].lstrip('0')
        fractional_part = str_value[-module.shift:][:module.decimals]
        result = negative_sign + whole_part
        if fractional_part:
            result += '.' + fractional_part
    return result


def render_deadline_module(bitmap, y, module, pi, lang='en'):
    bitmap.fill(0, 0, y, bitmap.width, y + 16)
    yr, d, h, m, s = calc_countdown(module, cctime.get_millis())
    texts = {
        'de': f'{yr} Jahre {d} Tage {h:02d}:{m:02d}:{s:02d}',
        'en': f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}',
        'pt': f'{yr} ANOS {d} DIAS {h:02d}:{m:02d}:{s:02d}',
        'es': f'{yr} años {d} días {h:02d}:{m:02d}:{s:02d}',
        'fr': f'{yr} ans {d} jours {h:02d}:{m:02d}:{s:02d}',
    }
    text = texts.get(lang, texts['en'])
    if prefs.get('deadline_force_caps'):
        text = text.upper()
    width = large.measure(text)
    x = max((DISPLAY_WIDTH - width)//2, 0)
    large.draw(text, bitmap, x, y, pi)


def render_lifeline_module(bitmap, y, module, pi, with_label=True, lang='en'):
    bitmap.fill(0, 0, y, bitmap.width, y + 16)
    if module.type == 'value':
        render_value_module(bitmap, y, module, pi, with_label, lang)
    if module.type == 'newsfeed':
        render_newsfeed_module(bitmap, y, module, pi, lang)


def render_label(bitmap, y, labels, pi):
    for font in [large, small]:
        for text in labels:
            width = font.measure(text)
            if width < bitmap.width:
                x = (DISPLAY_WIDTH - width)//2
                font.draw(text, bitmap, x, y, pi)
                return
        y += 5


def render_value_module(bitmap, y, module, pi, with_label=True, lang='en'):
    value_text = format_value(module, cctime.get_millis())
    label_text = unit_text = ''
    label_w = value_w = 0
    for label_item in module.labels:
        if with_label:
            label_text = label_item
        label_w = small.measure(label_text)
        for unit_text in module.unit_labels:
            value_w = large.measure(value_text + unit_text)
            if value_w + label_w < bitmap.width:
                break
        if value_w + label_w < bitmap.width:
            break
    text = value_text + unit_text
    if unit_text.startswith('$'):
        text = '$' + value_text + unit_text[1:]
    width = large.measure(text)
    if label_text:
        width += 4 + small.measure(label_text)
    x = max((DISPLAY_WIDTH - width)//2, 0)
    x = large.draw(text, bitmap, x, y, pi)
    small.draw(label_text, bitmap, x + 4, y + 5, pi)


last_newsfeed_module = None
newsfeed_w = DISPLAY_WIDTH
newsfeed_buffer = None
newsfeed_static = False

headline_index = 0
headline_text = ''
headline_next_char = 0


def reset_newsfeed():
    global last_newsfeed_module
    last_newsfeed_module = None


def format_item(item):
    headline = item.headline.strip()
    return f'{headline} ({item.source.strip()})' if item.source else headline


def render_newsfeed_module(bitmap, y, module, pi, lang='en'):
    global newsfeed_w
    global newsfeed_buffer
    global newsfeed_static
    global headline_index
    global headline_text
    global headline_next_char
    global last_newsfeed_module

    if not module.items:
        print('Newsfeed contains no items.')
        return

    if not newsfeed_buffer:
        newsfeed_buffer = Bitmap(DISPLAY_WIDTH + 20, large.h, 2)

    if module != last_newsfeed_module:
        last_newsfeed_module = module
        newsfeed_w = DISPLAY_WIDTH
        newsfeed_buffer.fill(0)
        newsfeed_static = False
        # Don't reset headline_index, so that we keep making progress to the
        # next headline when flipping between the newsfeed and a custom message.
        headline_text = ''
        headline_next_char = 0

    n = len(module.items)
    item = module.items[headline_index % n]

    if n == 1 and not headline_text:
        headline_text = format_item(item)
        newsfeed_w = large.measure(headline_text)
        if newsfeed_w <= DISPLAY_WIDTH:
            # There is only one headline and it fits entirely; do not scroll.
            large.draw(headline_text, newsfeed_buffer)
            newsfeed_static = True
        else:
            newsfeed_w = DISPLAY_WIDTH
            headline_text = ''

    if newsfeed_static:
        x = (DISPLAY_WIDTH - newsfeed_w) // 2
        bitmap.freeblit(x, y, newsfeed_buffer, dest_value=pi)
        return

    # The headline isn't static, so render it with a U+00B7 dot as a separator.
    if not headline_text:
        headline_text = format_item(item) + ' \xb7 '

    # Move the headline over, then draw any more characters needed at the end.
    newsfeed_buffer.freeblit(0, 0, newsfeed_buffer, 2, 0)
    newsfeed_w -= 2
    while newsfeed_w < DISPLAY_WIDTH:
        if headline_next_char >= len(headline_text):
            headline_index += 1
            item = module.items[headline_index % n]
            headline_text = format_item(item) + ' \xb7 '
            headline_next_char = 0
        ch = headline_text[headline_next_char]
        headline_next_char += 1
        newsfeed_w = large.draw(ch, newsfeed_buffer, newsfeed_w, 0)

    bitmap.freeblit(0, y, newsfeed_buffer, dest_value=pi)
