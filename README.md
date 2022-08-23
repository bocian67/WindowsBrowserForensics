# About
This software was made to automatically extract databases from currently popular browsers - namely Internet Explorer, 
Microsoft Edge, Google Chrome, Mozilla Firefox and Opera, from forensic Windows disk copies. 
In the process, these browsers are detected in the disk image by registry references
and then their databases are extracted from the common paths. All histories are then filtered using a dynamic list. 
The result is a new disk image with the preprocessed databases of the browsers.
This should save investigators time in searching the browser data by having the history already filtered.

# Installation
## Requirements
1. Install Python3
2. Get Buildtools for C++: https://visualstudio.microsoft.com/visual-cpp-build-tools/
3. Then install python3 requirements:
`pip3 install -r requirements.txt`

# Usage
`python3 main.py <EVIDENCE_FILE> <IMAGE_TYPE> <TEMP_DRIVE> <OUTPUT_DIR>`

- EVIDENCE_FILE: Path to evidence file
- IMAGE_TYPE: Evidence file format (ewf, raw)
- TEMP_DRIVE: Path to temporary output directory for browser databases
- OUTPUT_DIR: Path to output directory for database image

## Supported Browsers
- Mozilla Firefox
- Microsoft Edge (from version 79)
- Internet Explorer
  - detected, but not filtered; currently ESE-database cannot be edited
- Google Chrome
- Opera

## How to edit Linkcollection.sqlite
Add url-base and your category in the table "urls".

## How to edit browsers.json
You can edit the browser list by adding or altering an object in the list. The structure is as is follows:
```json
...
  {
      "name": "BROWSER NAME",
      "references": ["ALSO A NAME FOR THAT BROWSER", "AND ANOTHER NAME"],
      "databases": {
        "default": "10",
        "name": "DATABASE NAME",
        "10": ["/path/to/database/directory/for/win/10/"],
        "7": ["/path/to/database/directory/for/win/7/"]
      },
      "_docs": "WHERE YOU FOUND YOUR INFORMATION"
    },
...
```