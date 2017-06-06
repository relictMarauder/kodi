#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcaddon, xbmc, xbmcgui, xbmcplugin
import sys
import os

import traceback
from resources.lib.debug import RemoteDebug
import resources.lib.series as hdout_series
import resources.lib.episodes as hdout_episodes
import resources.lib.common as hdout_common

debug = RemoteDebug(False)
debug.start()

# Plugin config
config = xbmcaddon.Addon(id='plugin.video.hdout.tv')
lang = config.getLocalizedString
login = config.getSetting('login')
password = config.getSetting('password')

handle = int(sys.argv[1])
##thumb = os.path.join(os.getcwd().replace(';', ''), "icon.png")
thumb = os.path.join(config.getAddonInfo('path'), "icon.png")

plugin = 'HDOut.TV'
rootURL = {'hd': 'http://hdout.tv/', 'uaj': 'http://uaj.cc/'}


def show_series(_pv):
    return hdout_series.show_all_series_list(True, False, _pv['tp'])


def show_new_series(_pv):
    return hdout_series.show_new_all_series_list(True, False, _pv['tp'])


def show_new_my_series(_pv):
    return hdout_series.show_new_my_series_list(True, False, _pv['tp'])



def show_my_series(_pv):
    return hdout_series.show_my_series_list(False, True, _pv['tp'])


def show_episodes(_pv):
    return hdout_episodes.show_episodes(_pv)


def show_episode(_pv):
    return hdout_episodes.show_episode(_pv)


# def showRSS(pv):
#     s = get("RSS/", pv['tp'])
#     return rss(s, pv['tp'])
#
#
# def showMyRSS(pv):
#     uid = config.getSetting('uid')
#     if uid and len(uid) > 0:
#         s = get("UserRSS/" + uid + "/", pv['tp'])
#         return rss(s, pv['tp'])
#     else:
#         auth(pv['tp'])
#         return showMyRSS(pv)
#
#
# def openSettings(pv):
#     global config
#     config.openSettings()
#     config.setSetting('sidhd', '')
#     config.setSetting('siduaj', '')
#     config.setSetting('uid', '')
#     xbmc.sleep(30)
#
#
# def addToFav(pv):
#     s = get('AddToFavorites/' + pv['id'] + '/', pv['tp'])
#     if s == None:
#         show_message(lang(30003), lang(30004))
#         return False
#
#
# def rmFromFav(pv):
#     s = get('RemoveFromFavorites/' + pv['id'] + '/', pv['tp'])
#     if s == None:
#         show_message(lang(30003), lang(30004))
#         return False
#     xbmc.sleep(10)
#     xbmc.executebuiltin('Container.Refresh')


def get_item(lang_id, url):
    return ((sys.argv[0] + url, xbmcgui.ListItem(lang(lang_id), iconImage=thumb, thumbnailImage=thumb),
             True,))


def default(pv):
    global handle
    list_items = [get_item(30010, '?f=show_series&tp=hd'),
                  get_item(30011, '?f=show_my_series&tp=hd'),
                  get_item(30012, '?f=show_new_series&tp=hd'),
                  get_item(30013, '?f=show_new_my_series&tp=hd'),
                  get_item(30020, '?f=show_series&tp=uaj'),
                  get_item(30021, '?f=show_my_series&tp=uaj'),
                  get_item(30022, '?f=show_new_series&tp=uaj'),
                  get_item(30023, '?f=show_new_my_series&tp=uaj'),
                  get_item(30050, '?f=openSettings')
                  ]

    # hdout_common.add_menu(30010, sys.argv[0] + '?f=show_series&tp=hd')
    # hdout_common.add_menu(30011, sys.argv[0] + '?f=show_my_series&tp=hd')
    # #	addMenu(30012, sys.argv[0] + '?f=showRSS&tp=hd')
    # hdout_common.add_menu(30012, sys.argv[0] + '?f=show_new_series&tp=hd')
    # hdout_common.add_menu(30013, sys.argv[0] + '?f=showMyRSS&tp=hd')
    #
    # hdout_common.add_menu(30020, sys.argv[0] + '?f=show_series&tp=uaj')
    # hdout_common.add_menu(30021, sys.argv[0] + '?f=showMySeries&tp=uaj')
    # hdout_common.add_menu(30022, sys.argv[0] + '?f=showRSS&tp=uaj')
    # hdout_common.add_menu(30023, sys.argv[0] + '?f=showMyRSS&tp=uaj')
    #
    # hdout_common.add_menu(30050, sys.argv[0] + '?f=openSettings')
    xbmcplugin.addDirectoryItems(handle, list_items, len(list_items))
    xbmcplugin.endOfDirectory(handle)


def init():
    global config, login, password, lang

    while not hdout_common.auth('hd'):
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading(lang(30001))
        user_keyboard.doModal()
        if user_keyboard.isConfirmed():
            login = user_keyboard.getText()
            pass_keyboard = xbmc.Keyboard()
            pass_keyboard.setHeading(lang(30002))
            pass_keyboard.setHiddenInput(True)
            pass_keyboard.doModal()
            if pass_keyboard.isConfirmed():
                password = pass_keyboard.getText()
                config.setSetting('login', login)
                config.setSetting('password', password)
            else:
                return False
        else:
            return False
    return True


