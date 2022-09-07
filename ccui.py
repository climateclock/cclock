"""Functions for formatting and constructing the Climate Clock display."""

import cctime
import math


TEST_MODE = False


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


def render_deadline_module(frame, y, module, cv, lang='en', upper=False):
    yr, d, h, m, s = calc_countdown(module, cctime.get_millis())
    if TEST_MODE:
        # Just testing various languages for now.
        texts = {
            'de': f'{yr} Jahre {d} Tage {h:02d}:{m:02d}:{s:02d}',
            'en': f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}',
            'es': f'{yr} años {d} días {h:02d}:{m:02d}:{s:02d}',
            'fr': f'{yr} ans {d} jours {h:02d}:{m:02d}:{s:02d}',
            'is': f'{yr} ár {d} dagar {h:02d}:{m:02d}:{s:02d}'
        }
        text = texts.get(lang, texts['en'])
    else:
        text = f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}'
    if upper:
        text = text.upper()
    frame.print(1, y, text, 'kairon-16', cv=cv)


def render_lifeline_module(frame, y, module, cv, lang='en', upper=False):
    if module.type == 'value':
        render_value_module(frame, y, module, cv, lang, upper)
    if module.type == 'newsfeed':
        render_newsfeed_module(frame, y, module, cv, lang, upper)


def render_value_module(frame, y, module, cv, lang='en', upper=False):
    if TEST_MODE:
        value_text = '43.5'
        unit_text = 'M km²'
        # Just testing various languages for now.
        texts = {
          'de': 'geshütztes indigenes Land',
          'en': 'indigenous protected land',
          'es': 'tierra indígena protegida',
          'fr': 'terre indigène protégée',
          'is': 'friðlýst frumbyggjaland'
        }
        label_text = texts.get(lang, texts['en'])
        if upper:
            label_text = label_text.upper()
    else:
        value_text = format_value(module, cctime.get_millis())
        for label_text in module.labels:
            label_w = frame.measure(label_text, 'kairon-10')
            for unit_text in module.unit_labels:
                value_w = frame.measure(value_text + unit_text, 'kairon-16')
                if value_w + label_w < frame.w:
                    break
            if value_w + label_w < frame.w:
                break
    x = 1
    x = frame.print(x, y, value_text + unit_text, 'kairon-16', cv=cv)
    frame.print(x + 4, y + 5, label_text, 'kairon-10', cv=cv)


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


def render_newsfeed_module(frame, y, module, cv, lang='en', upper=False):
    global newsfeed_x
    global newsfeed_index
    global headline_label
    global headline_width
    global last_newsfeed_module

    if module != last_newsfeed_module:
        headline_label = None
        last_newsfeed_module = module

    i = newsfeed_index
    n = len(module.items)
    item = module.items[i % n]

    if n == 1:
        if not headline_label:
            headline_label = frame.new_label(format_item(item), 'kairon-16')
        if headline_label.w <= DISPLAY_WIDTH:
            # There is only one headline and it fits entirely; do not scroll.
            frame.paste(0, y, headline_label, cv=cv)
            return
        headline_label = None

    if not headline_label:
        text = format_item(item) + ' \xb7 '
        headline_width = frame.measure(text, 'kairon-16')

        text_with_trail = text
        for attempt in range(3):
            i = (i + 1) % n
            item = module.items[i]
            trail = format_item(item) + ' \xb7 '
            text_with_trail += trail
            headline_label = frame.new_label(text_with_trail, 'kairon-16')
            if headline_label.w >= headline_width + DISPLAY_WIDTH:
                break

    frame.paste(newsfeed_x, y, headline_label, cv=cv)

    if newsfeed_x + headline_width < 0:
        newsfeed_x += headline_width
        newsfeed_index = (i + 1) % n
        headline_label = None
    else:
        newsfeed_x -= 3
