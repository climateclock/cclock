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


def render_deadline_module(frame, y, module, cv):
    yr, d, h, m, s = calc_deadline(module, cctime.get_time())
    text = f'{yr} years {d} days {h:02d}:{m:02d}:{s:02d}'
    frame.paste(1, y, frame.new_label(text, 'kairon-16', cv))


def render_lifeline_module(frame, y, module, cv):
    if module.type == 'value':
        render_value_module(frame, y, module, cv)
    if module.type == 'newsfeed':
        render_newsfeed_module(frame, y, module, cv)


def measure_text(frame, font_id, text):
    return frame.new_label(text, font_id, 0).width


def render_value_module(frame, y, module, cv):
    formatted_value = format_value(module, cctime.get_time())
    value_label = frame.new_label(formatted_value, 'kairon-16', cv)
    space = frame.w - value_label.w
    for text in module.labels:
        text_label = frame.new_label(text, 'kairon-10', cv)
        for unit_text in module.unit_labels:
            unit_label = frame.new_label(unit_text + ' ', 'kairon-10', cv)
            if value_label.w + text_label.w + unit_label.w < frame.w:
                break
    x = 1
    frame.paste(x, y, value_label)
    x += value_label.w
    frame.paste(x, y + 5, unit_label)
    x += unit_label.w
    frame.paste(x, y + 5, text_label)


def render_newsfeed_module(frame, y, module, cv):
    item = module.items[0]
    headline_label = frame.new_label(item.headline, 'kairon-10', cv)
    frame.paste(1, y, headline_label)
