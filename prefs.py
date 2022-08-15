import json
import utils


DEFAULTS = {
    'wifi_ssid': 'climateclock',
    'wifi_password': 'climateclock',
    'api_hostname': 'api.climateclock.world',
    'api_path': '/v1/clock',
    'index_hostname': 'zestyping.github.io',
    'index_path': '/cclock/packs.json',
    'custom_message': 'Time left before 1.5\u00b0C rise',
    'updates_paused_until': None
}


class Prefs:
    def __init__(self, fs):
        self.fs = fs
        self.prefs = DEFAULTS.copy()
        try:
            self.prefs.update(json.load(self.fs.open('/prefs.json')))
        except Exception as e:
            utils.report_error(e, f'Could not read prefs.json')
            self.save()
        self.get = self.prefs.get

    def set(self, name, value):
        if self.prefs.get(name) != value:
            self.prefs[name] = value
            self.save()

    def save(self):
        try:
            with self.fs.open('/prefs.json.new', 'wt') as file:
                json.dump(self.prefs, file)
            self.fs.rename('/prefs.json.new', '/prefs.json')
        except OSError as e:
            utils.report_error(e, f'Could not write prefs.json')
