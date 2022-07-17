import cctime
import json
from http_fetcher import HttpFetcher
from unpacker import Unpacker


UPDATE_INITIAL_DELAY = 2
UPDATE_INTERVAL_AFTER_FAILURE = 10
UPDATE_INTERVAL_AFTER_SUCCESS = 60


class SoftwareUpdater:
    def __init__(self, fs, network, prefs):
        self.fs = fs
        self.network = network
        self.prefs = prefs
        self.index_hostname = prefs.get('index_hostname')
        self.index_path = prefs.get('index_path')

        self.index_fetcher = None
        self.index_file = None
        self.index_name = None
        self.index_updated = None
        self.index_fetched = None
        self.index_packs = None
        self.unpacker = None

        self.retry_after(UPDATE_INITIAL_DELAY)

    def retry_after(self, delay):
        self.index_fetcher = None
        self.unpacker = None
        self.next_check = cctime.monotonic() + delay
        self.step = self.wait_step

    def wait_step(self):
        if cctime.monotonic() > self.next_check:
            self.index_fetcher = HttpFetcher(
                self.network, self.prefs, self.index_hostname, self.index_path)
            self.index_file = self.fs.open('/packs.json', 'wb')
            self.step = self.index_fetch_step

    def index_fetch_step(self):
        try:
            data = self.index_fetcher.read()
            self.index_file.write(data)
            return
        except Exception as e:
            self.index_fetcher = None
            self.index_file.close()
            self.index_file = None
            if not isinstance(e, StopIteration):
                print(f'Index fetch aborted: {e} ({repr(e)})')
                self.retry_after(UPDATE_INTERVAL_AFTER_FAILURE)
                return
        # StopIteration means fetch was successfully completed
        print(f'Index file successfully fetched!')
        self.index_fetched = cctime.get_datetime()
        try:
            with self.fs.open('/packs.json') as index_file:
                pack_index = json.load(index_file)
            self.index_name = pack_index['name']
            self.index_updated = pack_index['updated']
            self.index_packs = pack_index['packs']
        except Exception as e:
            print(f'Unreadable index file: {e} ({repr(e)})')
            self.retry_after(UPDATE_INTERVAL_AFTER_FAILURE)
            return

        version = get_latest_enabled_version(self.index_packs)
        if version:
            latest, url_path, dir_name = version
            print(f'Latest enabled version is {dir_name} at {url_path}.')
            if self.fs.isfile(dir_name + '/@VALID'):
                print(f'{dir_name} already exists and is valid.')
                write_enabled_flags(self.fs, self.index_packs)
                self.retry_after(UPDATE_INTERVAL_AFTER_SUCCESS)
            else:
                self.unpacker = Unpacker(self.fs, HttpFetcher(
                    self.network, self.prefs, self.index_hostname, url_path))
                self.step = self.pack_fetch_step

    def pack_fetch_step(self):
        try:
            done = self.unpacker.step()
        except Exception as e:
            print(f'Fetch aborted due to {e} ({repr(e)})')
            self.retry_after(UPDATE_INTERVAL_AFTER_FAILURE)
        else:
            if done:
                write_enabled_flags(self.fs, self.index_packs)
                self.retry_after(UPDATE_INTERVAL_AFTER_SUCCESS)


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


def write_enabled_flags(fs, index_packs):
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

