# coding=utf-8
import xbmcaddon, xbmc, xbmcgui, xbmcplugin
import os, sys
import common
import xml.etree.ElementTree as ET

import xmltodict
import resources.lib.fscache as fscache

handle = int(sys.argv[1])
config = xbmcaddon.Addon(id='plugin.video.hdout.tv')
lang = config.getLocalizedString
thumb = os.path.join(os.getcwd().replace(';', ''), "icon.png")

request_all_series_it = fscache.FSCache(xbmc.translatePath('special://temp/plugin.video.hdout.tv/all_series'),
                                        minutes=50)
request_new_series_it = fscache.FSCache(xbmc.translatePath('special://temp/plugin.video.hdout.tv/new_series'),
                                        minutes=50)
request_my_series_it = fscache.FSCache(xbmc.translatePath('special://temp/plugin.video.hdout.tv/my_series'),
                                       minutes=1)
request_my_new_series_it = fscache.FSCache(xbmc.translatePath('special://temp/plugin.video.hdout.tv/my_new_series'),
                                           minutes=1)


@request_all_series_it(False)
def get_all_series_xml(tp):
    return common.get("List/all/XML/", tp)


@request_new_series_it(False)
def get_new_series_xml(tp):
    return common.get("List/new/XML/", tp)


@request_my_series_it(False)
def get_my_series_xml(tp):
    return common.get("List/my/XML/", tp)


@request_my_new_series_it(False)
def get_my_new_series_xml(tp):
    return common.get("List/mynew/XML/", tp)


def show_new_my_series_list(afv, rfv, tp):
    xbmc.log("Show my new series list", 3)
    s = get_my_new_series_xml(tp)
    if s is None:
        common.show_message(lang(30003), lang(30004))
        return False
    return show_new_series_list(afv, rfv, tp, s)


def show_new_all_series_list(afv, rfv, tp):
    xbmc.log("Show all new series list", 3)
    s = get_new_series_xml(tp)
    if s is None:
        common.show_message(lang(30003), lang(30004))
        return False
    return show_new_series_list(afv, rfv, tp, s)


def show_new_series_list_ucc(afv, rfv, tp, s):
    root = ET.fromstring(s)
    series_obj = root.findall('fp/series')
    series = {}
    channel_items = []
    for serie_obj in series_obj:
        serie_info_obj = serie_obj.find('seriesinfo/item')
        serie_id = serie_info_obj.find('id_series').text
        episodes_obj = serie_obj.findall('item')
        list_of_episodes = u""
        for episode_obj in episodes_obj:
            list_of_episodes += \
                u"[%02dx%02d]%s" % \
                (int(episode_obj.find('snum').text),
                 int(episode_obj.find('enum').text),
                 episode_obj.find('title').text) + u' '
        serie_channel = get_serial_channel(tp, serie_info_obj, None, list_of_episodes)
        url = sys.argv[0] + '?f=show_episodes&id=' + serie_id + '&tp=' + tp
        item = get_list_item_for_serie_channel(serie_channel, tp, afv, rfv)
        channel_items.append((url, item, True,))
    xbmcplugin.addDirectoryItems(handle, channel_items, len(channel_items))
    # xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(handle)
    return True


