from pathlib import Path, WindowsPath, PosixPath
from dataclasses import dataclass
import platform
import os

@dataclass
class PathTranslator:
    path_str: str
    path_obj: Path = None
    system:str = platform.system()

    def __post_init__(self):
        if (self.system == "Linux") & (self.path_str.find("//") == 0):
            # //npo needs to be changed to /npo
            linux_str = self.path_str[1:]
            self.path_obj = Path(linux_str)
        self.path_obj = Path(self.path_str)
        assert self.path_obj.exists()

    def to_windows(self):
        return self.path_str

    @property
    def path(self):
        return self.path_obj







