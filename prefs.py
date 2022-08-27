import fs
import json
import utils


pairs = {
    'wifi_ssid': 'climateclock',
    'wifi_password': 'climateclock',
    'api_hostname': 'api.climateclock.world',
    'api_path': '/v1/clock',
    'index_hostname': 'zestyping.github.io',
    'index_path': '/cclock/packs.json',
    'custom_message': 'Time left before 1.5\u00b0C rise',
    'auto_cycling': None,
    'updates_paused_until': None,
    'rgb_pins': 'MTX_R1 MTX_G1 MTX_B1 MTX_R2 MTX_G2 MTX_B2',
    'addr_pins': 'MTX_ADDRA MTX_ADDRB MTX_ADDRC MTX_ADDRD',
}
get = pairs.get


def init():
    if not fs.isfile('/prefs.json'):
        print('Creating prefs.json.')
        save()
    try:
        pairs.update(json.load(fs.open('/prefs.json')))
    except Exception as e:
        utils.report_error(e, 'Could not read prefs.json.')
        save()


def set(name, value):
    if pairs.get(name) != value:
        pairs[name] = value
        save()


def save():
    try:
        with fs.open('/prefs.json.new', 'wt') as file:
            json.dump(pairs, file)
        fs.rename('/prefs.json.new', '/prefs.json')
    except OSError as e:
        utils.report_error(e, 'Could not write prefs.json.')
