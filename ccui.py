"""Functions for formatting and constructing the Climate Clock display."""

import cctime
import math


def calc_deadline(module, now_time):
    t = int(module.ref_time - now_time)
    s, t = t % 60, t // 60
    m, t = t % 60, t // 60
    h, t = t % 24, t // 24
    d, t = t % 365, t // 365
    y = t
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


def format_value(module, now_time):
    elapsed_ms = int(now_time * 1000 - module.ref_time * 1000)
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


def render_deadline_module(frame, y, module, cv, lang='en'):
    yr, d, h, m, s = calc_deadline(module, cctime.get_time())
    # Just testing various languages for now.
    texts = {
        'de': f'{yr} Jahre {d} Tage {h:02d}:{m:02d}:{s:02d}',
        'en': f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}',
        'es': f'{yr} años {d} días {h:02d}:{m:02d}:{s:02d}',
        'fr': f'{yr} ans {d} jours {h:02d}:{m:02d}:{s:02d}',
        'is': f'{yr} ár {d} dagar {h:02d}:{m:02d}:{s:02d}'
    }
    text = texts.get(lang, texts['en'])
    frame.paste(1, y, frame.new_label(text, 'kairon-16', cv))


def render_lifeline_module(frame, y, module, cv, lang='en'):
    if module.type == 'value':
        render_value_module(frame, y, module, cv, lang)
    if module.type == 'newsfeed':
        render_newsfeed_module(frame, y, module, cv, lang)


def measure_text(frame, font_id, text):
    return frame.new_label(text, font_id, 0).width


def render_value_module(frame, y, module, cv, lang='en'):
    # formatted_value = format_value(module, cctime.get_time())
    formatted_value = '43.5'
    unit_text = 'M km²'
    value_label = frame.new_label(formatted_value + unit_text, 'kairon-16', cv)
    # Just testing various languages for now.
    texts = {
      'de': 'geshütztes indigenes Land',
      'en': 'indigenous protected land',
      'es': 'tierra indígena protegida',
      'fr': 'terre indigène protégée',
      'is': 'friðlýst frumbyggjaland'
    }
    text_label = frame.new_label(texts.get(lang, texts['en']), 'kairon-10', cv)
    #space = frame.w - value_label.w
    #for text in module.labels:
    #    text_label = frame.new_label(text, 'kairon-10', cv)
    #    for unit_text in module.unit_labels:
    #        unit_label = frame.new_label(unit_text + ' ', 'kairon-10', cv)
    #        if value_label.w + text_label.w + unit_label.w < frame.w:
    #            break
    x = 1
    frame.paste(x, y, value_label)
    x += value_label.w
    frame.paste(x + 4, y + 5, text_label)


def render_newsfeed_module(frame, y, module, cv):
    item = module.items[0]
    headline_label = frame.new_label(item.headline, 'kairon-10', cv)
    frame.paste(1, y, headline_label)