# def rss(s, tp):
#     global handle, plugin, lang
#
#     if s is None:
#         show_message(lang(30003), lang(30004))
#         return False
#     d = xml.dom.minidom.parseString(s)
#     sl = d.getElementsByTagName('item')
#     if sl:
#         for i in sl:
#             title = getVal(i, 'title')
#             link = getVal(i, 'link')
#             image = getVal(i, 'image')
#             tumbnail = getVal(i, 'tumbnail')
#
#             ub = re.search("/Episode/([0-9]*)/", link)
#             if ub:
#                 url = sys.argv[0] + '?f=showEpisode&id=' + ub.group(1) + "&tp=" + tp
#                 item = xbmcgui.ListItem(title, iconImage=tumbnail, thumbnailImage=tumbnail)
#                 item.setInfo(type='video', infoLabels={
#                     'id': "hdout_tv_episode_" + tp + "_" + ub.group(1),
#                     'title': title})
#                 item.setProperty('fanart_image', image)
#                 xbmcplugin.addDirectoryItem(handle, url, item, True)
#         xbmcplugin.endOfDirectory(handle)
#     else:
#         show_message(lang(30003), lang(30005))
#     return True
#
#
#
#
#
#
# def showSeriesList(u, afv, rfv, tp):
#     global handle, plugin, rootURL, lang
#
#     s = get(u, tp)
#     if s is None:
#         show_message(lang(30003), lang(30004))
#         return False
#     d = xml.dom.minidom.parseString(s)
#     sl = d.getElementsByTagName('serieslist')
#     if sl:
#         sli = sl[0].getElementsByTagName('item')
#         if sli:
#             for i in sli:
#                 id = getVal(i, 'id_series')
#                 title = getVal(i, 'title')
#                 etitle = getVal(i, 'etitle')
#                 info = strip_html(getVal(i, 'info'))
#                 mark = getVal(i, 'mark');
#                 tpi = getVal(i, 'type');
#
#                 if tp == 'uaj':
#                     img = rootURL[tp] + "/" + getVal(i, 'simg');
#                     bimg = rootURL[tp] + "/" + getVal(i, 'bimg');
#                     if title == None: title = ""
#                     if etitle and len(etitle) > 1: title += " [" + etitle + "]"
#                 else:
#                     img = rootURL[tp] + "static/c/s/" + mark + ".jpg"
#                     bimg = rootURL[tp] + "static/c/b/" + mark + ".jpg"
#                     if tpi == '1':
#                         title = "[SD] " + title + " (" + etitle + ")"
#                     else:
#                         title = "[HD] " + title + " (" + etitle + ")"
#                 url = sys.argv[0] + '?f=showEpisodes&id=' + id + '&tp=' + tp
#
#                 item = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
#                 item.setInfo(type='video', infoLabels={
#                     'id': "hdout_tv_series_" + tp + "_" + id,
#                     'title': title,
#                     'plot': info})
#                 item.setProperty('fanart_image', bimg)
#
#                 if tp == 'uaj':
#                     if afv: item.addContextMenuItems(
#                         [(lang(30311), 'XBMC.RunPlugin(%s?f=addToFav&id=%s&tp=uaj)' % (sys.argv[0], id),)])
#                     if rfv: item.addContextMenuItems(
#                         [(lang(30312), 'XBMC.RunPlugin(%s?f=rmFromFav&id=%s&tp=uaj)' % (sys.argv[0], id),)])
#                 else:
#                     if afv: item.addContextMenuItems(
#                         [(lang(30301), 'XBMC.RunPlugin(%s?f=addToFav&id=%s&tp=hd)' % (sys.argv[0], id),)])
#                     if rfv: item.addContextMenuItems(
#                         [(lang(30302), 'XBMC.RunPlugin(%s?f=rmFromFav&id=%s&tp=hd)' % (sys.argv[0], id),)])
#
#                 xbmcplugin.addDirectoryItem(handle, url, item, True)
#
#             xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
#             xbmcplugin.endOfDirectory(handle)
#         else:
#             show_message(lang(30003), lang(30005))
#     else:
#         show_message(lang(30003), lang(30005))
#     return True


# utility functions



# def fTitle(snum, vnum, title, etitle):
#     if title and len(title) > 1:
#         ftitle = "%2dx%s. " % (snum, vnum) + title
#         if etitle and len(etitle) > 1: ftitle += " (" + etitle + ")"
#     else:
#         ftitle = "%2dx%s. " % (snum, vnum) + etitle
#     return ftitle






def ping():
    hdout_common.get("PingUser/", "hd")

    # XBMC misc


def get_params(dv):
    param = dv
    param_string = sys.argv[2]
    if len(param_string) >= 2:
        params = sys.argv[2]
        cleaned_params = params.replace('?', '')
        if params[len(params) - 1] == '/':
            params = params[0:len(params) - 2]
        pairs_of_params = cleaned_params.split('&')
        for i in range(len(pairs_of_params)):
            split_params = {}
            split_params = pairs_of_params[i].split('=')
            if (len(split_params)) == 2: param[split_params[0]] = split_params[1]
    return param


try:
    if init():
        pv = {'f': None, 'id': 0, 'tp': 'hd'}
        funs = ['show_series', 'show_new_series', 'show_my_series', 'show_episodes', 'show_episode', 'showRSS',
                'show_new_my_series',
                'openSettings',
                'addToFav', 'rmFromFav']

        pvm = get_params(pv)
        ping()
        if pvm['f'] in funs:
            eval(pvm['f'] + "(pv)")
        else:
            default(pv)
    debug.stop()
except Exception as e:
    xbmc.log('-----------------', 4)
    xbmc.log(traceback.format_exc(sys.exc_info()), 4)
    debug.stop()
    raise e

    # Main processing
