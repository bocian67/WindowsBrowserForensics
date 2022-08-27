# -*- encoding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import sqlite3
import pyesedb

browser_directory_name = "browser_history"


class Browser:
    # Parent class, browsers should implement this
    __metaclass__ = ABCMeta

    @abstractmethod
    def filter_history(self, category_filter):
        raise NotImplementedError


class Firefox(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_ALL_HISTORY = "SELECT v.id, v.place_id, u.url, u.id from moz_places as u left outer join moz_historyvisits as v on v.place_id = u.id"
        self.DELETE_URL_BY_ID = "DELETE FROM moz_places WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM moz_historyvisits WHERE id = (?)"

    def filter_history(self, category_filter):
        # Filter history using browser database and category filter
        db = sqlite3.connect(self.location)
        for item in db.execute(self.GET_ALL_HISTORY):
            # Using the history, get ids and url from table
            historyvisits_id = item[0]
            url_string = item[2]
            places_id = item[3]
            match = category_filter.get_url_category(str(url_string))
            # If a match in the url base was found, use filter
            if match is not None:
                # Only keep items that are in the whitelist
                if category_filter.use_whitelist:
                    if match not in category_filter.whitelist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URL_BY_ID, (places_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (historyvisits_id,))
                else:
                    # Only delete things that are in the blacklist
                    if match in category_filter.blacklist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URL_BY_ID, (places_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (historyvisits_id,))
        db.commit()


class Chrome(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url, u.id from urls as u left outer join visits as v on v.url = u.id"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        for item in db.execute(self.GET_JOINED_HISTORY):
            visit_id = item[0]
            url_string = item[2]
            url_id = item[3]
            match = category_filter.get_url_category(str(url_string))
            if match is not None:
                # Only keep items that are in the whitelist
                if category_filter.use_whitelist:
                    if match not in category_filter.whitelist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                # Only delete things that are in the blacklist
                else:
                    if match in category_filter.blacklist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
        db.commit()


class Opera(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url, u.id from urls as u left outer join visits as v on v.url = u.id"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        for item in db.execute(self.GET_JOINED_HISTORY):
            visit_id = item[0]
            url_string = item[2]
            url_id = item[3]
            match = category_filter.get_url_category(str(url_string))
            if match is not None:
                # Only keep items that are in the whitelist
                if category_filter.use_whitelist:
                    if match not in category_filter.whitelist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                # Only delete things that are in the blacklist
                else:
                    if match in category_filter.blacklist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
        db.commit()


class Edge(Browser):
    def __init__(self, location):
        self.location = location
        self.GET_JOINED_HISTORY = "SELECT v.id, v.url, u.url, u.id from urls as u left outer join visits as v on v.url = u.id"
        self.DELETE_URLS_BY_ID = "DELETE FROM urls WHERE id = (?)"
        self.DELETE_VISITS_BY_ID = "DELETE FROM visits WHERE id = (?)"

    def filter_history(self, category_filter):
        db = sqlite3.connect(self.location)
        for item in db.execute(self.GET_JOINED_HISTORY):
            visit_id = item[0]
            url_string = item[2]
            url_id = item[3]
            match = category_filter.get_url_category(str(url_string))
            if match is not None:
                # Only keep items that are in the whitelist
                if category_filter.use_whitelist:
                    if match not in category_filter.whitelist:
                        cursor = db.cursor()
                        cursor.execute(self.DELETE_URLS_BY_ID, (url_id,))
                        cursor.execute(self.DELETE_VISITS_BY_ID, (visit_id,))
                # Only delete things that are in the blacklist
                else:
                    if match in category_filter.blacklist:
                        cursor = db.cursor()
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
