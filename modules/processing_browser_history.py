# -*- encoding: utf-8 -*-
import re
from abc import ABCMeta, abstractmethod
import sqlite3

browser_directory_name = "browser_history"


class Browser:
    __metaclass__ = ABCMeta

    @abstractmethod
    def filter_history(self, category_filter):
        raise NotImplementedError


"""
moz_annos: Downloads, ID === ID von History
moz_places: History, ID universal
moz_historyvisits: Vergangene Website besuche, ID === ID von History
"""


class Firefox(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_ALL_HISTORY = "SELECT * FROM moz_places ORDER BY id"
        self.DELETE_HISTORY_BY_ID = "DELETE FROM moz_places WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM moz_historyvisits WHERE id = (?)"
        self.DELETE_DOWNLOADS_BY_ID = "DELETE FROM moz_annos WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        cursor = db.cursor()
        cursor.execute(self.GET_ALL_HISTORY)
        filter_list = category_filter.get_filter_list()
        for item in cursor.fetchall():
            print("[ITEM] " + str(item[1]))
            # Only keep items that are in the whitelist
            if category_filter.use_whitelist:
                for item_filter in filter_list:
                    print("[FILTER] " + item_filter)
                    if not re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(item[1])):
                        cursor.execute(self.DELETE_HISTORY_BY_ID, (item[0],))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (item[0],))
                        cursor.execute(self.DELETE_DOWNLOADS_BY_ID, (item[0],))
                        db.commit()
            # Only delete things that are in the blacklist
            else:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(item[1])):
                        cursor.execute(self.DELETE_HISTORY_BY_ID, (item[0],))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (item[0],))
                        cursor.execute(self.DELETE_DOWNLOADS_BY_ID, (item[0],))
                        db.commit()