def show_new_series_list(afv, rfv, tp, s):
    if tp == 'uaj':
        return show_new_series_list_ucc(afv, rfv, tp, s)
    root = ET.fromstring(s)
    days = root.findall('fp/episodesbyday/day')
    series = {}
    array_of_series = []
    for day in days:
        series_obj = day.findall('seriesday')
        for serie_obj in series_obj:
            series_id = serie_obj.find('seriesitem/item/id_series').text
            if series_id not in series.keys():
                series[series_id] = {
                    'firstday': common.parser_date_time(serie_obj.find('item/tmark').text),
                    'serie': serie_obj
                }
                array_of_series.append(series_id)
            else:
                new_time = common.parser_date_time(serie_obj.find('item/tmark').text)
                if series[series_id]['firstday'] < new_time:
                    series[series_id] = {'firstDay': new_time, 'serie': serie_obj}

    array_of_series.sort(
        key=lambda serieid: series[series_id]['firstday'])
    channel_items = []
    for serie_id in array_of_series:
        episode_objs = series[serie_id]['serie'].findall('item')
        list_of_episodes = u""
        for episodeObj in episode_objs:
            list_of_episodes += \
                u"[%02dx%02d]" % \
                (int(episodeObj.find('snum').text),
                 int(episodeObj.find('enum').text)) + u' '
        list_of_episodes += u'\n'
        serie_obj = series[serie_id]['serie'].find('seriesitem/item')
        serie_channel = get_serial_channel(tp, serie_obj, series[serie_id]['firstday'], list_of_episodes)

        url = sys.argv[0] + '?f=show_episodes&id=' + serie_id + '&tp=' + tp
        item = get_list_item_for_serie_channel(serie_channel, tp, afv, rfv)
        channel_items.append((url, item, True,))

    xbmcplugin.addDirectoryItems(handle, channel_items, len(channel_items))
    # xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(handle)
    return True


def show_all_series_list(afv, rfv, tp):
    xbmc.log("Show all series list", 3)
    s = get_all_series_xml(tp)
    xbmc.log("Show all series list items", 3)
    list_items = show_series_list(afv, rfv, tp, s)
    return list_items


def show_my_series_list(afv, rfv, tp):
    s = get_my_series_xml(tp)
    return show_series_list(afv, rfv, tp, s)


def show_series_list(afv, rfv, tp, s):
    # global handle, plugin, root_url, lang
    # import xml.etree.cElementTree as cET
    if s is None:
        common.show_message(lang(30003), lang(30004))
        return False
    xbmc.log("Start elementtree", 4)
    root = ET.fromstring(s)
    xbmc.log("end elementtree", 4)
    xbmc.log("Start elementtree", 4)
    xbmc.log("end elementtree", 4)
    sl = root.findall('fp/serieslist/item')
    channel_items = []
    if sl:
        for serie_obj in sl:
            serie_channel = get_serial_channel(tp, serie_obj)
            url = sys.argv[0] + '?f=show_episodes&id=' + serie_channel['id'] + '&tp=' + tp
            item = get_list_item_for_serie_channel(serie_channel, tp, afv, rfv)
            channel_items.append((url, item, True,))
        xbmcplugin.addDirectoryItems(handle, channel_items, len(channel_items))
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(handle)
    else:
        common.show_message(lang(30003), lang(30005))
    xbmc.log("Prepare end", 4)
    return True


def get_serial_logo(tp, serie_obj):
    if tp == 'uaj':
        img = common.get_text(serie_obj.find('simg'))
        bimg = common.get_text(serie_obj.find('bimg'))
    else:
        mark = common.get_text(serie_obj.find('mark'))
        img = common.rootURL[tp] + "static/c/s/" + mark + ".jpg"
        bimg = common.rootURL[tp] + "static/c/b/" + mark + ".jpg"
    return img, bimg


