import cctime
import fs
import json
from http_fetcher import HttpFetcher
import prefs
from unpacker import Unpacker
import utils


# All durations are measured in milliseconds.
INITIAL_DELAY = 2000  # wait this long after booting up
INTERVAL_AFTER_FAILURE = 15000  # try again after 15 seconds
INTERVAL_AFTER_SUCCESS = 30 * 60 * 1000  # recheck for updates every half hour


class SoftwareUpdater:
    def __init__(self, network, clock_mode):
        self.network = network
        self.clock_mode = clock_mode

        self.api_hostname = prefs.get('api_hostname')
        self.api_path = prefs.get('api_path')
        self.api_fetcher = None
        self.api_file = None
        self.api_fetched = None

        self.index_hostname = prefs.get('index_hostname')
        self.index_path = prefs.get('index_path')
        self.index_fetcher = None
        self.index_file = None
        self.index_name = None
        self.index_updated = None
        self.index_fetched = None
        self.index_packs = None
        self.unpacker = None

        self.retry_after(INITIAL_DELAY)

    def retry_after(self, delay):
        self.network.close_step()
        self.index_fetcher = None
        self.unpacker = None
        self.next_check = cctime.get_millis() + delay
        self.step = self.wait_step

    def wait_step(self):
        if cctime.get_millis() > self.next_check:
            self.api_fetcher = HttpFetcher(
                self.network, self.api_hostname, self.api_path)
            self.step = self.api_fetch_step

    def api_fetch_step(self):
        try:
            data = self.api_fetcher.read()
            if data:
                if not self.api_file:
                    self.api_file = fs.open('/cache/clock.json', 'wb')
                self.api_file.write(data)
            return
        except Exception as e:
            self.api_fetcher = None
            if self.api_file:
                self.api_file.close()
                self.api_file = None
            if not isinstance(e, StopIteration):
                utils.report_error(e, 'API fetch aborted')
                self.network.close_step()
                # Continue with software update anyway
                self.index_fetcher = HttpFetcher(
                    self.network, self.index_hostname, self.index_path)
                self.step = self.index_fetch_step
                return

        # StopIteration means fetch was successfully completed
        print(f'API file successfully fetched!')
        self.api_fetched = cctime.get_datetime()
        self.clock_mode.reload_definition()

        self.index_fetcher = HttpFetcher(
            self.network, self.index_hostname, self.index_path)
        self.step = self.index_fetch_step

    def index_fetch_step(self):
        try:
            data = self.index_fetcher.read()
            if data:
                if not self.index_file:
                    self.index_file = fs.open('/cache/packs.json', 'wb')
                self.index_file.write(data)
            return
        except Exception as e:
            self.index_fetcher = None
            if self.index_file:
                self.index_file.close()
                self.index_file = None
            if not isinstance(e, StopIteration):
                utils.report_error(e, 'Index fetch aborted')
                self.retry_after(INTERVAL_AFTER_FAILURE)
                return
        # StopIteration means fetch was successfully completed
        print(f'Index file successfully fetched!')
        self.index_fetched = cctime.get_datetime()
        try:
            with fs.open('/cache/packs.json') as index_file:
                pack_index = json.load(index_file)
            self.index_name = pack_index['name']
            self.index_updated = pack_index['updated']
            self.index_packs = pack_index['packs']
        except Exception as e:
            utils.report_error(e, 'Unreadable index file')
            self.retry_after(INTERVAL_AFTER_FAILURE)
            return

        version = get_latest_enabled_version(self.index_packs)
        if version:
            latest, url_path, dir_name = version
            print(f'Latest enabled version is {dir_name} at {url_path}.')
            if fs.isfile(dir_name + '/@VALID'):
                print(f'{dir_name} already exists and is valid.')
                write_enabled_flags(self.index_packs)
                self.retry_after(INTERVAL_AFTER_SUCCESS)
            else:
                self.index_fetcher = None
                self.unpacker = Unpacker(HttpFetcher(
                    self.network, self.index_hostname, url_path))
                self.step = self.pack_fetch_step

    def pack_fetch_step(self):
        try:
            done = self.unpacker.step()
        except Exception as e:
            utils.report_error(e, 'Pack fetch aborted')
            self.retry_after(INTERVAL_AFTER_FAILURE)
        else:
            if done:
                write_enabled_flags(self.index_packs)
                self.retry_after(INTERVAL_AFTER_SUCCESS)


def get_latest_enabled_version(index_packs):
    latest = None
    for pack_name, props in index_packs.items():
        enabled = props.get('enabled')
        pack_hash = props.get('hash', '')
        url_path = props.get('path', '')
        try:
            assert pack_hash
            assert url_path
            assert pack_name.startswith('v')
            num = int(pack_name[1:])
        except:
            print(f'Ignoring invalid pack entry: {pack_name}')
            continue
        if enabled:
            version = (num, url_path, pack_name + '.' + pack_hash)
            if not latest or version > latest:
                latest = version
    return latest


def write_enabled_flags(index_packs):
    for pack_name, props in index_packs.items():
        enabled = props.get('enabled')
        pack_hash = props.get('hash', '')
        dir_name = pack_name + '.' + pack_hash
        if fs.isdir(dir_name):
            fs.destroy(dir_name + '/@ENABLED')
            if enabled:
                print('Enabled:', dir_name)
                fs.write(dir_name + '/@ENABLED', b'')
            else:
                print('Disabled:', dir_name)
