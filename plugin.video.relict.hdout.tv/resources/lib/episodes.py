# coding=utf-8
import xbmcaddon, xbmc, xbmcgui, xbmcplugin
import os, sys
import common
import xml.etree.ElementTree as ET
import resources.lib.fscache as fscache
import series as hdout_series
import xml.dom.minidom
import json

request_all_episodes_it = fscache.FSCache(xbmc.translatePath('special://temp/plugin.video.relict.hdout.tv/episode'),
                                          seconds=5)


@request_all_episodes_it(False)
def get_all_episodes_xml(id, tp):
    return common.get("Series/" + id + "/XML/", tp)


def show_episodes(_pv):
    s = get_all_episodes_xml(_pv['id'], _pv['tp'])
    if s is None:
        common.show_message(common.lang(30003), common.lang(30004))
        return False
    root = ET.fromstring(s)
    serie = root.find('series')
    if serie is not None:
        series_info = hdout_series.get_serial_channel(_pv['tp'], serie)
        mark = common.get_text(serie.find('mark'))
        server = common.get_text(serie.find('server'))
        type = common.get_text(serie.find('type'))
        episodes = serie.findall('season/item')
        simg, bimg = hdout_series.get_serial_logo(_pv['tp'], serie)
        if episodes is not None:
            episode_items = []
            for episode in episodes:
                # last_update = parserDateTime(episode.find('item/tmark')[0].text)
                id = common.get_text(episode.find('id_episodes'))
                series = common.get_text(episode.find('series'))

                snum = int(common.get_text(episode.find('snum')))
                enum = int(common.get_text(episode.find('enum')))
                vnum = common.get_text(episode.find('vnum'))
                # title = gettext(episode, 'title')
                # etitle = gettext(episode, 'etitle')


                img = get_episode_logo(_pv, _pv['tp'], type, server, mark, series, snum, enum)
                if img is None:
                    img = simg
                ftitle = get_episode_title(episode, snum, enum)
                url = sys.argv[0] + '?f=show_episode&id=' + id + "&tp=" + _pv['tp']

                item = xbmcgui.ListItem(ftitle, iconImage=img, thumbnailImage=img)
                item.setInfo(type='video', infoLabels={
                    'id': "hdout_tv_episode_" + id,
                    'title': ftitle,
                    'plot': series_info['info'],
                    'season': snum,
                    'episode': enum})
                item.setProperty('fanart_image', bimg)
                item.setArt({'poster': img})
                item.setProperty('IsPlayable', 'true')
                watched_obj = root.find("aview/i[@id='%s']" % id)
                if watched_obj is not None:
                    item.setInfo('Video', {'playcount': 1})

                episode_items.append((url, item, True,))
            # episode_items = episode_items.reverse()
            xbmcplugin.addDirectoryItems(common.handle, episode_items, len(episode_items))
            xbmcplugin.addSortMethod(common.handle, xbmcplugin.SORT_METHOD_EPISODE)
            xbmcplugin.endOfDirectory(common.handle)


