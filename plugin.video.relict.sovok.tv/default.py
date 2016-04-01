from datetime import datetime
from datetime import date
import traceback
from resources.lib.debug import RemoteDebug
from resources.lib.iptvapi import SovokApi
from resources.lib.relictPlugin import RelictPlugin
import re
import time
import xbmc
import xbmcgui
import xbmcaddon
import sys
import os
import subprocess
import codecs

debug = RemoteDebug(False)
debug.start()

# Create plugin instance
plugin = RelictPlugin()
sovok = SovokApi(plugin)

"""
        listing = [{    'label': 'Label',
                        'label2': 'Label 2',
                        'thumb': 'thumb.png',
                        'icon': 'icon.png',
                        'fanart': 'fanart.jpg',
                        'art': {'clearart': 'clearart.png'},
                        'stream_info': {'video': {'codec': 'h264', 'duration': 1200},
                                        'audio': {'codec': 'ac3', 'language': 'en'}},
                        'info': {'video': {'genre': 'Comedy', 'year': 2005}},
                        'context_menu': ([('Menu Item', 'Action')], True),
                        'url': 'plugin:/plugin.video.test/?action=play',
                        'is_playable': True,
                        'is_folder': False,
                        'subtitles': ['/path/to/subtitles.en.srt', '/path/to/subtitles.uk.srt'],
                        'mime': 'video/mp4'
                        }]
"""


def _resolve_color(color=False):
    # if color and color in self.COLORSCHEMA:
    #    return self.COLORSCHEMA[color]

    if color:
        p = re.compile('^#')
        if re.match(p, str(color)):
            return re.sub(p, 'ee', str(color))

    return u'eeffffff'  # almost white


def _resolve_icon_url(channel):
    icon = u'DefaultAddonLibrary.png'
    if channel and u'icon' in channel:
        icon = channel[u'icon']
        if icon[:4] != u'http':
            icon = u'http://%s%s' % (u'sovok.tv', icon)
    return icon


def get_time_label(prog_start):
    return (datetime.utcfromtimestamp(prog_start) + sovok.get_time_zone()).strftime(u'%H:%M')


def list_day_epg_entries(params):
    channel_id = params[u'channel_id']
    day_str = params[u'day']
    day = datetime.fromtimestamp(float(day_str))
    group, channel = sovok.get_channel(channel_id)
    result_epg = sovok.get_channel_epg(channel_id, day)
    epg_list = []
    if u'epg' in result_epg:
        epg_list = result_epg[u'epg']
    icon = _resolve_icon_url(channel)
    listing = []
    counter = 0
    current_prog = False
    for epg_item in epg_list:
        program = ""
        counter += 1
        if u'progname' in epg_item:
            program = epg_item[u'progname']
        program += "\n"
        prog, desc = program.split("\n", 1)
        prog_start = int(epg_item['ut_start'])
        time_label = get_time_label(prog_start)
        can_play = True
        if can_play:
            if prog_start > time.time():
                can_play = False
        title = '%s %s %s' % (time_label, prog, desc)
        if prog_start < time.time():
            if not current_prog:
                if len(epg_list) > counter:
                    p = epg_list[counter]
                    if int(p['ut_start']) > time.time():
                        title = '[B][COLOR green]%s[/COLOR][/B]' % title
                        current_prog = counter
            pass
        else:
            title = '[I]%s[/I]' % title
        listing.append({
            u'label': title,
            u'label2': desc,
            u'url': plugin.get_url(action=u'archive_stream', start_time=prog_start, channel_id=channel_id),
            u'thumb': icon,
            u'icon': icon,
            u'fanart': icon,
            u'is_playable': True,
            u'context_menu': get_default_context_menu(u'list_day_epg', params,
                                                      {u'name': prog,
                                                       u'start_time': prog_start,
                                                       u'channel_id': channel_id})
        })
    context = plugin.create_listing(listing)
    # if current_prog:
    #    context[u'focus_item_idx'] = current_prog
    return context


