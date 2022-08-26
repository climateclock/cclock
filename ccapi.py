"""Client for the Climate Clock API.  Main entry point is load().

See: https://docs.climateclock.world/climate-clock-docs/climate-clock-api
"""

import cctime
import gc
import json
from collections import namedtuple


Config = namedtuple('Config', ('device_id', 'module_ids', 'display'))
Display = namedtuple('Display', ('deadline', 'lifeline', 'neutral'))
Palette = namedtuple('Palette', ('primary', 'secondary'))
Item = namedtuple('Item', ('pub_millis', 'headline', 'source'))
Timer = namedtuple('Timer', ('type', 'flavor', 'labels', 'lang', 'ref_millis'))
Newsfeed = namedtuple('Newsfeed', ('type', 'flavor', 'labels', 'lang', 'items'))
Value = namedtuple('Value', ('type', 'flavor', 'labels', 'lang', 'initial', 'ref_millis', 'growth', 'rate', 'unit_labels', 'decimals', 'scale'))
Defn = namedtuple('Defn', ('config', 'module_dict', 'modules'))


def load_config(data):
    gc.collect()
    return Config(
        data.get("device"),
        data.get("modules"),
        load_display(data.get("display") or {})
    )


def load_display(data):
    gc.collect()
    return Display(
        load_palette(data.get("deadline") or {}),
        load_palette(data.get("lifeline") or {}),
        load_palette(data.get("neutral") or {})
    )


def load_palette(data):
    gc.collect()
    return Palette(
        parse_css_color(data.get("color_primary") or None),
        parse_css_color(data.get("color_secondary") or None)
    )


def load_module(data):
    gc.collect()
    return (
        data.get("type"),
        data.get("flavor"),
        # Sort labels in order from longest to shortest
        sorted_longest_first(data.get("labels") or []),
        data.get("lang") or "en"
    )


def load_timer(data):
    gc.collect()
    return Timer(*(
        load_module(data) + 
        (cctime.try_isoformat_to_millis(data, "timestamp"),)
    ))


def load_newsfeed(data):
    gc.collect()
    return Newsfeed(*(
        load_module(data) +
        (list(reversed(sorted(
            [load_newsfeed_item(item) for item in data.get("newsfeed", [])]
        ))),)
    ))


def load_newsfeed_item(data):
    gc.collect()
    return Item(
        cctime.try_isoformat_to_millis(data, "date"),
        data.get("headline") or "",
        data.get("source") or "",
    )


def format_newsfeed_item(item):
    gc.collect()
    return f'{item.headline} ({item.source})' if item.source else item.headline


def load_value(data):
    res = data.get("resolution") or 1
    decimals = 0
    scale = 1
    # Convert the resolution field to some useful values.
    while res < 0.9:  # allow for precision error in CircuitPython floats
        res, decimals, scale = res * 10, decimals + 1, scale * 10

    return Value(*(
        load_module(data) + (
            data.get("initial") or 0,
            cctime.try_isoformat_to_millis(data, "timestamp"),
            data.get("growth") or "linear",
            data.get("rate") or 0,
            sorted_longest_first(data.get("unit_labels") or []),
            decimals,  # number of decimal places
            scale  # scaling factor as a bigint
        )
    ))


def load_chart(data):
    return load_module(data)  # TBD


def load_media(data):
    return load_module(data)  # TBD


def sorted_longest_first(labels):
    return sorted(labels, key=lambda label: -len(label))


def load_clock_definition(data):
    gc.collect()
    config = load_config(data.get("config", {}))
    gc.collect()
    module_dict = {}
    for module_id, value in data.get("modules", {}).items():
        if value["type"] == "timer":
            module = load_timer(value)
        elif value["type"] == "newsfeed":
            module = load_newsfeed(value)
        elif value["type"] == "value":
            module = load_value(value)
        gc.collect()
        module_dict[module_id] = module
    return Defn(
        config,
        module_dict,
        [module_dict[module_id] for module_id in config[1]]
    )


def parse_css_color(color):
    gc.collect()
    if color:
        color = color.replace("#", "")
        if len(color) == 6:
            return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        if len(color) == 3:
            r, g, b = color
            return int(r + r, 16), int(g + g, 16), int(b + b, 16)


def load(file):
    return load_clock_definition(json.load(file)["data"])