def get_serial_channel(tp, xml_obj, last_update_time=None, list_of_episodes=None):
    serie_obj = xml_obj
    title = common.get_text(serie_obj.find('title'))
    etitle = common.get_text(serie_obj.find('etitle'))

    mark = common.get_text(serie_obj.find('mark'))
    tpi = common.get_text(serie_obj.find('type'))
    genre = common.get_text(serie_obj.find('genre'))
    country = common.get_text(serie_obj.find('country'))
    years = common.get_text(serie_obj.find('years'))
    imbdb = common.get_text(serie_obj.find('imdb'))
    hdout_rate = common.get_text(serie_obj.find('hdout_rate'))
    imbd_rate = common.get_text(serie_obj.find('imdb_rate'))
    kinopoisk_rate = common.get_text(serie_obj.find('kinopoisk_rate'))
    status = u"Закончен" if common.get_text(serie_obj.find('closed')) == "1" else u"В эфире"
    info = u""
    if tp == 'uaj':
        img = common.rootURL[tp] + "/" + common.get_text(serie_obj.find('simg'))
        bimg = common.rootURL[tp] + "/" + common.get_text(serie_obj.find('bimg'))
        if title is None:
            title = ""
        if etitle and len(etitle) > 1:
            title += " [" + etitle + "]"
    else:
        (img, bimg) = get_serial_logo(tp, serie_obj)
        if tpi == '1':
            title = u"[SD] " + title + " (" + etitle + ")"
        else:
            title = u"[HD] " + title + " (" + etitle + ")"
    if last_update_time is not None:
        info += u"Обновлено:" + last_update_time.strftime('%Y-%m-%d %H:%M') + u'\n'
    info += country + u", " + genre + u" " + years + u"\n"

    info = info \
           + (list_of_episodes if list_of_episodes is not None else u"") + u'\n'\
           + common.strip_html(common.get_text(serie_obj.find('info')))
    return {
        'id': common.get_text(serie_obj.find('id_series')),
        'title': title,
        'etitle': etitle,
        'big_image': bimg,
        'small_image': img,
        'genre': genre,
        'country': country,
        'years': years,
        'year': (years.split('_')[0].split('-')[0]),
        'info': info,
        'status': status,
        'hdout_rate': hdout_rate,
        'kinopoisk_rate': kinopoisk_rate,
        'imdb': imbdb,
        'imdb_rate': imbd_rate
    }


def get_list_item_for_serie_channel(serie_channel, tp, afv, rfv):
    item = xbmcgui.ListItem(serie_channel['title'], iconImage=serie_channel['small_image'],
                            thumbnailImage=serie_channel['small_image'])
    item.setInfo(type='video',
                 infoLabels={
                     'id': "hdout_tv_series_" + tp + "_" + serie_channel['id'],
                     'title': serie_channel['title'],
                     'genre': serie_channel['genre'],
                     'year': serie_channel['year'],
                     'orignaltitle': serie_channel['etitle'],
                     'code': serie_channel['imdb'],
                     'country': serie_channel['country'],
                     'votes': serie_channel['hdout_rate'],
                     'status': serie_channel['status'],

                     'plotoutline': serie_channel['info'],
                     'plot': serie_channel['info'] + "\n" + u"Кинопоиск: " + (
                         (serie_channel['kinopoisk_rate']) +
                         "\n" if serie_channel['kinopoisk_rate'] not in (None, 0) else u"нет\n") + u"IMDB: " + (
                                 serie_channel['imdb_rate'] if serie_channel['imdb_rate'] not in (
                                     None, 0) else u"нет"),
                 })
    item.setProperty('IsPlayable', 'false')
    item.setProperty('fanart_image', serie_channel['big_image'])

    item.setArt({'poster': serie_channel['big_image'],
                 'banner': serie_channel['big_image'],
                 'fanart': serie_channel['big_image'],
                 'thumb': serie_channel['small_image'],
                 'landscape': serie_channel['big_image']})

    if tp == 'uaj':
        if afv:
            item.addContextMenuItems(
                [(lang(30311), 'XBMC.RunPlugin(%s?f=addToFav&id=%s&tp=uaj)' % (sys.argv[0], id),)])
        if rfv:
            item.addContextMenuItems(
                [(lang(30312), 'XBMC.RunPlugin(%s?f=rmFromFav&id=%s&tp=uaj)' % (sys.argv[0], id),)])
    else:
        if afv:
            item.addContextMenuItems(
                [(lang(30301), 'XBMC.RunPlugin(%s?f=addToFav&id=%s&tp=hd)' % (sys.argv[0], id),)])
        if rfv:
            item.addContextMenuItems(
                [(lang(30302), 'XBMC.RunPlugin(%s?f=rmFromFav&id=%s&tp=hd)' % (sys.argv[0], id),)])

    return item
