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
Timer = namedtuple('Timer', ('id', 'type', 'flavor', 'labels', 'ref_millis'))
Newsfeed = namedtuple('Newsfeed', ('id', 'type', 'flavor', 'labels', 'items'))
Value = namedtuple('Value', ('id', 'type', 'flavor', 'labels', 'initial', 'ref_millis', 'growth', 'rate', 'unit_labels', 'decimals', 'scale'))
Defn = namedtuple('Defn', ('config', 'module_dict', 'modules'))


def sorted_by_length(labels):
    return sorted(labels or [], key=lambda label: -len(label))


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


def parse_css_color(color):
    gc.collect()
    color = (color or "").replace("#", "")
    if len(color) == 6:
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def load_timer(id, data):
    gc.collect()
    return Timer(
        id,
        data.get("type"),
        data.get("flavor"),
        sorted_by_length(data.get("labels")),
        cctime.try_isoformat_to_millis(data, "timestamp")
    )


def load_newsfeed(id, data):
    gc.collect()
    return Newsfeed(
        id,
        data.get("type"),
        data.get("flavor"),
        sorted_by_length(data.get("labels")),
        list(reversed(sorted(
            [load_item(item) for item in data.get("newsfeed", [])]
        )))
    )


def load_item(data):
    gc.collect()
    return Item(
        cctime.try_isoformat_to_millis(data, "date"),
        data.get("headline") or "",
        data.get("source") or "",
    )


def load_value(id, data):
    res = data.get("resolution") or 1
    decimals = 0
    scale = 1
    # Convert the resolution field to some useful values.
    while res < 0.9:  # allow for precision error in CircuitPython floats
        res, decimals, scale = res * 10, decimals + 1, scale * 10

    return Value(
        id,
        data.get("type"),
        data.get("flavor"),
        sorted_by_length(data.get("labels")),
        data.get("initial") or 0,
        cctime.try_isoformat_to_millis(data, "timestamp"),
        data.get("growth") or "linear",
        data.get("rate") or 0,
        sorted_by_length(data.get("unit_labels")),
        decimals,  # number of decimal places
        scale  # scaling factor as a bigint
    )


def load_defn(data):
    gc.collect()
    config = load_config(data.get("config", {}))
    gc.collect()
    module_dict = {}
    for module_id, value in data.get("modules", {}).items():
        if value["type"] == "timer":
            module = load_timer(module_id, value)
        elif value["type"] == "newsfeed":
            module = load_newsfeed(module_id, value)
        elif value["type"] == "value":
            module = load_value(module_id, value)
        gc.collect()
        module_dict[module_id] = module
    return Defn(
        config,
        module_dict,
        [module_dict[module_id] for module_id in config[1]]
    )


def load(file):
    return load_defn(json.load(file)["data"])
