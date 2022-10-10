import fs
import json


pairs = {
    'wifi_ssid': 'climateclock',
    'wifi_password': 'climateclock',
    'api_url': 'https://api.climateclock.world/v2/portable_m4/clock.json',
    'update_url': 'https://zestyping.github.io/cclock/packs.json',
    'custom_message': '',
    'auto_cycling': None,
    'updates_paused_until': None,
    'updater_initial_delay': 1000,
    'updater_wifi_delay': 1000,
    'updater_failure_delay': 30 * 1000,
    'updater_success_delay': 30 * 60 * 1000,
    'min_restart_uptime': 60 * 60 * 1000,
    'rgb_pins': 'MTX_R1 MTX_G1 MTX_B1 MTX_R2 MTX_G2 MTX_B2',
    'addr_pins': 'MTX_ADDRA MTX_ADDRB MTX_ADDRC MTX_ADDRD',
}


def init():
    if not fs.isfile('data/prefs.json'):
        print('Creating prefs.json.')
        save()
    try:
        pairs.update(json.load(fs.open('data/prefs.json')))
    except Exception as e:
        print(f'Could not load /data/prefs.json: {e}')
        try:
            pairs.update(json.load(fs.open('prefs.json')))
        except Exception as e:
            print(f'Could not load /prefs.json: {e}')
        save()


def get(name):
    return pairs.get(name)


def get_int(name, val):
    try:
        return int(pairs.get(name))
    except:
        return val


def set(name, value):
    if pairs.get(name) != value:
        pairs[name] = value
        print(f'Set pref: {name} = {repr(value)}')
        save()


def save():
    try:
        with fs.open('data/prefs.json.new', 'wt') as file:
            json.dump(pairs, file)
        fs.move('data/prefs.json.new', 'data/prefs.json')
    except Exception as e:
        print(f'Could not write prefs.json: {e}')
