# -*- encoding: utf-8 -*-
import pathlib
import re
import sqlite3


class CategoryFilter:
    def __init__(self, whitelist=None, blacklist=None, use_whitelist=True):
        if blacklist is None:
            blacklist = []
        if whitelist is None:
            whitelist = []
        self.whitelist = whitelist
        self.blacklist = blacklist
        self.use_whitelist = use_whitelist

        db_path = pathlib.Path(__file__).parent.joinpath("Linkcollection.sqlite")
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db_cursor = self.db.cursor()

    def get_categories_from_source(self):
        categories = []
        GET_CATEGORIES = """select distinct category from urls;"""
        self.db_cursor.execute(GET_CATEGORIES)
        db_categories = self.db_cursor.fetchall()
        for category in db_categories:
            categories.append(category[0])
        return categories

    def find_match_in_category(self, category, item):
        GET_URL_BY_CATEGORY = """select url from urls where urls.category=(?)"""
        match = re.match(r"((http:\/\/)?(https:\/\/)?((\w*[-]*)+(\.)*)+)", item)
        if match:
            cursor = self.db.execute(GET_URL_BY_CATEGORY, (category,))
            for url in cursor:
                if url[0] == match[0]:
                    return True
        return False

    def add_category_to_whitelist(self, category):
        self.whitelist.append(category)

    def add_category_to_blacklist(self, category):
        self.blacklist.append(category)