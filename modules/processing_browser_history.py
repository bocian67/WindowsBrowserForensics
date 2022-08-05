# -*- encoding: utf-8 -*-
import re
from abc import ABCMeta, abstractmethod
import sqlite3
import pyesedb

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
        self.GET_ALL_HISTORY = "SELECT v.id, v.place_id, u.url from moz_historyvisits as v inner join moz_places as u on v.place_id = u.id"
        self.DELETE_URL_BY_ID = "DELETE FROM moz_places WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM moz_historyvisits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        cursor = db.cursor()
        cursor.execute(self.GET_ALL_HISTORY)
        filter_list = category_filter.get_filter_list()
        for item in cursor.fetchall():
            history_id = item[0]
            url_id = item[1]
            url_string = item[2]
            found_match = False
            # Only keep items that are in the whitelist
            if category_filter.use_whitelist:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if not found_match:
                    cursor.execute(self.DELETE_URL_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (history_id,))
                    db.commit()
            # Only delete things that are in the blacklist
            else:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if found_match:
                    cursor.execute(self.DELETE_URL_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (history_id,))
                    db.commit()


class Chrome(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url from visits as v inner join urls as u on v.url = u.id"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        cursor = db.cursor()
        cursor.execute(self.GET_JOINED_HISTORY)
        filter_list = category_filter.get_filter_list()
        for item in cursor.fetchall():
            visit_id = item[0]
            url_id = item[1]
            url_string = item[2]
            found_match = False
            # Only keep items that are in the whitelist
            if category_filter.use_whitelist:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if not found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()
            # Only delete things that are in the blacklist
            else:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()


class Opera(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url from visits as v inner join urls as u on v.url = u.id;"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        cursor = db.cursor()
        cursor.execute(self.GET_JOINED_HISTORY)
        filter_list = category_filter.get_filter_list()
        for item in cursor.fetchall():
            visit_id = item[0]
            url_id = item[1]
            url_string = item[2]
            found_match = False
            # Only keep items that are in the whitelist
            if category_filter.use_whitelist:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if not found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()
            # Only delete things that are in the blacklist
            else:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()


class Edge(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url from visits as v inner join urls as u on v.url = u.id"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        cursor = db.cursor()
        cursor.execute(self.GET_JOINED_HISTORY)
        filter_list = category_filter.get_filter_list()
        for item in cursor.fetchall():
            visit_id = item[0]
            url_id = item[1]
            url_string = item[2]
            found_match = False
            # Only keep items that are in the whitelist
            if category_filter.use_whitelist:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if not found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()
            # Only delete things that are in the blacklist
            else:
                for item_filter in filter_list:
                    if re.match(r"(^|^[^:]+:\/\/|[^\.]+\.)" + item_filter, str(url_string)):
                        found_match = True
                        break
                if found_match:
                    cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                    cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                    db.commit()


# TODO: Delete is not implemented
class InternetExplorer(Browser):
    def __init__(self, location):
        self.location = location

    def filter_history(self, category_filter):
        file = open(self.location, "rb")
        esedb_file = pyesedb.file()
        esedb_file.open_file_object(file)
        containers_table = esedb_file.get_table_by_name("Containers")
        web_history_tables = []
        urls = []
        for record in range(0, containers_table.get_number_of_records() - 1):
            container_record = containers_table.get_record(record)
            container_id = container_record.get_value_data_as_integer(0)
            container_name = container_record.get_value_data_as_string(8)
            container_directory = container_record.get_value_data_as_string(10)
            if container_name == "History" and "History.IE5" in container_directory:
                web_history_tables += [container_id]

        for record in web_history_tables:
            web_history_table = esedb_file.get_table_by_name("Container_" + str(record))
            for j in range(0, web_history_table.get_number_of_records() - 1):
                web_history_record = web_history_table.get_record(j)
                url_string = web_history_record.get_value_data_as_string(17)
                splitted_url = str(url_string).split("@")
                url = splitted_url[-1]
                urls.append(url)
        esedb_file.close()
        file.close()