def list_channel_time_shift_entries(params):
    channel_id = params[u'channel_id']
    group, channel = sovok.get_channel(channel_id)
    icon = _resolve_icon_url(channel)
    listing = [{
        # u'label': u'[COLOR %s]%s[/COLOR]' % (_resolve_color(group[u'color']), channel[u'name']),
        u'label': u'{0:s}'.format(channel[u'name']),
        u'url': plugin.get_url(action=u'live_stream', channel_id=channel[u'id']),
        u'thumb': icon,
        u'icon': icon,
        u'fanart': icon,
        u'is_playable': True,
        u'context_menu': get_default_context_menu(u'list_channel', params)
    }]
    for i in range(1, 12):
        listing.append({
            # u'label': u'[COLOR %s]%s[/COLOR]' % (_resolve_color(group[u'color']), channel[u'name']),
            u'label': u'-%s: %s' % (str(i), channel[u'name']),
            u'url': plugin.get_url(action=u'live_stream', channel_id=channel[u'id'], timeshift=i),
            u'thumb': icon,
            u'icon': icon,
            u'fanart': icon,
            u'is_playable': True,
            u'context_menu': get_default_context_menu(u'list_channel', params)
        })
    return listing


def get_live_channel_entry(channel, epg_cache=None):
    label = channel[u'name']
    if channel[u'epg_start'] is not u'' and channel[u'epg_start'] is not None or channel[u'have_archive'] == 1:
        epg_item = sovok.get_current_epg(channel[u'id'], epg_cache)

        if epg_item is not None:
            program = u''
            if u'progname' in epg_item:
                program = epg_item[u'progname']
            program += u"\n"
            prog, desc = program.split(u"\n", 1)
            prog_start = int(epg_item[u'ut_start'])
            time_label = get_time_label(prog_start)
            epg_str = u'%s %s %s' % (time_label, prog, desc)
            label = u'%s : %s' % (label, epg_str)

    icon = _resolve_icon_url(channel)
    return {
        # u'label': u'[COLOR %s]%s[/COLOR]' % (_resolve_color(group[u'color']), channel[u'name']),
        u'label': label,
        u'url': plugin.get_url(action=u'live_stream', channel_id=channel[u'id']),
        u'thumb': icon,
        u'icon': icon,
        u'fanart': icon,
        u'is_playable': True
    }


def list_channel_entries(params):
    channel_id = params[u'channel_id']
    group, channel = sovok.get_channel(channel_id)
    icon = _resolve_icon_url(channel)
    listing = []
    live_entry = get_live_channel_entry(channel)
    live_entry[u'context_menu'] = get_default_context_menu(u'list_channel', params)
    listing.append(live_entry)
    day = date.today()
    for i in range(7):
        listing.append({
            # u'label': u'[COLOR %s]%s[/COLOR]' % (_resolve_color(group[u'color']), day.strftime('%A %d/%m/%y')),
            u'label': day.strftime('%A %d/%m/%y'),
            u'url': plugin.get_url(action=u'list_day_epg', channel_id=channel[u'id'],
                                   day=str(time.mktime(day.timetuple()))),
            u'thumb': icon,
            u'icon': icon,
            u'fanart': icon,
            u'context_menu': get_default_context_menu(u'list_channel', params)
        })
        day = date.fromordinal(day.toordinal() - 1)
    return listing


def list_group_entries(params):
    group_id = ''
    if u'group' in params:
        group_id = params[u'group']
    channel_list = sovok.get_channel_list(group_id)
    listing = []
    # epg_cache = sovok.get_day_epg(date.today())
    epg_cache = None
    for channel in channel_list[u'channels']:
        prefix = u''
        url = plugin.get_url(action=u'live_stream',
                             channel_id=channel[u'id'])
        is_playable = True
        if u'have_archive' in channel:
            if channel[u'have_archive'] == u'1':
                prefix = '*'
                url = plugin.get_url(action=u'list_channel',
                                     channel_id=channel[u'id'])
                is_playable = False
        live_entry = get_live_channel_entry(channel, epg_cache)
        live_entry[u'context_menu'] = get_default_context_menu(u'list_group', params)
        live_entry[u'is_playable'] = is_playable
        live_entry[u'label'] = u'%s %s %s' % (prefix, live_entry[u'label'], prefix)
        live_entry[u'url'] = url
        listing.append(live_entry)
    plugin.log('end generate list')
    return listing


def list_root_entries(params):
    groups_obj = sovok.get_groups_list()
    listing = []
    for group in groups_obj:
        if u'100' not in group[u'id']:
            listing.append({
                u'label': u'[COLOR %s]%s[/COLOR]' % (_resolve_color(group[u'color']), group[u'name']),
                u'url': plugin.get_url(action=u'list_group', group=group[u'id']),
                u'context_menu': get_default_context_menu(u'list_root', params)
            })
    listing.append({
        u'label': u'All',
        u'url': plugin.get_url(action=u'list_group', group=None),
        u'context_menu': get_default_context_menu(u'list_root', params)
    })

    return listing


