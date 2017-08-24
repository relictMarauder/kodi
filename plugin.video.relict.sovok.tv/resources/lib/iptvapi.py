import sys
import os
import xbmc
import copy
import fscache
import re
from datetime import timedelta
from datetime import datetime
from datetime import date
import time
from requests import requests
from  epg_db import epg_db

__author__ = 'Alexander Bonelis'

__version__ = '0.10'

IPTV_DOMAIN = 'api.sovok.tv'
IPTV_API = 'http://%s/v2.3/json/%%s' % IPTV_DOMAIN
IPTV_API_HTTPS = 'https://%s/v2.3/json/%%s' % IPTV_DOMAIN
ARCHIVE_TIME_PREFIX = 5 * 60 * 1000

TIMZONE_REGEXP = re.compile(r'((?P<hours>[-+]\d\d):)?((?P<minutes>\d+?):)?((?P<seconds>\d\d))?')
CACHE_TIME_CHANNEL_LIST = 60 * 24
CACHE_TIME_STREAMERS_LIST = 180
CACHE_TIME_CHANNEL_EPG = 60 * 24
CACHE_TIME_DAY_EPG = 60 * 24
SESSION_TIMEOUT_MIN = 180
TIME_ZONES = [u'-12:00:00',
              u'-11:00:00',
              u'-10:00:00',
              u'-09:00:00',
              u'-08:00:00',
              u'-07:00:00',
              u'-06:00:00',
              u'-05:00:00',
              u'-04:00:00',
              u'-03:00:00',
              u'-02:00:00',
              u'-01:00:00',
              u'+00:00:00',
              u'+01:00:00',
              u'+02:00:00',
              u'+03:00:00',
              u'+04:00:00',
              u'+05:00:00',
              u'+06:00:00',
              u'+07:00:00',
              u'+08:00:00',
              u'+09:00:00',
              u'+10:00:00',
              u'+11:00:00',
              u'+12:00:00',
              u'+13:00:00',
              u'+14:00:00'
              ]
STORAGE_KEY_LOGIN_INFO = u'loginInfo'

# channel_list_cache_it = fscache.FSCache(xbmc.translatePath('special://temp/relict.sovok.tv/channelList'), days=1)
# epg_cache_it = fscache.FSCache(xbmc.translatePath('special://temp/relict.sovok.tv/epg'), days=7)
# ch_epg_cache_it = fscache.FSCache(xbmc.translatePath('special://temp/relict.sovok.tv/ch_epg'), days=7)
# login_info_cache_it = fscache.FSCache(xbmc.translatePath('special://temp/relict.sovok.tv/login_info'), days=1)
settings_cache_it = fscache.FSCache(xbmc.translatePath('special://temp/relict.sovok.tv/settings'), hours=1)


