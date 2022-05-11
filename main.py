from __future__ import print_function

import json
import random
from argparse import ArgumentParser
import datetime
from io import BytesIO
from os import listdir
from os.path import isfile, join

from Registry import Registry
from TSKUtility import TSKUtil
import codecs
import re
from difflib import SequenceMatcher
from pathlib import Path
import os

tsk_util = None
browser_list = []
browser_name_threshold = 0.8
findings = []
users = []
windows_version = ""
output_dir = ""
counter = 0


def get_windows_version(hive):
    root = hive.root()
    current_version = root.find_key("Microsoft") \
        .find_key("Windows NT") \
        .find_key("CurrentVersion")
    value = str(current_version.value("ProductName").value())
    regex_match = re.search("Windows (\w+) \w+", value)
    if regex_match:
        value = regex_match.group(1)

    return value


def parse_windows_filetime(date_value):
    microseconds = float(date_value) / 10
    ts = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=microseconds)
    return ts.strftime('%Y-%m-%d %H:%M:%S.%f')


def parse_unix_epoch(date_value):
    ts = datetime.datetime.fromtimestamp(date_value)
    return ts.strftime('%Y-%m-%d %H:%M:%S.%f')


def decode_value(value):
    guid_regex = re.compile("{[\s\S]+}")
    has_guid = guid_regex.search(value)
    guid = ""
    if has_guid:
        guid = has_guid.group(0)
        value = value[has_guid.end(0):]
    decoded = codecs.decode(value, "rot_13")
    return_value = guid + decoded
    return return_value


def check_registry_value_with_known_browsers(value, threshold=browser_name_threshold):
    value_name = value.name()
    try:
        display_name = value.value("DisplayName").value()
        install_location = value.value("InstallLocation").value()
    except:
        try:
            display_name = value.value("").value()
        except:
            display_name = value_name

    found_browser = check_name_with_known_browsers(display_name, threshold)
    if found_browser is not None:
        get_database(found_browser)


def get_database(found_browser):
    # Portable Browser
    if "portable" in found_browser and found_browser["portable"] is True:
        pass
    else:
        # Get database location in Windows
        if "databases" in found_browser:
            databases = found_browser["databases"]
            if windows_version in databases:
                database_locations = databases[windows_version]
            else:
                default_version = databases["default"]
                database_locations = databases[default_version]

            database_name = databases["name"]
            for database_location in database_locations:
                # Replace <user> in database location
                if "<user>" in database_location:
                    for user in users:
                        user_database_location = database_location.replace("<user>", user)
                        print(f"\t{user_database_location}")
                        database = tsk_util.recurse_files(database_name, user_database_location, "equals", False, True)
                        if database is not None:
                            file_name_directory = "/".join([found_browser["name"], user, str(database_name)])
                            extract_file(database[0][2], file_name_directory)
                else:
                    print(f"\t{database_location}")
                    database = tsk_util.recurse_files(database_name, user_database_location, "equals", False, True)
                    if database is not None:
                        file_name_directory = "/".join([found_browser["name"], str(database_name)])
                        extract_file(database[0][2], file_name_directory)

# Output:
    # Firefox
        # Viktor Web
                # places_1.sqlite
                # places_1.sqlite.txt -> hash
                # places_2.sqlite
                # + Hash-Vergleich, falls doppelt wieder löschen
    # Opera

# Container (ewf):


def extract_file(file, file_name):
    file_size = file.info.meta.size
    file_content = file.read_random(0, file_size)
    path = Path(output_dir).joinpath(file_name)
    print(path)
    os.makedirs(path.parent, exist_ok=True)

    files_in_directory = [f for f in listdir(str(path.parent)) if isfile(join(path.parent, f))]
# TODO: FIX
    if len(files_in_directory) > 0:
        file_name_without_ext = path.stem
        ext = path.suffix
        file_name_without_ext += "_" + str(len(files_in_directory))
        path = path.parent + file_name_without_ext + ext

    with open(path, "wb") as f:
        f.write(file_content)



def check_name_with_known_browsers(display_name, threshold=browser_name_threshold):
    for browser in browser_list:
        browser_name = browser["name"]
        seq_ratio = SequenceMatcher(a=display_name, b=browser_name).ratio()
        # print(f"{display_name} -- {browser_name}: {seq_ratio}")
        if seq_ratio >= threshold:
            print(f"[#] Browser: {display_name}")
            return browser
        else:
            for browser_ref in browser["references"]:
                seq_ratio = SequenceMatcher(a=display_name, b=browser_ref).ratio()
                # print(f"{display_name} -- {browser_ref}: {seq_ratio}")
                if seq_ratio >= threshold:
                    print(f"[#] Browser: {display_name}")
                    return browser
    return None


