import cctime
import fs
import json
from http_fetcher import HttpFetcher
import microcontroller
import os
import prefs
from unpacker import Unpacker
import utils


# All durations are measured in milliseconds.
INITIAL_DELAY = prefs.get_int('updater_initial_delay', 1000)
WIFI_DELAY = prefs.get_int('updater_wifi_delay', 3000)
FAILURE_DELAY = prefs.get_int('updater_failure_delay', 60 * 1000)
SUCCESS_DELAY = prefs.get_int('updater_success_delay', 60 * 60 * 1000)
MIN_RESTART_UPTIME = prefs.get_int('min_restart_uptime', 60 * 60 * 1000)


class SoftwareUpdater:
    def __init__(self, app, net, clock_mode):
        self.app = app
        self.net = net
        self.clock_mode = clock_mode
        self.fetcher = HttpFetcher(net)

        self.api_url = prefs.get('api_url')
        self.api_file = None
        self.api_fetched = None

        self.update_url = prefs.get('update_url')
        self.index_file = None
        self.index_name = None
        self.index_updated = None
        self.index_fetched = None
        self.index_packs = None
        self.unpacker = None

        self.retry_after(INITIAL_DELAY)

    def retry_after(self, delay):
        self.net.close()
        self.unpacker = None
        self.next_check = cctime.monotonic_millis() + delay
        self.step = self.wait_step
        utils.log(f'Next software update attempt in {delay} ms.')

    def wait_step(self):
        if cctime.monotonic_millis() > self.next_check:
            self.step = self.join_wifi_step

    def join_wifi_step(self):
        self.net.step()
        if self.net.state == 'OFFLINE' and prefs.get('wifi_ssid'):
            self.net.join(prefs.get('wifi_ssid'), prefs.get('wifi_password'))
        if self.net.state == 'ONLINE' and self.net.state_elapsed() > WIFI_DELAY:
            fc = self.app.frame_counter
            v = utils.version_dir()
            vp = ','.join(utils.versions_present())
            fv = os.uname().version.split()[0]
            now = cctime.millis_to_isoformat(cctime.get_millis())
            afetch = cctime.millis_to_isoformat(self.api_fetched) or ''
            ifetch = cctime.millis_to_isoformat(self.index_fetched) or ''
            self.fetcher.go(self.api_url +
                f'?p=ac&mac={self.net.mac_address}&up={fc.uptime()}' +
                f'&mem={utils.min_mem}&disk={fs.free()}&fps={fc.fps:.1f}' +
                f'&v={v}&vp={vp}&fv={fv}&t={now}&af={afetch}&if={ifetch}',
                prefs.get('api_etag'))
            self.step = self.api_fetch_step

    def api_fetch_step(self):
        try:
            data = self.fetcher.read()
            if data:
                if not self.api_file:
                    self.api_file = fs.open('data/clock.json.new', 'wb')
                self.api_file.write(data)
            return
        except Exception as error:
            self.net.close()
            if self.api_file:
                self.api_file.close()
                self.api_file = None

            received_new_file = False
            if isinstance(error, StopIteration):
                if error.value == 304:
                    error = None  # treat 304 Not Modified as success (no error)
                else:
                    try:
                        with fs.open('data/clock.json.new') as api_file:
                            json.load(api_file)
                        received_new_file = True
                        prefs.set('api_etag', error.value or '')
                        error = None
                    except Exception as e:
                        error = e

            if error:
                utils.report_error(error, 'API fetch failed')
            else:
                utils.log(f'API file successfully fetched!')
                self.api_fetched = cctime.get_millis()

        if received_new_file:
            fs.move('data/clock.json.new', 'data/clock.json')
            self.clock_mode.load_definition()

        self.fetcher.go(self.update_url)
        self.step = self.index_fetch_step

    def index_fetch_step(self):
        try:
            data = self.fetcher.read()
            if data:
                if not self.index_file:
                    self.index_file = fs.open('data/packs.json', 'wb')
                self.index_file.write(data)
            return
        except Exception as e:
            self.net.close()
            if self.index_file:
                self.index_file.close()
                self.index_file = None

            if not isinstance(e, StopIteration):
                utils.report_error(e, 'Index fetch aborted')
                self.retry_after(FAILURE_DELAY)
                return
        # StopIteration means fetch was successfully completed
        utils.log(f'Index file successfully fetched!')
        self.index_fetched = cctime.get_millis()
        try:
            with fs.open('data/packs.json') as index_file:
                pack_index = json.load(index_file)
            self.index_name = pack_index['name']
            self.index_updated = pack_index['updated']
            self.index_packs = pack_index['packs']
        except Exception as e:
            utils.report_error(e, 'Unreadable index file')
            self.retry_after(FAILURE_DELAY)
            return

        version = get_latest_enabled_version(self.index_packs)
        if version:
            num, url, dir_name = version
            print(f'Latest enabled version is {dir_name} at {url}.')
            if fs.isfile(dir_name + '/@VALID'):
                print(f'{dir_name} already exists and is valid.')
                self.finish_update()
            else:
                self.fetcher.go(url)
                self.unpacker = Unpacker(self.fetcher)
                self.step = self.pack_fetch_step
        else:
            print(f'No enabled versions found.')
            self.finish_update()

    def pack_fetch_step(self):
        try:
            done = self.unpacker.step()
        except Exception as e:
            utils.report_error(e, 'Pack fetch aborted')
            self.retry_after(FAILURE_DELAY)
        else:
            if done:
                self.finish_update()

    def finish_update(self):
        latest_num = write_enabled_flags(self.index_packs)
        if latest_num > utils.version_num():
            # Restart with the new version if the clock has been up long enough.
            if self.app.frame_counter.uptime()*1000 > MIN_RESTART_UPTIME:
                microcontroller.reset()
            else:
                utils.log(f'New version v{latest_num} is ready to run.')
        self.retry_after(SUCCESS_DELAY)


def get_latest_enabled_version(index_packs):
    latest = None
    for pack_name, props in index_packs.items():
        enabled = props.get('enabled')
        pack_hash = props.get('hash', '')
        url = props.get('url', '')
        try:
            assert pack_hash
            assert url
            assert pack_name.startswith('v')
            num = int(pack_name[1:].split('-')[0])
        except:
            print(f'Ignoring invalid pack entry: {pack_name}')
            continue
        if enabled:
            version = (num, url, pack_name + '.' + pack_hash)
            if not latest or version > latest:
                latest = version
    return latest


def write_enabled_flags(index_packs):
    latest_num = 0
    for pack_name, props in index_packs.items():
        enabled = props.get('enabled')
        pack_hash = props.get('hash', '')
        dir_name = pack_name + '.' + pack_hash
        if fs.isdir(dir_name):
            fs.destroy(dir_name + '/@ENABLED')
            if enabled:
                print('Enabled:', dir_name)
                with open(dir_name + '/@ENABLED', 'wb') as file:
                    pass
                usable = True
                if fs.isfile(dir_name + '/@PATH'):
                    with open(dir_name + '/@PATH') as file:
                        for dir in file.readline().split():
                            if not fs.isfile(dir + '/@VALID'):
                                usable = False
                if usable:
                    num = int(pack_name[1:].split('-')[0])
                    latest_num = max(latest_num, num)
            else:
                print('Disabled:', dir_name)
    print(f'Latest usable version: v{latest_num}')
    return latest_num