def show_episode(pv):
    s = common.get("EpisodeLink/" + pv['id'] + "/XML/", pv['tp'])
    if s is None:
        common.show_message(common.lang(30003), common.lang(30004))
        return False

    d = xml.dom.minidom.parseString(s)
    i = d.getElementsByTagName('item')
    if i and len(i) > 0:
        snum = int(common.getVal(i[0], 'snum'))
        enum = int(common.getVal(i[0], 'enum'))
        vnum = common.getVal(i[0], 'vnum')
        lenght = common.getVal(i[0], 'tl')
        title = common.getVal(i[0], 'title')
        etitle = common.getVal(i[0], 'etitle')

        smark = common.getVal(i[0], 'smark')
        server = common.getVal(i[0], 'server')
        series = common.getVal(i[0], 'series')

        if pv['tp'] == 'uaj':
            suburl = "http://" + server + "/content/" + series + "/"
            scurl = suburl + smark + ".jpg"
            videourl = common.getVal(i[0], 'vurl')
            sub_f = 0
        else:
            scurl = common.getVal(i[0], 'scurl')
            suburl = common.getVal(i[0], 'suburl')
            videourl = common.getVal(i[0], 'videourl')
            sub_f = int(common.getVal(i[0], 'sub_f'))

        sub_en = int(common.getVal(i[0], 'sub_en'))
        sub_ru = int(common.getVal(i[0], 'sub_ru'))
        tp = int(common.getVal(i[0], 'tp'))

        ftitle = common.fTitle(snum, vnum, title, etitle)

        item = xbmcgui.ListItem(ftitle, iconImage=scurl, thumbnailImage=scurl)
        item.setInfo(type='video', infoLabels={
            'id': "hdout_tv_episode_" + pv['tp'] + "_" + pv['id'],
            'title': ftitle,
            'season': snum,
            'episode': enum})
        player = xbmc.Player()
        player.play(videourl, item)
        xbmc.sleep(2000)
        if wait_for_plaing(player, videourl, 3):
            # xbmc.sleep(3000)

            if pv['tp'] == 'uaj':
                sub = int(common.config.getSetting('subuaj'))
                if sub == 1 and sub_ru == 1:
                    common.append_subtitle(smark, "1", suburl)
                elif sub == 2 and sub_en == 1:
                    common.append_subtitle(smark, "2", suburl)
            else:
                sub = int(common.config.getSetting('subhd'))
                if sub == 1 and sub_ru == 1:
                    common.append_subtitle(smark, "ru", suburl)
                elif sub == 2 and sub_en == 1:
                    common.append_subtitle(smark, "en", suburl)
                elif sub_f == 1:
                    common.append_subtitle(smark, "f", suburl)
            if wait_for_plaing(player, videourl, 3):
                mark_video_as_viewed(pv['id'], lenght, pv['tp'])
    else:
        e = d.getElementsByTagName('error')
        if e and len(e) > 0:
            et = common.getVal(e[0], "type")
            if type == "notfound":
                common.show_message(common.lang(30003), common.lang(30006))
                return False
            elif type == "nomoney":
                common.show_message(common.lang(30003), common.lang(30007))
                return False
            else:
                common.show_message(common.lang(30003), common.lang(30008))
                return False
        else:
            common.show_message(common.lang(30003), common.lang(30008))
            return False
    return True


def rpc(method, **params):
    params = json.dumps(params, encoding='utf-8')
    query = '{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params)
    return json.loads(xbmc.executeJSONRPC(query), encoding='utf-8')


def mark_video_as_viewed(episodeId, lenght, tp):
    #xbmc.log('Mark viewed:%s' % (episodeId), 4)
    common.get('?usecase=UpdateViewTime&t=%s&eid=%s' % (str(lenght), str(episodeId)), tp)


def wait_for_plaing(player, url, wait_time):
    wait_count = wait_time * 4
    count = 0
    while count < wait_count:
        if player.isPlayingVideo() and player.getPlayingFile() == url:
            xbmc.sleep(250)
            count += 1
        else:
            xbmc.log('PlayingStatus:%s,Url:%s' % (player.isPlayingVideo(), player.getPlayingFile()), 4)
            return False
    return True


def get_episode_title(episode_obj, snum, enum):
    prefix = u"[%02dx%02d]" % \
             (snum,
              enum)
    return prefix + " " + common.get_item_title(episode_obj)


def get_episode_logo(_pv, type, tp, server, mark, series, snum, enum):
    if _pv['tp'] == 'uaj':
        img = common.rootURL[(_pv['tp'])] + "/content/%s/%02d-%02d.jpg" % (series, snum, enum)
    else:
        # if tp == '1':
        #     img = rootURL[(pv['tp'])] + "v/%s/sd/%s/%02d-%02d.jpg" % (server, mark, snum, enum)
        # else:
        #     img = rootURL[(pv['tp'])] + "v/%s/hd/%s/sc/%02d-%02d.jpg" % (server, mark, snum, enum)
        img = None
    return img
