"""Client for the Climate Clock API.  Main entry points: load_file(), fetch().

See: https://docs.climateclock.world/climate-clock-docs/climate-clock-api
"""

import cctime
import math


def try_isoformat_to_time(data, key):
    try:
        return cctime.isoformat_to_time(data.get(key))
    except Exception as e:
        print("Field %r contains an invalid timestamp: %r" % (key, data))


def sorted_longest_first(labels):
    return sorted(labels, key=lambda label: -len(label))


class SlotRepr:
    def __repr__(self):
        cls, slots = self.__class__, []
        while cls:
            slots[:0] = getattr(cls, '__slots__', [])
            cls = cls.__bases__ and cls.__bases__[0]
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(f"{key}={repr(getattr(self, key))}" for key in slots)
        )


class Config(SlotRepr):
    __slots__ = "device_id", "module_ids", "display"

    def load(self, data):
        self.device_id = data.get("device")
        self.module_ids = data.get("modules")
        self.display = Display().load(data.get("display") or {})
        return self


class Display(SlotRepr):
    __slots__ = "deadline", "lifeline", "neutral"

    def load(self, data):
        self.deadline = Palette().load(data.get("deadline") or {})
        self.lifeline = Palette().load(data.get("lifeline") or {})
        self.neutral = Palette().load(data.get("neutral") or {})
        return self


class Palette(SlotRepr):
    __slots__ = "primary", "secondary"

    def load(self, data):
        self.primary = parse_css_color(data.get("color_primary") or None)
        self.secondary = parse_css_color(data.get("color_secondary") or None)
        return self


class Module(SlotRepr):
    __slots__ = "type", "flavor", "description", "update_time", "labels", "lang"

    def load(self, data):
        self.type = data.get("type")
        self.flavor = data.get("flavor")
        self.description = data.get("description") or ""
        self.update_time = data.get(
            "update_time", cctime.get_time() + data.get("update_interval_seconds", 3600)
        )
        # Sort labels in order from longest to shortest
        self.labels = sorted_longest_first(data.get("labels") or [])
        self.lang = data.get("lang") or "en"
        return self


class Timer(Module):
    __slots__ = ("ref_time",)

    def load(self, data):
        Module.load(self, data)
        self.ref_time = try_isoformat_to_time(data, "timestamp")
        return self


class Newsfeed(Module):
    __slots__ = ("items",)

    def load(self, data):
        Module.load(self, data)
        self.items = sorted(
            [NewsfeedItem().load(item) for item in data.get("newsfeed", [])],
            key=lambda item: -item.pub_time,
        )
        return self


class NewsfeedItem(SlotRepr):
    __slots__ = "pub_time", "headline", "headline_original", "source", "link", "summary"

    def load(self, data):
        self.pub_time = try_isoformat_to_time(data, "date")
        self.headline = data.get("headline") or ""
        self.headline_original = data.get("headline_original") or ""
        self.source = data.get("source") or ""
        self.link = data.get("link") or ""
        self.summary = data.get("summary") or ""
        return self


class Value(Module):
    __slots__ = "initial", "ref_time", "growth", "rate", "resolution", "unit_labels"

    def load(self, data):
        Module.load(self, data)
        self.initial = data.get("initial") or 0
        self.ref_time = try_isoformat_to_time(data, "timestamp")
        self.growth = data.get("growth") or "linear"
        self.rate = data.get("rate") or 0
        self.resolution = data.get("resolution") or 1
        self.unit_labels = sorted_longest_first(data.get("unit_labels") or [])

        # Convert the resolution field to some useful values.
        res, decimals, scale = self.resolution, 0, 1
        while res < 0.9:  # allow for precision error in CircuitPython floats
            res, decimals, scale = res * 10, decimals + 1, scale * 10
        self.decimals = decimals  # number of decimal places
        self.scale = scale  # scaling factor as a bigint
        return self


class Chart(Module):
    pass  # TBD


class Media(Module):
    pass  # TBD


class ClockDefinition(SlotRepr):
    __slots__ = "config", "module_dict", "modules"

    MODULE_CLASSES = {
        "timer": Timer,
        "newsfeed": Newsfeed,
        "value": Value,
        "chart": Chart,
        "media": Media,
    }

    def load(self, data):
        self.config = Config().load(data.get("config", {}))
        self.module_dict = {
            module_id: self.MODULE_CLASSES[value["type"]]().load(value)
            for module_id, value in data.get("modules", {}).items()
        }
        self.modules = [
            self.module_dict[module_id] for module_id in self.config.module_ids
        ]
        return self


def parse_css_color(color):
    if color:
        color = color.replace("#", "")
        if len(color) == 6:
            return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        if len(color) == 3:
            r, g, b = color
            return int(r + r, 16), int(g + g, 16), int(b + b, 16)


def load_file(filename):
    import json

    return ClockDefinition().load(json.load(open(filename))["data"])


def load_url(url):
    import requests

    return ClockDefinition().load(requests.get(url).json()["data"])


def fetch():
    return load_url("https://api.climateclock.world/v1/clock")
