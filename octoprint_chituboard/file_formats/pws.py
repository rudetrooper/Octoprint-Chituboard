import os
import pathlib
import struct
from dataclasses import dataclass
from typing import List, Mapping, Type, Tuple

import png
from typedstruct import LittleEndianStruct, StructType

from . import SlicedModelFile

@dataclass(frozen=True)
class PwsFileMark(LittleEndianStruct):
	mark1: int = StructType.unsigned_char()
	mark2: int = StructType.unsigned_char()
	mark3: int = StructType.unsigned_char()
	mark4: int = StructType.unsigned_char()
	mark5: int = StructType.unsigned_char()
	mark6: int = StructType.unsigned_char()
	mark7: int = StructType.unsigned_char()
	mark8: int = StructType.unsigned_char()
	mark9: int = StructType.unsigned_char()
	mark10: int = StructType.unsigned_char()
	mark11: int = StructType.unsigned_char()
	mark12: int = StructType.unsigned_char()
	version: int = StructType.uint32()
	areaNum: int = StructType.uint32()
	header_offset: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	preview_offset: int = StructType.uint32()
	unknown_02: int = StructType.uint32()
	layer_defs_offset: int = StructType.uint32()
	unknown_03: int = StructType.uint32()
	layer_img_offset: int = StructType.uint32()
	
# ~ @dataclass(frozen=True)
# ~ class PwsHeaderMark(LittleEndianStruct):
	# ~ mark: str = StructType.chars().decode()
	# ~ length: int = StructType.uint32()  # 04: Always 0x01

@dataclass(frozen=True)
class PwsHeader(LittleEndianStruct):
	mark1: int = StructType.unsigned_char()
	mark2: int = StructType.unsigned_char()
	mark3: int = StructType.unsigned_char()
	mark4: int = StructType.unsigned_char()
	mark5: int = StructType.unsigned_char()
	mark6: int = StructType.unsigned_char()
	mark7: int = StructType.unsigned_char()
	mark8: int = StructType.unsigned_char()
	mark9: int = StructType.unsigned_char()
	mark10: int = StructType.unsigned_char()
	mark11: int = StructType.unsigned_char()
	mark12: int = StructType.unsigned_char()
	section_length: int = StructType.uint32()
	pixel_size: float = StructType.float32()
	layer_height_mm: float = StructType.float32()
	layer_exposure: float = StructType.float32()  # Layer exposure(in seconds)
	layer_off_time: float = StructType.float32()  # Layer off time(in seconds)
	bottom_exposure: float = StructType.float32()  # Bottom layers exposure
	bottom_count: int = StructType.uint32()  # Number of bottom layers
	lift_height: float = StructType.float32()
	lift_speed: float = StructType.float32()
	retract_speed: float = StructType.float32()
	volume_ml: float = StructType.float32()
	anti_alias_level: int = StructType.uint32()
	resolution_x: int = StructType.uint32()
	resolution_y: int = StructType.uint32()
	weight_gr: float = StructType.float32()  # resin weight in grams
	cost_dollars: float = StructType.float32()  # slicers estimated resin cost USD
	resin_type: float = StructType.float32()
	per_layer_override: float = StructType.float32()
	unknown_01: int = StructType.uint32()  # 2c:
	unknown_02: int = StructType.uint32()  # 30:
	unknown_03: int = StructType.uint32()  # 34:

@dataclass(frozen=True)
class PwsPreviewMark(LittleEndianStruct):
	mark1: int = StructType.unsigned_char()
	mark2: int = StructType.unsigned_char()
	mark3: int = StructType.unsigned_char()
	mark4: int = StructType.unsigned_char()
	mark5: int = StructType.unsigned_char()
	mark6: int = StructType.unsigned_char()
	mark7: int = StructType.unsigned_char()
	mark8: int = StructType.unsigned_char()
	mark9: int = StructType.unsigned_char()
	mark10: int = StructType.unsigned_char()
	mark11: int = StructType.unsigned_char()
	mark12: int = StructType.unsigned_char()
	layer_count: int = StructType.uint32()  # 04: Always 0x01

@dataclass(frozen=True)
class PwsPreview(LittleEndianStruct):
	mark1: int = StructType.unsigned_char()
	mark2: int = StructType.unsigned_char()
	mark3: int = StructType.unsigned_char()
	mark4: int = StructType.unsigned_char()
	mark5: int = StructType.unsigned_char()
	mark6: int = StructType.unsigned_char()
	mark7: int = StructType.unsigned_char()
	mark8: int = StructType.unsigned_char()
	mark9: int = StructType.unsigned_char()
	mark10: int = StructType.unsigned_char()
	mark11: int = StructType.unsigned_char()
	mark12: int = StructType.unsigned_char()
	image_length: int = StructType.uint32()
	resolution_x: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	resolution_y: int = StructType.uint32()
	# ~ image_offset: int = StructType.uint32()
	# ~ image_length: int = StructType.uint32()
	# ~ unknown_01: int = StructType.uint32()
	# ~ unknown_02: int = StructType.uint32()
	# ~ unknown_03: int = StructType.uint32()
	# ~ unknown_04: int = StructType.uint32()

