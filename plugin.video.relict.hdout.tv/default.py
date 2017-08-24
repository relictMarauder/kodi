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
config = xbmcaddon.Addon(id='plugin.video.relict.hdout.tv')
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


def get_item(lang_id, url):
    return ((sys.argv[0] + url, xbmcgui.ListItem(lang(lang_id), iconImage=thumb, thumbnailImage=thumb),
             True,))


def addToFav(pv):
    s = hdout_common.get('AddToFavorites/' + pv['id'] + '/', pv['tp'])
    if s is None:
        hdout_common.showMessage(lang(30003), lang(30004))
        return False
    xbmc.sleep(10)
    hdout_series.clear_cache()
    xbmc.executebuiltin('Container.Refresh')


def rmFromFav(pv):
    s = hdout_common.get('RemoveFromFavorites/' + pv['id'] + '/', pv['tp'])
    if s is None:
        hdout_common.showMessage(lang(30003), lang(30004))
        return False
    xbmc.sleep(10)
    hdout_series.clear_cache()
    xbmc.executebuiltin('Container.Refresh')


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
