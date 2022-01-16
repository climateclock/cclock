import cctime
import requests


def log(message, *args):
    print(message % args)


def try_isoformat_to_time(data, key):
    try:
        return cctime.isoformat_to_time(data.get(key))
    except Exception as e:
        log("Field %r contains an invalid timestamp: %r", key, data)


class SlotRepr:
    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(f"{key}={getattr(self, key)!r}" for key in self.__slots__),
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
        self.primary = data.get("color_primary") or None
        self.secondary = data.get("color_secondary") or None
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
        self.labels = sorted(data.get("labels") or [], key=lambda label: -len(label))
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
        self.source = data.get("source")
        self.link = data.get("link")
        self.summary = data.get("summary") or ""
        return self


class Value(Module):
    __slots__ = "initial", "start_time", "growth", "resolution", "unit_labels"

    def load(self, data):
        Module.load(self, data)
        self.initial = data.get("initial") or 0
        self.start_time = try_isoformat_to_time(data, "timestamp")
        self.growth = data.get("growth") or "linear"
        self.resolution = data.get("resolution") or 1
        self.unit_labels = sorted(
            data.get("unit_labels") or [], key=lambda label: -len(label)
        )
        return self


class Chart(Module):
    pass  # TBD


class Media(Module):
    pass  # TBD


class Clock(SlotRepr):
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


def fetch():
    response = requests.get("https://api.climateclock.world/v1/clock")
    return Clock().load(response.json()["data"])