@dataclass(frozen=True)
class PwsLayerMark(LittleEndianStruct):
	mark1: bytes = StructType.char()
	mark2: int = StructType.unsigned_char()
	mark3: int = StructType.unsigned_char()
	mark4: int = StructType.unsigned_char()
	mark5: int = StructType.unsigned_char()
	mark6: int = StructType.unsigned_char()
	mark7: int = StructType.unsigned_char()
	mark8: int = StructType.unsigned_char()
	mark9: int = StructType.unsigned_char()
	mark10: int = StructType.unsigned_char()
	mark11: int = StructType.unsigned_char()
	mark12: int = StructType.unsigned_char()
	image_offset: int = StructType.uint32()
	layer_count: int = StructType.uint32()  # 04: Always 0x01

@dataclass(frozen=True)
class PwsLayerDef(LittleEndianStruct):
	layer_height_mm: float = StructType.float32()  # 00:
	layer_exposure: float = StructType.float32()  # 04:
	layer_off_time: float = StructType.float32()  # 08:
	image_offset: int = StructType.uint32()  # 0c:
	image_length: int = StructType.uint32()  # 10:
	unknown_01: int = StructType.uint32()  # 14:
	unknown_02: int = StructType.uint32()  # 18:
	unknown_03: int = StructType.uint32()  # 1c:
	unknown_04: int = StructType.uint32()  # 20:



REPEAT_RGB15_MASK: int = 1 << 5


def _read_image(width: int, height: int, data: bytes) -> png.Image:
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data):
		color16 = int(struct.unpack_from("<H", data, i)[0])
		i += 2
		repeat = 1
		if color16 & REPEAT_RGB15_MASK:
			repeat += int(struct.unpack_from("<H", data, i)[0]) & 0xFFF
			i += 2

		(r, g, b) = (
			(color16 >> 0) & 0x1F,
			(color16 >> 6) & 0x1F,
			(color16 >> 11) & 0x1F,
		)

		while repeat > 0:
			array[-1] += [r, g, b]
			repeat -= 1

			x += 1
			if x == width:
				x = 0
				array.append([])

	array.pop()

	return png.from_array(array, "RGB;5")

EXTENSION_TO_BED_SIZE: Mapping[str, Tuple[str, float, float, float]] = {
	".pws": ("Anycubic Photon S", 68.04, 120.96, 165),
	".pw0": ("Anycubic Photon Zero", 55.44, 98.64, 150),
	".pwmo": ("Anycubic Photon Mono", 68.04, 120.96, 165),
	".pwms": ("Anycubic Photon Mono SE", 78, 130, 160),
	".pwmx": ("Anycubic Photon Mono X", 120, 192, 245),
}

def _get_printer_info(filename):
	(_, extension) = os.path.splitext(filename)
	
	printer_info = EXTENSION_TO_BED_SIZE.get(extension.lower())

	assert printer_info is not None
	return printer_info

@dataclass(frozen=True)
class PwsFile(SlicedModelFile):
	@classmethod
	def read(self, path: pathlib.Path) -> "PwsFile":
		with open(str(path), "rb") as file:
			pws_filemark = PwsFileMark.unpack(file.read(PwsFileMark.get_size()))
			pws_header = PwsHeader.unpack(file.read(PwsHeader.get_size()))
			pws_layermark = PwsLayerMark.unpack(file.read(PwsLayerMark.get_size()))
						
			printer_info = _get_printer_info(path.name)
			printer_name = printer_info[0]
			
			end_byte_offset_by_layer = []
			# ~ for layer in range(0, pws_header.layer_count):
				# ~ file.seek(
					# ~ pws_header.layer_defs_offset + layer * PwsLayerDef.get_size()
				# ~ )
				# ~ layer_def = PwsLayerDef.unpack(file.read(PwsLayerDef.get_size()))
				# ~ end_byte_offset_by_layer.append(
					# ~ layer_def.image_offset + layer_def.image_length
				# ~ )
			# calc print time:
			# Bottom
			
			return PwsFile(
				filename=path.name,
				bed_size_mm=(
					round(pws_header.resolution_x*pws_header.pixel_size/1000.0, 4),
					round(pws_header.resolution_y*pws_header.pixel_size/1000.0, 4),
					printer_info[3]
				),
				height_mm=round(pws_header.layer_height_mm*pws_layermark.layer_count, 4),
				layer_height_mm=pws_header.layer_height_mm,
				layer_count=pws_layermark.layer_count,
				resolution=(pws_header.resolution_x, pws_header.resolution_y),
				print_time_secs = 1550,
				# ~ print_time_secs=pws_header.print_time, # will hae to calculate from file info
				# ~ end_byte_offset_by_layer=end_byte_offset_by_layer,
				end_byte_offset_by_layer=[4,5],
				slicer_version="1.8.0.0",
				printer_name=printer_name,# Use filename ending to determine printer name
			)

	@classmethod
	def read_preview(cls, path: pathlib.Path) -> png.Image:
		with open(str(path), "rb") as file:
			pws_filemark = PwsFileMark.unpack(file.read(PwsFileMark.get_size()))
			pws_header = PwsHeader.unpack(file.read(PwsHeader.get_size()))
			# image offset is PWSpreview offset + pwspreview.getsize()

			file.seek(pws_header.preview_offset)
			preview = PwsPreview.unpack(file.read(PwsPreview.get_size()))

			file.seek(pws_header.preview_offset+PwsPreview.get_size())
			data = file.read(preview.image_length)

			return _read_image(preview.resolution_x, preview.resolution_y, data)
