import os
from typing import Mapping, Set, Type

from . import SlicedModelFile
from .ctb import CTBFile
from .cbddlp import CBDDLPFile
from .fdg import FDGFile
from .photon import PhotonFile
from .pws import PwsFile
from .pwms import PwmsFile

EXTENSION_TO_FILE_FORMAT: Mapping[str, Type[SlicedModelFile]] = {
	".ctb": CTBFile,
	".cbddlp": CBDDLPFile,
	".photon": PhotonFile,
	".fdg": FDGFile,
	".pws": PwsFile,
	".pw0": PwmsFile,
	".pwmo": PwmsFile,
	".pwms": PwmsFile,
	".pwmx": PwmsFile,
}

def get_file_format(filename: str) -> Type[SlicedModelFile]:
	(_, extension) = os.path.splitext(filename)

	file_format = EXTENSION_TO_FILE_FORMAT.get(extension.lower())

	assert file_format is not None
	return file_format


def get_supported_extensions() -> Set[str]:
	return set(EXTENSION_TO_FILE_FORMAT.keys())
