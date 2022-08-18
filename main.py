# -*- encoding: utf-8 -*-
from __future__ import print_function

import codecs
import datetime
import os
import time
import re
import subprocess
from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path

from extensions.Hive import Hive
from win32_setctime import setctime

import variables
from TSKUtility import TSKUtil
from modules import extraction_browser_history


def main(evidence, image_type, temp_drive, out_dir):
    variables.temp_output_dir = temp_drive

    variables.tsk_util = TSKUtil(evidence, image_type)

    variables.users = variables.tsk_util.find_users("/users")

    # Use modules
    start_time = extraction_browser_history.__init__()

    # Create image
    make_image(out_dir)

    end_time = time.time()
    print("[*] Duration: " + str(end_time - start_time) + " seconds")


def make_image(out_dir):
    # Make image from partition
    out_dir_path = Path(out_dir) / "image"
    fkt_path = Path(os.path.realpath(__file__)).parent.joinpath("ftkimager/ftkimager.exe")
    execution = [str(fkt_path), str(variables.temp_output_dir), "--e01", str(out_dir_path), "--compress", "9"]
    subprocess.run(execution)


def open_file_as_reg(reg_file):
    file_size = reg_file.info.meta.size
    file_content = reg_file.read_random(0, file_size)
    file_like_obj = BytesIO(file_content)
    return Hive(file_like_obj)


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


def extract_file_and_get_path(file, file_name, count_file_name):
    file_size = file.info.meta.size

    # Get timestamps
    crtime = file.info.meta.crtime
    atime = file.info.meta.atime
    mtime = file.info.meta.mtime

    file_content = file.read_random(0, file_size)
    path = Path(variables.temp_output_dir).joinpath(file_name)
    os.makedirs(path.parent, exist_ok=True)

    file_name_without_ext = path.stem
    ext = path.suffix
    file_name_without_ext += "_" + str(count_file_name)
    path = path.parent.joinpath(str(file_name_without_ext) + str(ext))

    with open(path, "wb") as f:
        f.write(file_content)

    # Set timestamps
    try:
        setctime(path, crtime)
        os.utime(path, times=(atime, mtime))
        """
        Access time is changing due to copying.
        Things I tried:
            - using exFAT, but this changes the date -> time is gone
            - making the partition read only after writing files but time changes
            - Using FTK instead of dd for Windows
        """
    except:
        pass
    return path


def get_windows_version(hive):
    current_version = hive.get_key("SOFTWARE\Microsoft\Windows NT\CurrentVersion")
    value = str(current_version.get_value("ProductName"))
    regex_match = re.search("Windows (\w+) \w+", value)
    if regex_match:
        value = regex_match.group(1)
    return value


if __name__ == '__main__':
    parser = ArgumentParser('Evidence from Windows Registry')
    parser.add_argument('EVIDENCE_FILE', help="Path to evidence file")
    parser.add_argument('IMAGE_TYPE', help="Evidence file format", choices=('ewf', 'raw'))
    parser.add_argument('TEMP_DRIVE', help="Path to output directory for browser databases")
    parser.add_argument('OUTPUT_DIR', help="Path to output directory for browser databases")
    args = parser.parse_args()

    main(args.EVIDENCE_FILE, args.IMAGE_TYPE, args.TEMP_DRIVE, args.OUTPUT_DIR)