def play_live_stream(params):
    channel_id = params[u'channel_id']
    if u'timeshift' in params:
        time_shift = params[u'timeshift']
    else:
        time_shift = None
    live_url = sovok.get_live_url(channel_id, time_shift)
    clean_url = re.sub('http/ts(.*?)\s(.*)', u'http\\1', live_url)
    return clean_url


def play_archive_stream(params):
    channel_id = params[u'channel_id']
    start_time = params[u'start_time']
    live_url = sovok.get_archive_next_url(channel_id, start_time)
    clean_url = re.sub('http/ts(.*?)\s(.*)', u'http\\1', live_url)
    return clean_url


def download_archive_stream(params):
    plugin.log(params)
    name = params[u'name']
    url = play_archive_stream(params).encode('UTF-8')

    temporary_path = xbmc.translatePath(xbmcaddon.Addon(id='plugin.video.relict.sovok.tv').getAddonInfo("profile"))
    tmp_file = os.path.join(temporary_path.decode("utf-8"), "tmp_download.cmd")

    with codecs.open(tmp_file, "w", "cp1251") as temp:
        temp.write('\nchcp 1251')
        temp.write((u"\nwget -t20 -T 240 -O \"q:\\%s\" \"%s\"" % (
            name.decode('utf-8').replace('/', '-').replace(':', '-').replace('"', '_') + '.mp4', url)))
    subprocess.Popen(tmp_file)


def clear_cache(params):
    sovok.clear_cache()
    sovok.logout()
    refresh_url = plugin.get_plugin_url()
    if u'currentUrl' in params:
        refresh_url += params[u'currentUrl']
    xbmc.executebuiltin('XBMX.Container.Refresh(%s)' % refresh_url)


def select_streamer(params):
    streamers = sovok.get_streamers()
    selected_streamer = sovok.get_setting(u'streamer')[u'streamer']
    dialog = xbmcgui.Dialog()
    selection = []
    for server in streamers:
        if selected_streamer == server[u'id']:
            selection.append('* ' + server[u'name'])
        else:
            selection.append(server[u'name'])
    ret = dialog.select(u'Streamers', selection)
    if ret > -1:
        sovok.set_setting(u'streamer', streamers[ret][u'id'])
        clear_cache(params)


def get_default_context_menu(action, parent_params, current_params=None):
    uri_p = 'XBMC.Container.Update(%s)'
    default_list = [
        #        ('Settings', uri_p % u'Settings'),
        (u'Select Streamer', uri_p % plugin.get_url(action=u'selectStreamer', currentUrl=sys.argv[2])),
        (u'Clear cache', uri_p % plugin.get_url(action=u'clearCache', currentUrl=sys.argv[2]))
    ]
    list_ = default_list
    if action == u'list_day_epg':
        from urllib import urlencode
        # plugin.log(urlencode(current_params[u'name']))
        list_.append(
            (u'Download',
             uri_p % plugin.get_url(action=u'download_archive_stream',
                                    name=(current_params[u'name']).encode('UTF-8'),
                                    start_time=current_params[u'start_time'],
                                    channel_id=current_params[u'channel_id'])))

    return list_


plugin.actions[u'root'] = list_root_entries  # 'root' item is mandatory!
plugin.actions[u'list_group'] = list_group_entries
plugin.actions[u'list_channel'] = list_channel_entries
plugin.actions[u'list_day_epg'] = list_day_epg_entries
plugin.actions[u'live_stream'] = play_live_stream
plugin.actions[u'list_time_shifts'] = list_channel_time_shift_entries
plugin.actions[u'archive_stream'] = play_archive_stream
plugin.actions[u'download_archive_stream'] = download_archive_stream
plugin.actions[u'Settings'] = list_day_epg_entries
plugin.actions[u'clearCache'] = clear_cache
plugin.actions[u'selectStreamer'] = select_streamer

try:
    if __name__ == '__main__':
        # Run our plugin
        plugin.run()
    debug.stop()
except Exception as e:
    plugin.log(traceback.format_exc(), xbmc.LOGERROR)
    debug.stop()
    raise e
