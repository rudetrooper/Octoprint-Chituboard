from typing import Type

from . import SlicedModelFile
from .photon import PhotonFile


# we just treat cbddlp as a photon file, since they're very similar to each other
CBDDLPFile: Type[SlicedModelFile] = PhotonFile
