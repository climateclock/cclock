"""Functions for formatting and constructing the Climate Clock display."""

import cctime

def calc_deadline(ref_time, now_time):
    t = ref_time - now_time
    s, t = t % 60, t // 60
    m, t = t % 60, t // 60
    h, t = t % 24, t // 24
    d, t = t % 365, t // 365
    y = t
    return y, d, h, m, s


def format_deadline_module(module):
    y, d, h, m, s = calc_deadline(module.ref_time, cctime.get_time())
    return f'{y} vuosi {d} päivä {h:02d}:{m:02d}:{s:02d}'
