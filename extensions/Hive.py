from io import BytesIO

from regipy.registry import RegistryHive, NKRecord
from regipy.structs import REGF_HEADER
from regipy.utils import boomerang_stream, identify_hive_type


class Hive(RegistryHive):
    def __init__(self, hive):
        self.partial_hive_path = None
        self.hive_type = None

        file_size = hive.info.meta.size
        file_content = hive.read_random(0, file_size)
        file_like_obj = BytesIO(file_content)

        self._stream = file_like_obj

        with boomerang_stream(self._stream) as s:
            self.header = REGF_HEADER.parse_stream(s)

            # Get the first cell in root HBin, which is the root NKRecord:
            root_hbin = self.get_hbin_at_offset()
            root_hbin_cell = next(root_hbin.iter_cells(s))
            self.root = NKRecord(root_hbin_cell, s)
        self.name = self.header.file_name

        try:
            self.hive_type = identify_hive_type(self.name)
        except:
            print("Could not parse Hive")
