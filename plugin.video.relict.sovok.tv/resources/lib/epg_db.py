import xbmc
import os
import datetime
import time
from sqlite3 import dbapi2 as sqlite


class epg_db:
    def __init__(self):
        db_dir = xbmc.translatePath('special://temp/relict.sovok.tv')
        self.db_file = os.path.join(db_dir, 'epg_db.sqlite')
        self.db = sqlite.connect(self.db_file, detect_types=sqlite.PARSE_DECLTYPES | sqlite.PARSE_COLNAMES)
        self.init_shema()

    def init_shema(self):
        cursor = self.db.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS program_favorites
            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER ,epg_id TEXT,
            FOREIGN KEY(epg_id)  REFERENCES epg(id),
            UNIQUE (program_favorites_id) ON CONFLICT IGNORE)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS last_programs
            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER ,epg_id TEXT,
            FOREIGN KEY(epg_id)  REFERENCES epg(id),
           UNIQUE (epg_id) ON CONFLICT IGNORE)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS groups

            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER ,color TEXT, group_id TEXT, name TEXT,
            UNIQUE (group_id) ON CONFLICT IGNORE)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS channels
            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER, have_archive TEXT,epg_start TEXT ,icon TEXT,
            channel_id TEXT, is_video TEXT,name TEXT, protected TEXT, sprite_pos TEXT,
            UNIQUE (channel_id) ON CONFLICT IGNORE)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS channel_to_group
            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER, channel_id INTEGER, group_id INTEGER,
            UNIQUE (channel_id,group_id) ON CONFLICT IGNORE,
            FOREIGN KEY(channel_id)  REFERENCES channels(id), FOREIGN KEY(group_id)  REFERENCES groups(id))''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS epg
            (id INTEGER PRIMARY KEY NOT NULL, created INTEGER ,channel_id INTEGER,
            description TEXT, progname TEXT, t_start TEXT, ut_start INTEGER,
            UNIQUE (channel_id,ut_start) ON CONFLICT IGNORE,
            FOREIGN KEY(channel_id)  REFERENCES channels(id))''')
        cursor.execute(
            '''CREATE INDEX IF NOT EXISTS idx_epg ON epg (ut_start)''')
        cursor.execute(
            '''CREATE INDEX IF NOT EXISTS idx_epg ON epg (channel_id,ut_start)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS epg_full_status
            (id INTEGER PRIMARY KEY NOT NULL, epg_day INTEGER, created INTEGER)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS epg_status
            (id INTEGER PRIMARY KEY NOT NULL, channel_id INTEGER, epg_day INTEGER, created INTEGER )''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS login_info
            (id INTEGER PRIMARY KEY NOT NULL, login TEXT, login_time INTEGER, pwd TEXT, sid TEXT, sid_name TEXT )''')
        self.db.commit()

    def set_login_info(self, login_info):
        self.db.execute("DELETE FROM login_info")
        self.db.execute("INSERT INTO login_info(login,login_time,pwd,sid,sid_name) VALUES(?,?,?,?,?)",
                        [login_info[u'login'],
                         int(time.mktime(login_info[u'login_time'].timetuple())),
                         login_info[u'pwd'],
                         login_info[u'sid'],
                         login_info[u'sid_name']])
        self.db.commit()

    def get_login_info(self):
        login_row = self.db.execute("SELECT login,login_time,pwd,sid,sid_name FROM login_info").fetchone()
        if login_row is not None:
            return {
                u'login': login_row[0],
                u'login_time': datetime.datetime.fromtimestamp(int(login_row[1])),
                u'pwd': login_row[2],
                u'sid': login_row[3],
                u'sid_name': login_row[4],
            }
        return None

    def mark_full_day(self, day):
        import_day = int(time.mktime(day.timetuple()))
        import_time = int(time.mktime(datetime.datetime.now().timetuple()))
        self.db.execute('INSERT  INTO '
                        'epg_full_status(epg_day, created) '
                        'VALUES(?,?)',
                        [import_day, import_time])
        self.db.commit()

    def mark_channel_day(self, channel_id, day):
        import_day = int(time.mktime(day.timetuple()))
        import_time = int(time.mktime(datetime.datetime.now().timetuple()))
        self.db.execute('INSERT  INTO '
                        'epg_status(channel_id,epg_day, created) '
                        'SELECT id,?,? FROM channels WHERE channel_id=?',
                        [import_day, import_time, channel_id])
        self.db.commit()

    def is_channel_epg_loaded(self, channel_id, day):
        result = False
        import_day = int(time.mktime(day.timetuple()))
        full_epg_status_row = self.db.execute('SELECT created FROM epg_full_status WHERE epg_day=?',
                                              [import_day]).fetchone()
        if full_epg_status_row is None:
            channel_epg_status_row = self.db.execute(
                'SELECT epg_status.created FROM epg_status '
                'INNER JOIN channels ON channels.id = epg_status.channel_id '
                'WHERE epg_status.epg_day=? AND channels.channel_id=?',
                [import_day, channel_id]).fetchone()
            result = channel_epg_status_row is not None
        else:
            result = True
        return result

    def is_full_day_loaded(self):
        import_day = int(time.mktime(datetime.date.today().timetuple()))
        full_epg_status_row = self.db.execute('SELECT created FROM epg_full_status WHERE epg_day=?',
                                              [import_day]).fetchone()
        return full_epg_status_row is not None

    def import_epg(self, day_epg):

        import_time = int(time.mktime(datetime.datetime.now().timetuple()))
        cleanup_time = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=14)).timetuple()))
        result = self.db.execute("DELETE FROM epg WHERE ut_start < ?", [cleanup_time])
        if result.rowcount > 0:
            self.db.execute("VACUUM")
        for epg_channel in day_epg:
            existed_channel = self.db.execute("SELECT id FROM channels WHERE channel_id=?",
                                              [str(epg_channel[u'id'])]).fetchone()
            if existed_channel is not None:
                ch_id = existed_channel[0]

                epg_inserts = []
                for epg_item in epg_channel[u'epg']:
                    epg_inserts.append((import_time, ch_id, epg_item[u'description'], epg_item[u'progname'],
                                        epg_item[u't_start'], epg_item[u'ut_start']))
                self.db.executemany("INSERT OR REPLACE "
                                    "INTO epg (created,channel_id,description, progname, t_start,ut_start) "
                                    "VALUES(?,?,?,?,?,?)",
                                    epg_inserts)

        self.db.commit()

    def import_channel_list(self, channel_list):
        import_time = int(time.mktime(datetime.datetime.now().timetuple()))
        group_inserts = []
        group_updates = []
        for group in channel_list[u'groups']:
            group_obj = (import_time,
                         group[u'color'],
                         group[u'id'],
                         group[u'name'])
            id_existed_group_row = self.db.execute("SELECT id FROM groups WHERE group_id=?", [group[u'id']]).fetchone()
            if id_existed_group_row is None:
                group_inserts.append(group_obj)
            else:
                updateObj = group_obj + (id_existed_group_row[0],)
                group_updates.append(updateObj)
        if len(group_inserts) > 0:
            result_group_inserts = self.db.executemany("INSERT INTO groups "
                                                       "(created,color, group_id, name) "
                                                       "VALUES(?,?,?,?)",
                                                       group_inserts)
        if len(group_updates) > 0:
            result_group_updates = self.db.executemany("UPDATE groups "
                                                       "SET created=?,color=?,group_id=?,name=?"
                                                       "WHERE id=?",
                                                       group_updates)
        channel_inserts = []
        channels_updates = []
        for group in channel_list[u'groups']:

            for channel in group[u'channels']:
                channel_obj = (
                    import_time,
                    str(channel[u'have_archive']),
                    channel[u'icon'],
                    str(channel[u'id']),
                    channel[u'is_video'],
                    channel[u'name'],
                    str(channel[u'protected']),
                    str(channel[u'epg_start']),
                    channel[u'sprite_pos']
                )
                id_existed_channel_row = self.db.execute("SELECT id FROM channels WHERE channel_id=?",
                                                         [channel[u'id']]).fetchone()
                if id_existed_channel_row is None:
                    channel_inserts.append(channel_obj)
                else:
                    channels_updates.append(channel_obj + (id_existed_channel_row[0],))
        if len(channel_inserts) > 0:
            self.db.executemany(
                "INSERT INTO channels "
                "(created,have_archive, icon, channel_id, is_video, name, protected,epg_start, sprite_pos) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                channel_inserts)
        if len(group_updates) > 0:
            result_channels_updates = self.db.executemany("UPDATE channels "
                                                          "SET created=?,have_archive=?, icon=?, channel_id=?, "
                                                          "is_video=?, name=?, protected=?,epg_start=?, sprite_pos=? "
                                                          "WHERE id=?",
                                                          channels_updates)
        result_delete_groups = self.db.execute("DELETE FROM groups WHERE created!=?", [import_time])
        result_delete_channels = self.db.execute("DELETE FROM channels WHERE created!=?", [import_time])
        self.db.execute("DELETE FROM channel_to_group")
        self.db.execute("VACUUM")
        self.db.commit()
        mapping_inserts = []
        for group in channel_list[u'groups']:
            group_id = self.db.execute("SELECT id FROM groups WHERE group_id=?", [(group[u'id'])]).fetchone()[0]
            for channel in group[u'channels']:
                channel_id = \
                    self.db.execute("SELECT id FROM channels WHERE channel_id=?", [(channel[u'id'])]).fetchone()[0]
                mapping_inserts.append((import_time, channel_id, group_id))

        result_channel_mapping = self.db.executemany(
            "INSERT INTO channel_to_group (created,channel_id, group_id)"
            "VALUES(?,?,?)",
            mapping_inserts)
        self.db.commit()

    def add_program_favorites(self, epg_id):
        add_time = int(time.mktime(datetime.datetime.now().timetuple()))
        self.db.execute('INSERT  INTO '
                        'program_favorites(epg_id, created) '
                        'VALUES (?,?)',
                        [epg_id, add_time])
        self.db.commit()

    def remove_from_program_favorites(self, epg_id):
        self.db.execute('DELETE FROM '
                        'program_favorites '
                        'WHERE epg_id=?',
                        [epg_id])
        self.db.commit()

    def add_last_program(self, epg_id):
        add_time = int(time.mktime(datetime.datetime.now().timetuple()))
        self.db.execute('INSERT  INTO '
                        'last_programs(epg_id, created) '
                        'VALUES (?,?)',
                        [epg_id, add_time])
        self.db.commit()

    def clean_last_program(self):

        self.db.execute('DELETE FROM '
                        'last_programs '
                        'WHERE id not in  (select lp.id from last_programs as lp order by lp.created DESC LIMIT 20)')
        self.db.commit()

    def get_day_epg(self, channel_id, day):
        start_time = int(time.mktime(day.timetuple()))
        end_time = int(time.mktime((day + datetime.timedelta(days=1)).timetuple()))
        epgs = []
        for epg_row in self.db.execute("SELECT epg.description,epg.progname, epg.t_start, epg.ut_start, epg.id ,"
                                       "program_favorites.id FROM epg "
                                       "INNER JOIN channels ON channels.id=epg.channel_id "
                                       "LEFT OUTER JOIN  program_favorites ON program_favorites.epg_id=epg.id "
                                       "WHERE channels.channel_id=? AND ut_start BETWEEN ? AND ?  "
                                       "ORDER BY ut_start",
                                       (str(channel_id), start_time, end_time)):
            epgs.append({
                u'descriptions': epg_row[0],
                u'progname': epg_row[1],
                u't_start': epg_row[2],
                u'ut_start': epg_row[3],
                u'is_favorites': epg_row[5],
                u'id': epg_row[4],
                u'channel_id': channel_id
            })

        if len(epgs) > 0:
            return epgs
        return None

    def get_last_programs(self):
        epgs = []
        self.clean_last_program()
        for epg_row in self.db.execute("SELECT epg.description,epg.progname, epg.t_start, epg.ut_start, epg.id ,"
                                       "last_programs.id, "
                                       "channels.channel_id FROM epg "
                                       "INNER JOIN last_programs ON last_programs.epg_id=epg.id "
                                       "INNER JOIN channels ON channels.id=epg.channel_id "
                                       "ORDER BY last_programs.created DESC "):
            epgs.append({
                u'descriptions': epg_row[0],
                u'progname': epg_row[1],
                u't_start': epg_row[2],
                u'ut_start': epg_row[3],
                u'id': epg_row[4],
                u'is_favorites': None,
                u'channel_id': epg_row[6]
            })

        if len(epgs) > 0:
            return epgs
        return None

    def get_program_favorites(self):
        epgs = []

        for epg_row in self.db.execute("SELECT epg.description,epg.progname, epg.t_start, epg.ut_start, epg.id ,"
                                       "program_favorites.id, "
                                       "channels.channel_id FROM epg "
                                       "INNER JOIN program_favorites ON program_favorites.epg_id=epg.id "
                                       "INNER JOIN channels ON channels.id=epg.channel_id "
                                       "ORDER BY ut_start"):
            epgs.append({
                u'descriptions': epg_row[0],
                u'progname': epg_row[1],
                u't_start': epg_row[2],
                u'ut_start': epg_row[3],
                u'id': epg_row[4],
                u'is_favorites': epg_row[5],
                u'channel_id': epg_row[6]
            })

        if len(epgs) > 0:
            return epgs
        return None

    def get_current_prog(self, channel_id):
        current_time = int(time.mktime(datetime.datetime.now().timetuple()))
        epg_row = self.db.execute("SELECT epg.description,epg.progname, epg.t_start, epg.ut_start , epg.id, "
                                  "program_favorites.id "
                                  "FROM epg "
                                  "LEFT OUTER JOIN  program_favorites ON program_favorites.epg_id=epg.id "
                                  "INNER JOIN channels ON channels.id=epg.channel_id "
                                  "WHERE channels.channel_id=? AND ut_start < ? ORDER BY ut_start DESC LIMIT 1",
                                  (str(channel_id), current_time)).fetchone()
        epg_item = None
        if epg_row is not None:
            epg_item = {
                u'descriptions': epg_row[0],
                u'progname': epg_row[1],
                u't_start': epg_row[2],
                u'ut_start': epg_row[3],
                u'id': epg_row[4],
                u'is_favorites': epg_row[5],
                u'channel_id': channel_id
            }
        return epg_item

    def get_groups(self):
        tm = datetime.datetime.now() - datetime.timedelta(days=1)
        last_time = int(time.mktime(tm.timetuple()))
        groups = []
        for group_row in self.db.execute("SELECT group_id, color, name FROM groups WHERE created > ?", [last_time]):
            groups.append({u'channels': [], u'color': group_row[1], u'id': group_row[0], u'name': group_row[2]})
        if len(groups) > 0:
            return groups
        return None

    def _get_raw_group(self, group_id):
        group_row = self.db.execute(
            "SELECT group_id, color, name FROM groups WHERE group_id=?"
            , [group_id]
        ).fetchone()
        return self._get_group_from_row(group_row)

    @staticmethod
    def _get_group_from_row(group_row):
        if group_row is not None:
            return {
                u'channels': [],
                u'color': group_row[1],
                u'id': group_row[0],
                u'name': group_row[2]
            }
        return None

    @staticmethod
    def _get_channel_from_row(ch_row):
        return {u'id': ch_row[0],
                u'name': ch_row[1],
                u'icon': ch_row[2],
                u'is_video': ch_row[3],
                u'have_archive': ch_row[4],
                u'protected': ch_row[5],
                u'epg_start': ch_row[6]}

    def get_channel(self, channel_id):
        ch_row = self.db.execute("SELECT channels.channel_id,"
                                 "channels.name,"
                                 "channels.icon,"
                                 "channels.is_video,"
                                 "channels.have_archive,"
                                 "channels.protected, "
                                 "channels.epg_start "
                                 "FROM channels  WHERE channel_id=?", [channel_id]).fetchone()
        if ch_row is not None:
            ch = self._get_channel_from_row(ch_row)
            group_row = self.db.execute(
                "SELECT groups.group_id, groups.color, groups.name "
                "FROM groups "
                "INNER JOIN channel_to_group ON channel_to_group.group_id=groups.id "
                "INNER JOIN channels ON channel_to_group.channel_id=channels.id "
                "WHERE channels.channel_id=?"
                , [channel_id]
            ).fetchone()
            group = self._get_group_from_row(group_row)
            return group, ch
        return None, None

    def get_group(self, group_id):
        chs = []
        if group_id is None or group_id == 'None':
            select_result = self.db.execute("SELECT channels.channel_id,"
                                            "channels.name,"
                                            "channels.icon,"
                                            "channels.is_video,"
                                            "channels.have_archive,"
                                            "channels.protected, "
                                            "channels.epg_start "
                                            "FROM channels ORDER BY  name")
            group = {
                u'channels': [],
                u'color': None,
                u'id': None,
                u'name': 'All'
            }
        else:
            group = self._get_raw_group(group_id)
            if group is not None:
                select_result = self.db.execute(
                    "SELECT channels.channel_id,"
                    "channels.name,"
                    "channels.icon,"
                    "channels.is_video,"
                    "channels.have_archive,"
                    "channels.protected, "
                    "channels.epg_start "
                    "FROM channels "
                    "INNER JOIN channel_to_group "
                    "ON channels.id=channel_to_group.channel_id "
                    "INNER JOIN groups "
                    "ON groups.id=channel_to_group.group_id "
                    "WHERE groups.group_id=?"
                    "ORDER BY channels.name",
                    [group_id])
            else:
                return None

        for ch_row in select_result:
            chs.append(self._get_channel_from_row(ch_row))
        if len(chs) > 0:
            group[u'channels'] = chs
            return group

        return None

    def clear_login_info(self):
        self.db.execute('''DELETE FROM login_info''')

    def clear(self):
        self.db.execute('''DELETE FROM last_programs''')
        self.db.execute('''DELETE FROM program_favorites''')
        self.db.execute('''DELETE FROM channel_to_group''')
        self.db.execute('''DELETE FROM epg''')
        self.db.execute('''DELETE FROM epg_status''')
        self.db.execute('''DELETE FROM epg_full_status''')
        self.db.execute('''DELETE FROM channels''')
        self.db.execute('''DELETE FROM groups''')
        self.db.execute("VACUUM")
        self.db.commit()

    def __enter__(self):
        """Create context manager"""
        return self

    def __exit__(self, *args):
        """Clean up context manager"""
        self.db.commit()
        self.db.close()
        return False