def process_recent_opened_applications(hive):
    root = hive.root()
    applications = []
    try:
        userassist = root.find_key("SOFTWARE")\
            .find_key("Microsoft")\
            .find_key("Windows")\
            .find_key("CurrentVersion")\
            .find_key("Explorer")\
            .find_key("UserAssist")
        userassist_guids = userassist.subkeys()

        for guid in userassist_guids:
            count = guid.find_key("Count")
            count_values = count.values()
            for key in count_values:
                key_name = decode_value(key.name())
                applications.append(key_name)
    except:
        print("[!] Error getting last opened applications")
    return applications


def process_start_menu_internet(hive):
    root = hive.root()
    print("\n[*] Looking for StartMenuInternet key...\n")
    try:
        print("[*] for x64 bit systems...")
        uninstall_key = root.find_key("WOW6432Node")\
            .find_key("Clients")\
            .find_key("StartMenuInternet")
        subkeys = uninstall_key.subkeys()
        for value in subkeys:
            check_registry_value_with_known_browsers(value)

    except:
        print("[!] Error finding StartMenuInternet key")

    try:
        print("[*] for x86 bit systems...")
        uninstall_key = root.find_key("Clients")\
            .find_key("StartMenuInternet")
        subkeys = uninstall_key.subkeys()
        for value in subkeys:
            check_registry_value_with_known_browsers(value)

    except:
        print("[!] Error finding StartMenuInternet key")


def process_uninstall_key_from_hive(hive):
    print("\n[*] Processing uninstall keys from hive...\n")
    root = hive.root()
    # x32
    print("[*] looking in x32 bit location...")
    try:
        uninstall_key = root.find_key("WOW6432Node")\
            .find_key("Microsoft")\
            .find_key("Windows")\
            .find_key("CurrentVersion")\
            .find_key("Uninstall")
        subkeys = uninstall_key.subkeys()
        for value in subkeys:
            check_registry_value_with_known_browsers(value)
    except:
        print("[!] Error finding uninstall key")

    # x64
    print("[*] looking in x64 bit location...")
    try:
        uninstall_key = root.find_key("Microsoft")\
            .find_key("Windows")\
            .find_key("CurrentVersion")\
            .find_key("Uninstall")
        subkeys = uninstall_key.subkeys()
        for value in subkeys:
            check_registry_value_with_known_browsers(value)
    except:
        print("[!] Error finding uninstall key")


def open_file_as_reg(reg_file):
    file_size = reg_file.info.meta.size
    file_content = reg_file.read_random(0, file_size)
    file_like_obj = BytesIO(file_content)
    return Registry.Registry(file_like_obj)


def main(evidence, image_type, out_dir):
    global browser_list
    global users
    global windows_version
    global tsk_util
    global output_dir

    output_dir = out_dir

    # Load browser list from json
    with open("browsers.json", "r") as f:
        file_content = f.read()
        json_file_content = json.loads(file_content)
        browser_list = json_file_content["browsers"]
        f.close()

    tsk_util = TSKUtil(evidence, image_type)

    users = tsk_util.find_users("/users")

    # Software hive
    tsk_software_hive = tsk_util.recurse_files("software", "/Windows/system32/config", "equals", False, False)
    software_hive = open_file_as_reg(tsk_software_hive[0][2])

    # Get windows version (to find databases)
    windows_version = get_windows_version(software_hive)
    print(f"Windows Version: {windows_version}")

    # Uninstall key
    process_uninstall_key_from_hive(software_hive)

    # StartMenuInternet key
    process_start_menu_internet(software_hive)

    # ntuser.dat per user
    user_ntuser = []
    for user in users:
        ntuser = tsk_util.recurse_files("ntuser.dat", "/users/" + user, "equals")
        user_ntuser.append(ntuser)
        print(f"\n[*] Getting recent opened application for user {user}...\n")
        user_hive = open_file_as_reg(ntuser[0][2])

        # Last opened applications per user
        last_opened_applications = process_recent_opened_applications(user_hive)
        for application in last_opened_applications:
            path = Path(application)
            check_name_with_known_browsers(path.stem)


if __name__ == '__main__':
    parser = ArgumentParser('Evidence from Windows Registry')
    parser.add_argument('EVIDENCE_FILE', help="Path to evidence file")
    parser.add_argument('IMAGE_TYPE', help = "Evidence file format", choices = ('ewf', 'raw'))
    parser.add_argument('OUTPUT_DIR', help="Path to output directory for browser databases")
    args = parser.parse_args()

    main(args.EVIDENCE_FILE, args.IMAGE_TYPE, args.OUTPUT_DIR)
