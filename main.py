from __future__ import print_function
from argparse import ArgumentParser
import datetime
from io import BytesIO
from Registry import Registry
from TSKUtility import TSKUtil
import codecs
import re

browser_list = []

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


def display_names_from_key(subkeys):
    for value in subkeys:
        value_name = value.name()
        try:
            display_name = value.value("DisplayName").value()
        except:
            try:
                display_name = value.value("").value()
            except:
                display_name = value_name
        if display_name not in browser_list:
            browser_list.append(display_name)

        print(f"Key: {display_name}")


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
        display_names_from_key(subkeys)

    except:
        print("[!] Error finding StartMenuInternet key")

    try:
        print("[*] for x86 bit systems...")
        uninstall_key = root.find_key("Clients")\
            .find_key("StartMenuInternet")
        subkeys = uninstall_key.subkeys()
        display_names_from_key(subkeys)

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
        display_names_from_key(subkeys)
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
        display_names_from_key(subkeys)
    except:
        print("[!] Error finding uninstall key")


def open_file_as_reg(reg_file):
    file_size = reg_file.info.meta.size
    file_content = reg_file.read_random(0, file_size)
    file_like_obj = BytesIO(file_content)
    return Registry.Registry(file_like_obj)


def main(evidence, image_type):
    tsk_util = TSKUtil(evidence, image_type)

    # Software Hive
    tsk_software_hive = tsk_util.recurse_files("software", "/Windows/system32/config", "equals", False)
    software_hive = open_file_as_reg(tsk_software_hive[0][2])
    # Alle Programme zu viel -> liste mit allen Browsern zum Abgleich?
    process_uninstall_key_from_hive(software_hive)
    process_start_menu_internet(software_hive)

    users = tsk_util.find_users("/users")
    user_ntuser = []
    for user in users:
        ntuser = tsk_util.recurse_files("ntuser.dat", "/users/" + user, "equals")
        user_ntuser.append(ntuser)
        print(f"\n[*] Getting recent opened application for user {user}...\n")
        user_hive = open_file_as_reg(ntuser[0][2])
        last_opened_applications = process_recent_opened_applications(user_hive)
        for application in last_opened_applications:
            print(application)


if __name__ == '__main__':
    parser = ArgumentParser('Evidence from Windows Registry')
    parser.add_argument('EVIDENCE_FILE', help="Path to evidence file (raw)")
    # TODO: Implement ewf functionality
    parser.add_argument('IMAGE_TYPE', help = "Evidence file format", choices = ('ewf', 'raw'))
    args = parser.parse_args()
    main(args.EVIDENCE_FILE, args.IMAGE_TYPE)
