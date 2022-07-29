variables.tsk_util = TSKUtil(evidence, image_type)

# Software hive
tsk_software_hive = variables.tsk_util.recurse_files("software", "/Windows/system32/config", "equals", False, False)
software_hive = open_file_as_reg(tsk_software_hive[0][2])

# Get windows version (to find databases)
windows_version = get_windows_version(software_hive)
print(f"Windows Version: {windows_version}")

# Uninstall key
process_uninstall_key_from_hive(software_hive)

# StartMenuInternet key
process_start_menu_internet(software_hive)