class SovokApi:
    def __init__(self, plugin):
        self.plugin = plugin
        self.day_epg_cache = None
        self.db = epg_db()

    def gen_ua(self):
        ver_info = sys.version_info
        python_version = '%s.%s.%s' % (ver_info[0], ver_info[1], ver_info[2])
        osname = '%s %s; %s' % (os.name, sys.platform, python_version)

        is_xbmc = 'Relict-XBMC'
        if getattr(xbmc, "nonXBMC", None) is not None:
            is_xbmc = 'Relict-nonXBMC'

        ua = '%s/%s (%s; %s)  iptv/%s user/%s' % (
            is_xbmc, xbmc.getInfoLabel('System.BuildVersion').split(" ")[0], xbmc.getInfoLabel('System.BuildVersion'),
            osname, __version__, '---')
        ua = 'Relict-XBMC/16.1-RC2 (16.1-RC2 Git:20160328-be20e8a; nt win32; 2.7.8)  iptv/0.10 user/---'
        self.plugin.log('[sovok.TV] UA: %s' % ua)
        return ua

    def get_login_info(self):
        return self.db.get_login_info()

    def set_login_info(self, login_info):
        self.db.set_login_info(login_info)

    def is_authenticated(self):
        login_info = self.get_login_info()
        if login_info is not None:
            login_time = login_info[u'login_time']
            login_time += timedelta(minutes=SESSION_TIMEOUT_MIN)
            if login_time < datetime.now():  # Session TimeOut
                self.plugin.log('Sessions timeout -> clean session', xbmc.LOGWARNING)
                self.db.clear_login_info()
                return False
            else:
                return True
        else:
            return False

    def clear_cache(self):
        self.plugin.log('Cleaning cache ... ')
        # channel_list_cache_it.purge()
        # epg_cache_it.purge()
        # ch_epg_cache_it.purge()
        self.db.clear()
        settings_cache_it.purge()

    def is_login_changed(self):
        login_info = self.get_login_info()
        if login_info is not None:
            return \
                login_info[u'login'] != self.plugin.get_setting('login') \
                and \
                login_info[u'pwd'] != self.plugin.get_setting('password')
        return False  # no LoginInfo are stored

    def logout(self):
        self.plugin.log(u'Logout: Remove Session info')
        if self.get_login_info() is not None:
            self._send_request(u'logout')
            self.db.clear_login_info()

    def is_clean_cache_needed(self):
        return self.is_login_changed()

    def send_request(self, action, params=None):
        if self.is_login_changed():
            self.plugin.log(u'New credentials detected')
            self.logout()
        if not self.is_authenticated():  # user is not authenticated
            self.do_authentication()
        return self._send_request(action, params)

    def _send_request(self, action, params=None):
        self.plugin.log(u'Send request for action: %s ' % action)
        if params is None:
            cloned_params = {}
        else:
            cloned_params = copy.deepcopy(params)

        login_info = self.get_login_info()
        if login_info is not None:
            cloned_params[login_info[u'sid_name']] = login_info[u'sid']

        r = requests.get(IPTV_API % action, cloned_params,
                         headers={
                             'User-Agent': self.gen_ua(),
                             'Accept-Encoding': 'identity, deflate, compress, gzip'
                         })
        self.plugin.log('response retrieved %s' % r.elapsed)
        json_response = r.json()
        if u'error' in json_response:
            error_code = json_response[u'error'][u'code']
            if error_code == 12:
                self.plugin.log(u'You are not logged, try to login', xbmc.LOGWARNING)
                self.do_authentication()
                return self.send_request(action, params)
            else:
                self.plugin.log(u"Response Error for %s: code - %s, message - %s" % (
                    action,
                    json_response[u'error'][u'code'], json_response[u'error'][u'message']), xbmc.LOGERROR)
                raise ValueError(u"Response Error: code - %s, message - %s" % (
                    json_response[u'error'][u'code'], json_response[u'error'][u'message']))
        return json_response

    def do_authentication(self):
        login = self.plugin.get_setting(u'login')
        pwd = self.plugin.get_setting(u'password')
        if login is None or login == '':
            self.plugin.log(u'Login is not defined, using default login', xbmc.LOGWARNING)
            # use default logn/password
            login = '1111'
            pwd = '1111'
            self.plugin.set_setting('login', login)
            self.plugin.set_setting('password', pwd)
        if login is not None or login != '':
            # try:
            login_response = self._send_request('login', {'login': login, 'pass': pwd})
            login_info = {
                u'login': login,
                u'pwd': pwd,
                u'login_time': datetime.now(),
                u'sid': login_response[u'sid'],
                u'sid_name': login_response[u'sid_name']}
            self.set_login_info(login_info)
            return True
        return False

    def _get_channel_list(self):
        return self.send_request(u'channel_list', None)

    def _get_archive_channels_list(self):
        return self.send_request(u'archive_channels_list', None)

    def _get_favorites(self):
        return self.send_request(u'favorites', None)

    def get_favorites_list(self):
        remote_favorites = self._get_favorites()
        ch_list = []
        for fav in remote_favorites[u'favorites']:
            ch_list.append(self.get_channel(fav[u'channel_id']))
        return ch_list

    def get_groups_list(self):
        groups = self.db.get_groups()
        if groups is None:
            ch_list = self._get_channel_list()
            self.db.import_channel_list(ch_list)
            groups = self.db.get_groups()
        return groups

    def get_channel_list(self, group_id=None):
        group = self.db.get_group(group_id)
        if group is None:
            ch_list = self._get_channel_list()
            self.db.import_channel_list(ch_list)
            group = self.db.get_group(group_id)
        return group

    def get_archive_hours(self, channel_id):
        archive_hours = self.db.get_archive_hours(channel_id)
        self.plugin.log(u'First retrieving archive hours for channel %s :%s ' % (channel_id, archive_hours))
        if archive_hours is None or archive_hours == 0:
            archive_channels_list = self._get_archive_channels_list()
            self.db.import_archive_channels_list(archive_channels_list)
            archive_hours = self.db.get_archive_hours(channel_id)
            self.plugin.log(u'Second retrieving archive hours for channel %s :%s ' % (channel_id, archive_hours))
        return 0 if archive_hours is None else archive_hours

    def get_channel(self, channel_id):
        group, channel = self.db.get_channel(channel_id)
        if group is None:
            ch_list = self._get_channel_list()
            self.db.import_channel_list(ch_list)
            group, channel = self.db.get_channel(channel_id)
        return group, channel

    def _get_day_epg(self, day):
        start_time = datetime(year=day.year, month=day.month, day=day.day) \
                     + timedelta(hours=2)
        d_time = time.mktime(start_time.timetuple())
        all_epg_cache = self.send_request(u'epg3',
                                          {
                                              u'dtime': d_time,
                                              u'period': 26
                                          })
        return all_epg_cache

    def get_day_epg(self, day):
        all_epg_cache = self._get_day_epg(day)
        return all_epg_cache

    # def get_channel_epg_from_cache(self, channel_id, day, all_epg_cache):
    #     all_epg = all_epg_cache[u'epg3']
    #     self.day_epg_cache = all_epg
    #     ch_epg = self.get_channel_epg(channel_id, day)
    #     self.day_epg_cache = None
    #     return ch_epg

    def get_channel_epg(self, channel_id, day):
        if not self.db.is_channel_epg_loaded(channel_id, day):
            epg_list = self._get_channel_epg(channel_id, day)
            self.db.import_epg([{u'epg': epg_list[u'epg'], u'id': channel_id}])
            self.db.mark_channel_day(channel_id, day)
        epgs = self.db.get_day_epg(channel_id, day)
        if epgs is None:
            epgs = []
        return {u'epg': epgs}

    def _get_channel_epg(self, channel_id, day):
        start_time = datetime(year=day.year, month=day.month, day=day.day).strftime(u'%d%m%y')
        return self.send_request(u'epg',
                                 {
                                     u'cid': channel_id,
                                     u'day': start_time
                                 })

    def get_current_epg(self, channel_id, epg_cache=None):
        if not self.db.is_full_day_loaded():
            epg_list = self._get_day_epg(date.today())
            self.db.import_epg(epg_list[u'epg3'])
            self.db.mark_full_day(date.today())
        epg_item = self.db.get_current_prog(channel_id)
        return epg_item

    def get_live_url(self, channel_id, time_shift):
        if time_shift is not None:
            return self.get_timeshifted_live_url(channel_id, time_shift)
        result = self.send_request(u'get_url', {u'cid': channel_id, u'protect_code': '0000'})
        return result[u'url']

    def get_archive_next_url(self, channel_id, timestamp):
        # result = self.send_request(u'archive_next2', {u'cid': channel_id, u'time': int(timestamp)})
        # return result[u'archive'][u'url']
        result = self.send_request(u'get_url', {u'cid': channel_id, u'gmt': int(timestamp)})
        return result[u'url']

    @staticmethod
    def find_timezone_index(time_zone):
        for i in range(len(TIME_ZONES)):
            if TIME_ZONES[i] == time_zone:
                return i
        return None

    def get_timeshifted_live_url(self, channel_id, time_shift):
        settings = self.get_setting(None)
        time_zone = settings[u'timezone']
        time_zone_index = self.find_timezone_index(time_zone)
        # new_tmp_time_zone = TIME_ZONES[time_zone_index - int(time_shift)]
        # self.set_setting(u'timezone', new_tmp_time_zone[0:6])
        url = self.get_live_url(channel_id, None)
        # self.set_setting(u'timezone', time_zone[0:6])
        return url

    def get_streamers(self):
        result = self.send_request(u'streamers')
        return result[u'streamers']

    @settings_cache_it(True)
    def get_setting(self, _type):
        result = self.send_request(u'settings')

        return result[u'settings']

    @staticmethod
    def parseTimeDelta(s):
        if s is None:
            return None
        d = TIMZONE_REGEXP.match(str(s)).groupdict(0)
        return timedelta(**dict(((key, int(value))
                                 for key, value in d.items())))

    def get_time_zone(self):
        time_zone = self.get_setting(None)[u'timezone']
        return self.parseTimeDelta(time_zone)

    def set_channel_to_favorites(self, channel_id):
        result = self.send_request(u'favorites_set', ({u'cid': channel_id}))
        return result

    def set_setting(self, _type, value):
        self.plugin.log(u'Set setting %s to %s ' % (_type, value))
        result = self.send_request(u'settings_set', ({_type: value}))
        settings_cache_it.purge()
        return result
