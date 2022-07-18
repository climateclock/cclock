import json
import utils


class Prefs:
    def __init__(self, fs):
        self.fs = fs
        try:
            self.prefs = json.load(self.fs.open('/prefs.json'))
        except Exception as e:
            utils.report_error(e, f'Could not read prefs.json')
            self.prefs = {
                'wifi_ssid': 'climateclock',
                'wifi_password': 'climateclock',
                'index_hostname': 'zestyping.github.io',
                'index_path': '/cclock/packs.json'
            }
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
