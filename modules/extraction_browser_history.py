# -*- encoding: utf-8 -*-
import json
import time
from difflib import SequenceMatcher
from pathlib import Path

from Menu import Menu
from categoryfilter import CategoryFilter
from extensions.Hive import Hive
from main import decode_value, open_file_as_reg, get_windows_version, extract_file_and_get_path
import variables
from modules.processing_browser_history import Firefox, Chrome, Opera, Edge

browser_list = []
browser_name_threshold = 0.8
windows_version = ""
found_browsers = []
written_browser_count = {}
browser_directory_name = "browser_history"
category_filter = CategoryFilter()


def __init__():
    global browser_list
    global windows_version
    global category_filter
    global found_browsers

    # Ask user which categories to choose from
    categories = category_filter.get_categories_from_source()
    white_black_selection = ["Whitelist", "Blacklist"]
    menu = Menu("Bitte auswählen, ob über Whitelist oder Blacklist geprüft werden soll", white_black_selection)
    selection = menu.show()
    if white_black_selection[selection[0]] == white_black_selection[0]:
        category_filter.use_whitelist = True
    else:
        category_filter.use_whitelist = False

    menu = Menu("Wähle die zu nutzenden Kategorien aus", categories,
                           epilogue="Zum Beispiel: 1,2,3 oder 1-4 oder 1,3-4\n")
    selection = menu.show()
    if category_filter.use_whitelist:
        for selection_id in selection:
            category_filter.add_category_to_whitelist(categories[selection_id])
    else:
        for selection_id in selection:
            category_filter.add_category_to_blacklist(categories[selection_id])
    start_time = time.time()

    # Load browser list from json
    with open("browsers.json", "r") as f:
        file_content = f.read()
        json_file_content = json.loads(file_content)
        browser_list = json_file_content["browsers"]
        f.close()

    # Software hive
    tsk_software_hive = variables.tsk_util.recurse_files("software", "/Windows/system32/config", "equals", False, False)

    software_hive = open_file_as_reg(tsk_software_hive[0][2])

    # Get windows version (to find databases)
    windows_version = get_windows_version(software_hive)
    print(f"Windows Version: {windows_version}")

    # Uninstall key
    process_uninstall_key_from_root(software_hive)

    # StartMenuInternet key
    process_start_menu_internet_from_root(software_hive)

    # Get Amcache.hve
    amcache = variables.tsk_util.recurse_files("Amcache.hve", "/Windows/appcompat/Programs", "equals", False, False)
    if len(amcache) == 0:
        print("[!] Could not find Amcache.hve")
    else:
        try:
            hive = open_file_as_reg(amcache[0][2])
            root = hive.get_key("Root")
            process_amcache_file_from_root(root)
        except:
            print("[!] Could not parse Amcache.hve")

    # ntuser.dat per user
    user_ntuser = []
    for user in variables.users:
        ntuser = variables.tsk_util.recurse_files("ntuser.dat", "/users/" + user, "equals")
        user_ntuser.append(ntuser)
        user_hive = open_file_as_reg(ntuser[0][2])

        # Uninstall Keys from user
        try:
            print(f"\n[*] Getting uninstall keys from user {user}...\n")
            process_uninstall_key_from_root(user_hive, True)
        except:
            print("[!] Could not find User SOFTWARE Hive")

        try:
            print(f"\n[*] Getting StartMenuInternet keys from user {user}...\n")
            process_start_menu_internet_from_root(user_hive, True)
        except:
            print("[!] Could not find User SOFTWARE Hive")

        # Last opened applications per user
        print(f"\n[*] Getting recent opened application for user {user}...\n")
        last_opened_applications = process_recent_opened_applications(user_hive)
        for application in last_opened_applications:
            path = Path(application)
            found_browser = check_name_with_known_browsers(path.stem, browser_name_threshold)
            if found_browser is not None and found_browser not in found_browsers:
                found_browsers.append(found_browser)

    get_databases()
    print_total_browsers()
    return start_time


def print_total_browsers():
    global found_browsers
    if len(found_browsers) > 0:
        print(f"[*] Found these {len(found_browsers)} Browsers:")
        for browser in found_browsers:
            browser_name = browser["name"]
            print(f"\t{browser_name}")
    else:
        print("[!] Could not find any browsers")


