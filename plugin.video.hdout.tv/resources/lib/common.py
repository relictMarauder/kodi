import xbmcaddon, xbmc, xbmcgui, xbmcplugin
import urllib2
import urllib
import os
import sys
import re
from datetime import datetime
import time
import xml.dom.minidom
import htmlentitydefs
import zlib

handle = int(sys.argv[1])
config = xbmcaddon.Addon(id='plugin.video.hdout.tv')
lang = config.getLocalizedString
thumb = os.path.join(os.getcwd().replace(';', ''), "icon.png")
plugin = 'HDOut.TV'
rootURL = {'hd': 'http://hdout.tv/', 'uaj': 'http://uaj.cc/'}


def get_item_title(item_obj):
    title = get_text(item_obj.find('title'))
    etitle = get_text(item_obj.find('etitle'))
    ftitle = ""
    if title and len(title) > 1:
        ftitle = title
        if etitle and len(etitle) > 1:
            ftitle += " (" + etitle + ")"
    else:
        ftitle = etitle
    return ftitle


def parser_date_time(date_string):
    try:
        return datetime(*(time.strptime(date_string, '%Y-%m-%d %H:%M:%S')[0:6]))
    except (TypeError, ValueError):
        return datetime.strptime(date_string, '%Y-%m-%d %H:%S')


def get_text(element):
    if element is None:
        return ""
    else:
        return element.text


def show_message(head, message, times=10000):
    xbmc.executebuiltin(
        'XBMC.Notification("%s", "%s", %s, "%s")' % (
            head.encode('utf-8'), message.encode('utf-8'), times, thumb))


def add_menu(ids, uri, thumb):
    global handle
    item = xbmcgui.ListItem(lang(ids), iconImage=thumb, thumbnailImage=thumb)
    xbmcplugin.addDirectoryItem(handle, uri, item, True)


def append_subtitle(smark, ln, suburl):
    url = suburl + smark + "_" + ln
    surl = None
    try:
        surl = url + ".srt"
        sf = urllib2.urlopen(surl, None)
    except:
        surl = None
        pass

    if surl is None:
        try:
            surl = url + ".ass"
            sf = urllib2.urlopen(surl, None)
        except:
            surl = None
            pass

    if surl is not None:
        xbmc.Player().setSubtitles(surl)


def get(url, tp):
    global config, rootURL
    xbmc.log('Start get %s' % url, 2)
    sid = config.getSetting('sid' + tp)
    if len(sid) < 2:
        if auth(tp):
            sid = config.getSetting('sid' + tp)
        else:
            return None

    request = urllib2.Request(rootURL[tp] + url, None)
    if tp == 'uaj':
        request.add_header('Cookie', 'PHPSESSID=' + sid)
    else:
        request.add_header('Cookie', 'SID=' + sid)
    request.add_header('Accept-encoding', 'gzip,deflate')

    o = urllib2.urlopen(request)
    isGZipped = o.headers.get('content-encoding', '').find('gzip') >= 0
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)  # this magic number can be inferred from the structure of a gzip file
    data = o.read()
    if isGZipped:
        page = d.decompress(data)
    else:
        page = data
    xbmc.log('%s is retrieved' % url, 2)
    if page.find('<form id="loginform"') == -1:
        return page
    else:
        if auth(tp):
            return get(url, tp)
        else:
            return None



def auth(tp):
    global config, rootURL

    if tp == 'uaj': return uajauth()

    r = False
    params = urllib.urlencode(
        dict(login=config.getSetting('login'), password=config.getSetting('password'), iapp=1))
    f = urllib2.urlopen(rootURL['hd'], params)
    d = f.read()
    f.close()
    if d.find('<form id="loginform"') == -1:
        try:
            ad = xml.dom.minidom.parseString(d)
            sid = getVal(ad, 'SID')
            if sid and len(sid) > 2:
                config.setSetting('sid' + tp, sid)
                r = True
            uid = getVal(ad, 'UID')
            if uid and len(uid) > 0:
                config.setSetting('uid', uid)
        except:
            r = False
            pass
    return r


def uajauth():
    global config

    sid = config.getSetting('sidhd')
    if sid and len(sid) > 2:
        r = urllib2.Request("http://hdout.tv/ToUAJT/", None)
        r.add_header('Cookie', 'SID=' + sid)
        f = urllib2.urlopen(r)
        d = f.read()
        f.close()
        if d.find('<form id="loginform"') == -1:
            ad = xml.dom.minidom.parseString(d)
            nsid = getVal(ad, 'SID')
            if nsid and len(nsid) > 2:
                config.setSetting('siduaj', nsid)
                return True
    if auth('hd'):
        return uajauth()
    else:
        return False


def strip_html(text):
    if text is None:
        return ""

    def fixup(m):
        text = m.group(0)
        try:
            if text[:1] == "<":
                if text[1:3] == 'br':
                    return u'\n'
                else:
                    return u""
            if text[:2] == "&#":
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            elif text[:1] == "&":
                if text[1:-1] == "dash" or text[1:-1] == "mdash;":
                    entity = u" - "
                elif text[1:-1] == "ndash":
                    entity = u"-"
                elif text[1:-1] == "hellip":
                    entity = u"-"
                else:
                    entity = unichr(htmlentitydefs.name2codepoint.get(text[1:-1]))
                if entity:
                    if entity[:2] == "&#":
                        try:
                            return unichr(int(entity[2:-1]))
                        except ValueError:
                            pass
                    else:
                        return entity
        except Exception as e:
            pass
        return text

    try:
        ret = re.sub(u"(?s)<[^>]*>|&#?\w+;", fixup, text) if text else u""
    except Exception as e:
        pass
    return re.sub(u"\n+", u'\n', ret)


def getVal(d, tag):
    r = None
    try:
        r = d.getElementsByTagName(tag)[0].childNodes[0].nodeValue.strip().encode('utf-8')
    except:
        pass
    return r


def fTitle(snum, vnum, title, etitle):
    if title and len(title) > 1:
        ftitle = "%2dx%s. " % (snum, vnum) + title
        if etitle and len(etitle) > 1: ftitle += " (" + etitle + ")"
    else:
        ftitle = "%2dx%s. " % (snum, vnum) + etitle
    return ftitle
