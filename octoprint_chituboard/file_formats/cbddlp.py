from typing import Type

from . import SlicedModelFile
from .ctb import CTBFile


# we just treat cbddlp as a ctb file, since they're very similar to each other
CBDDLPFile: Type[SlicedModelFile] = CTBFile