def check_registry_value_with_known_browsers(value, threshold=browser_name_threshold):
    global found_browsers
    value_name = value.name
    try:
        display_name = value.get_value("DisplayName")
        if display_name is None:
            display_name = value.get_value("")
            if display_name is None:
                display_name = value_name
        install_location = value.get_value("InstallLocation")
    except:
        try:
            display_name = value.get_value("")
        except:
            display_name = value_name

    found_browser = check_name_with_known_browsers(display_name, threshold)
    if found_browser is not None and found_browser not in found_browsers:
        print("[*] Found " + display_name)
        found_browsers.append(found_browser)


def get_databases():
    global written_browser_count
    global found_browsers

    for found_browser in found_browsers:
        # Portable Browser
        if "portable" in found_browser and found_browser["portable"] is True:
            # TODO: Portable browser db
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
                        for user in variables.users:
                            user_database_location = database_location.replace("<user>", user)
                            browser_name = found_browser["name"]
                            print(f"\tDatabase Location for {browser_name}: {user_database_location}")
                            database = variables.tsk_util.recurse_files(database_name, user_database_location,
                                                                        "equals", False, True)
                            if database is not None:
                                file_name_directory = "/".join([browser_directory_name, found_browser["name"],
                                                                user, str(database_name)])
                                if file_name_directory not in written_browser_count:
                                    written_browser_count[file_name_directory] = 1
                                extract_and_filter(database, file_name_directory, found_browser["name"])
                                written_browser_count[file_name_directory] += 1
                    else:
                        browser_name = found_browser["name"]
                        print(f"\tDatabase Location for {browser_name}: {database_location}")
                        database = variables.tsk_util.recurse_files(database_name, database_location, "equals",
                                                                    False, True)
                        if database is not None:
                            file_name_directory = "/".join([browser_directory_name, found_browser["name"],
                                                            str(database_name)])
                            if file_name_directory not in written_browser_count:
                                written_browser_count[file_name_directory] = 1
                            extract_and_filter(database, file_name_directory, found_browser["name"])
                            written_browser_count[file_name_directory] += 1


def check_name_with_known_browsers(display_name, threshold=browser_name_threshold):
    for browser in browser_list:
        browser_name = browser["name"]
        seq_ratio = SequenceMatcher(a=display_name, b=browser_name).ratio()
        if seq_ratio >= threshold:
            print(f"[#] Browser: {display_name}")
            return browser
        else:
            for browser_ref in browser["references"]:
                seq_ratio = SequenceMatcher(a=display_name, b=browser_ref).ratio()
                if seq_ratio >= threshold:
                    print(f"[#] Browser: {display_name}")
                    return browser
    return None


def process_recent_opened_applications(hive):
    applications = []
    try:
        userassist = hive.get_key("SOFTWARE")
        userassist = userassist.get_subkey("Microsoft")
        userassist = userassist.get_subkey("Windows")
        userassist = userassist.get_subkey("CurrentVersion")
        userassist = userassist.get_subkey("Explorer")
        userassist = userassist.get_subkey("UserAssist")
        for guid in userassist.iter_subkeys():
            count = guid.get_subkey("Count")
            for key in count.iter_values():
                key_name = decode_value(key.name)
                applications.append(key_name)
    except Exception as e:
        print(e)
        print("[!] Error getting last opened applications")
    return applications


def process_start_menu_internet_from_root(root, is_user_hive=False):
    print("\n[*] Looking for StartMenuInternet key...")
    try:
        print("[*] for x86 bit systems...")
        if is_user_hive:
            uninstall_key = root.get_key("SOFTWARE")
            uninstall_key = uninstall_key.get_subkey("WOW6432Node")
            uninstall_key = uninstall_key.get_subkey("Clients")
            uninstall_key = uninstall_key.get_subkey("StartMenuInternet")
        else:
            uninstall_key = root.get_key("WOW6432Node")
            uninstall_key = uninstall_key.get_subkey("Clients")
            uninstall_key = uninstall_key.get_subkey("StartMenuInternet")
        for value in uninstall_key.iter_subkeys():
            if value is not None:
                check_registry_value_with_known_browsers(value)
    except Exception as e:
        print(e)
        print("[!] Error finding StartMenuInternet key")

    try:
        print("[*] for x64 bit systems...")
        if is_user_hive:
            uninstall_key = root.get_key("SOFTWARE")
            uninstall_key = uninstall_key.get_subkey("Clients")
            uninstall_key = uninstall_key.get_subkey("StartMenuInternet")
        else:
            uninstall_key = root.get_key("Clients")
            uninstall_key = uninstall_key.get_subkey("StartMenuInternet")
        for value in uninstall_key.iter_subkeys():
            if value is not None:
                check_registry_value_with_known_browsers(value)
    except Exception as e:
        print(e)
        print("[!] Error finding StartMenuInternet key")


