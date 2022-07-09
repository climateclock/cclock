"""Functions for formatting and constructing the Climate Clock display."""

import cctime
import math
try:
    import datetime
except:
    import adafruit_datetime as datetime


def calc_deadline(module, now):
    deadline = module.ref_datetime
    next_anniversary = deadline.replace(year=now.year)
    if next_anniversary < now:
        next_anniversary = deadline.replace(year=now.year + 1)
    y = deadline.year - next_anniversary.year
    t = int((next_anniversary - now).total_seconds())
    s, t = t % 60, t // 60
    m, t = t % 60, t // 60
    h, d = t % 24, t // 24
    return y, d, h, m, s


def to_bigint(f, scale):
    mantissa, exponent = math.frexp(f)
    # CircuitPython floats have 22 bits of mantissa
    scaled = int(mantissa * (1<<22)) * scale
    if exponent > 0:
        scaled = scaled * (1<<exponent)
    else:
        scaled = scaled // (1<<-exponent)
    return scaled // (1<<22)


def format_value(module, now):
    elapsed_ms = int((now - module.ref_datetime).total_seconds() * 1000)
    if module.growth == 'linear':
        scale = module.scale * 10000000  # 22 bits = about 7 decimal places
        decimals = module.decimals + 7

        scaled_initial = to_bigint(module.initial, scale)
        scaled_rate = to_bigint(module.rate, scale)
        scaled_value = scaled_initial + scaled_rate * elapsed_ms // 1000
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
    yr, d, h, m, s = calc_deadline(module, cctime.get_datetime())
    # Just testing various languages for now.
    texts = {
        'de': f'{yr} Jahre {d} Tage {h:02d}:{m:02d}:{s:02d}',
        'en': f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}',
        'es': f'{yr} años {d} días {h:02d}:{m:02d}:{s:02d}',
        'fr': f'{yr} ans {d} jours {h:02d}:{m:02d}:{s:02d}',
        'is': f'{yr} ár {d} dagar {h:02d}:{m:02d}:{s:02d}'
    }
    text = texts.get(lang, texts['en'])
    if upper:
        text = text.upper()
    frame.paste(2, y, frame.new_label(text, 'kairon-16'), cv=cv)


def render_lifeline_module(frame, y, module, cv, lang='en', upper=False):
    if module.type == 'value':
        render_value_module(frame, y, module, cv, lang, upper)
    if module.type == 'newsfeed':
        render_newsfeed_module(frame, y, module, cv, lang, upper)


def render_value_module(frame, y, module, cv, lang='en', upper=False):
    # formatted_value = format_value(module, cctime.get_datetime())
    formatted_value = '43.5'
    unit_text = 'M km²'
    value_label = frame.new_label(formatted_value + unit_text, 'kairon-16')
    # Just testing various languages for now.
    texts = {
      'de': 'geshütztes indigenes Land',
      'en': 'indigenous protected land',
      'es': 'tierra indígena protegida',
      'fr': 'terre indigène protégée',
      'is': 'friðlýst frumbyggjaland'
    }
    text = texts.get(lang, texts['en'])
    if upper:
        text = text.upper()
    text_label = frame.new_label(text, 'kairon-10')
    #space = frame.w - value_label.w
    #for text in module.labels:
    #    text_label = frame.new_label(text, 'kairon-10')
    #    for unit_text in module.unit_labels:
    #        unit_label = frame.new_label(unit_text + ' ', 'kairon-10')
    #        if value_label.w + text_label.w + unit_label.w < frame.w:
    #            break
    x = 1
    frame.paste(x, y, value_label, cv=cv)
    x += value_label.w
    frame.paste(x + 4, y + 5, text_label, cv=cv)


DISPLAY_WIDTH = 192
newsfeed_x = DISPLAY_WIDTH
newsfeed_index = 0
headline_label = None
headline_width = None

def render_newsfeed_module(frame, y, module, cv, lang='en', upper=False):
    global newsfeed_x
    global newsfeed_index
    global headline_label
    global headline_width

    i = newsfeed_index
    n = len(module.items)

    if not headline_label:
        item = module.items[i]
        text = f'{item.headline} ({item.source}) \xb7 '
        if upper:
            text = text.upper()
        headline_width = frame.new_label(text, 'kairon-16').w

        text_with_trail = text
        while True:
            i = (i + 1) % n
            item = module.items[i]
            trail = f'{item.headline} ({item.source}) \xb7 '
            if upper:
                trail = trail.upper()
            text_with_trail += trail
            headline_label = frame.new_label(text_with_trail, 'kairon-16')
            if headline_label.w >= headline_width + DISPLAY_WIDTH:
                break

    frame.paste(newsfeed_x, y, headline_label, cv=cv)

    if newsfeed_x + headline_width < 0:
        newsfeed_x = 0
        newsfeed_index = (i + 1) % n
        headline_label = None
    else:
        newsfeed_x -= 1