def process_uninstall_key_from_root(root, is_user_hive=False):
    print("\n[*] Processing uninstall keys from hive...")
    # x32
    print("[*] looking in x32 bit location...")
    try:
        if is_user_hive:
            uninstall_key = root.get_key("SOFTWARE")
            uninstall_key = uninstall_key.get_subkey("WOW6432Node")
            uninstall_key = uninstall_key.get_subkey("Microsoft")
            uninstall_key = uninstall_key.get_subkey("Windows")
            uninstall_key = uninstall_key.get_subkey("CurrentVersion")
            uninstall_key = uninstall_key.get_subkey("Uninstall")

        else:
            uninstall_key = root.get_key("WOW6432Node")
            uninstall_key = uninstall_key.get_subkey("Microsoft")
            uninstall_key = uninstall_key.get_subkey("Windows")
            uninstall_key = uninstall_key.get_subkey("CurrentVersion")
            uninstall_key = uninstall_key.get_subkey("Uninstall")
        for value in uninstall_key.iter_subkeys():
            if value is not None:
                check_registry_value_with_known_browsers(value)
    except Exception as e:
        print(e)
        print("[!] Error finding uninstall key")

    # x64
    print("[*] looking in x64 bit location...")
    try:
        if is_user_hive:
            uninstall_key = root.get_key("SOFTWARE")
            uninstall_key = uninstall_key.get_subkey("Microsoft")
            uninstall_key = uninstall_key.get_subkey("Windows")
            uninstall_key = uninstall_key.get_subkey("CurrentVersion")
            uninstall_key = uninstall_key.get_subkey("Uninstall")
        else:
            uninstall_key = root.get_key("Microsoft")
            uninstall_key = uninstall_key.get_subkey("Windows")
            uninstall_key = uninstall_key.get_subkey("CurrentVersion")
            uninstall_key = uninstall_key.get_subkey("Uninstall")
        for value in uninstall_key.iter_subkeys():
            if value is not None:
                check_registry_value_with_known_browsers(value)
    except Exception as e:
        print(e)
        print("[!] Error finding uninstall key")


def extract_and_filter(database, file_name_directory, browser_name):
    global category_filter
    path_to_db = extract_file_and_get_path(
        database[0][2],
        file_name_directory,
        written_browser_count[file_name_directory])

    if browser_name == "Firefox":
        browser = Firefox(path_to_db)
        browser.filter_history(category_filter)
    elif browser_name == "Chrome":
        browser = Chrome(path_to_db)
        browser.filter_history(category_filter)
    elif browser_name == "Opera":
        browser = Opera(path_to_db)
        browser.filter_history(category_filter)
    elif browser_name == "Edge":
        browser = Edge(path_to_db)
        browser.filter_history(category_filter)


def process_amcache_file_from_root(root):
    global found_browsers
    print("[*] Processing Amcache.hve file...")

    # Processing InventoryApplications key
    print("[*] Processing InventoryApplications Key...")
    try:
        inventory_application_key = root.get_subkey("InventoryApplication")
        for key in inventory_application_key.iter_subkeys():
            name = key.get_value("Name")
            if name is not None:
                found_browser = check_name_with_known_browsers(name, browser_name_threshold)
                if found_browser is not None and found_browser not in found_browsers:
                    print("[*] Found " + name)
                    found_browsers.append(found_browser)

    except Exception as e:
        print(e)
        print("[!] Could not locate InventoryApplication key")
        pass

    print("[*] Processing InventoryApplicationFile key")
    try:
        inventory_application_file_key = root.get_subkey("InventoryApplicationFile")
        for key in inventory_application_file_key.iter_subkeys():
            name = key.get_value("Name")
            if name is not None:
                found_browser = check_name_with_known_browsers(name, browser_name_threshold)
                if found_browser is not None and found_browser not in found_browsers:
                    print("[*] Found " + name)
                    found_browsers.append(found_browser)

    except Exception as e:
        print(e)
        print("[!] Could not locate InventoryApplicationFile key")
        pass
