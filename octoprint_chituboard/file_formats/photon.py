import pathlib
import struct
from dataclasses import dataclass
from typing import List

import png, time
from typedstruct import LittleEndianStruct, StructType
import numpy as np
from . import SlicedModelFile
from .rle import *


@dataclass(frozen=True)
class PhotonHeader(LittleEndianStruct):
	magic: int = StructType.uint32()  # 00: Always 0x12FD0019
	version: int = StructType.uint32()  # 04: Always 0x01
	bed_size_x_mm: float = StructType.float32()  # 08:
	bed_size_y_mm: float = StructType.float32()
	bed_size_z_mm: float = StructType.float32()
	unknown_01: int = StructType.uint32()  # 14
	unknown_02: int = StructType.uint32()
	height_mm: float = StructType.float32()
	layer_height_mm: float = StructType.float32()  # 20:
	layer_exposure: float = StructType.float32()  # 24: Layer exposure(in seconds)
	bottom_exposure: float = StructType.float32()  # 28: Bottom layers exposure
	layer_off_time: float = StructType.float32()  # 2c: Layer off time(in seconds)
	bottom_count: int = StructType.uint32()  # 30: Number of bottom layers
	resolution_x: int = StructType.uint32()  # 34:
	resolution_y: int = StructType.uint32()  # 38:
	high_res_preview_offset: int = StructType.uint32()
	# 3c: Offset of the high-res preview
	layer_defs_offset: int = StructType.uint32()  # 40: Offset of the layer definitions
	layer_count: int = StructType.uint32()  # 44:
	low_res_preview_offset: int = StructType.uint32()  # 48: Offset of the low-rew prev
	print_time: int = StructType.uint32()  # 4c: In seconds
	projector: int = StructType.uint32()  # 50: 0 = CAST, 1 = LCD_X_MIRROR
	param_offset: int = StructType.uint32()  # 54:
	param_size: int = StructType.uint32()  # 58:
	anti_alias_level: int = StructType.uint32()  # 5c:
	light_pwm: int = StructType.uint16()  # 60:
	bottom_light_pwm: int = StructType.uint16()  # 62:
	encryption_seed: int = StructType.uint32()  # 64:
	slicer_offset: int = StructType.uint32()
	slicer_size: int = StructType.uint32()


@dataclass(frozen=True)
class PhotonParam(LittleEndianStruct):
	bottom_lift_height: float = StructType.float32()  # 00:
	bottom_lift_speed: float = StructType.float32()  # 04:
	lift_height: float = StructType.float32()  # 08:
	lift_speed: float = StructType.float32()  # 0c:
	retract_speed: float = StructType.float32()  # 10:
	volume_ml: float = StructType.float32()  # 14: Volume of resin in ml
	weight_gr: float = StructType.float32()  # 18: resin weight in grams
	cost_dollars: float = StructType.float32()  # 1c: slicers estimated resin cost USD
	bottom_lift_off_time: float = StructType.float32()  # 20
	light_off_time: float = StructType.float32()  # 24:
	bottom_layer_count: int = StructType.uint32()  # 28:
	unknown_01: int = StructType.uint32()  # 2c:
	unknown_02: int = StructType.uint32()  # 30:
	unknown_03: int = StructType.uint32()  # 34:
	unknown_04: int = StructType.uint32()  # 38:


@dataclass(frozen=True)
class PhotonSlicer(LittleEndianStruct):
	skip_0: int = StructType.uint32()
	skip_1: int = StructType.uint32()
	skip_2: int = StructType.uint32()
	skip_3: int = StructType.uint32()
	skip_4: int = StructType.uint32()
	skip_5: int = StructType.uint32()
	skip_6: int = StructType.uint32()
	machine_offset: int = StructType.uint32()
	machine_size: int = StructType.uint32()
	encryption_mode: int = StructType.uint32()
	time_seconds: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	version_patch: int = StructType.unsigned_char()
	version_minor: int = StructType.unsigned_char()
	version_major: int = StructType.unsigned_char()
	version_release: int = StructType.unsigned_char()
	unknown_02: int = StructType.uint32()
	unknown_03: int = StructType.uint32()
	unknown_04: float = StructType.float32()
	unknown_05: int = StructType.uint32()
	unknown_06: int = StructType.uint32()
	unknown_07: float = StructType.float32()


@dataclass(frozen=True)
class PhotonLayerDef(LittleEndianStruct):
	layer_height_mm: float = StructType.float32()  # 00:
	layer_exposure: float = StructType.float32()  # 04:
	layer_off_time: float = StructType.float32()  # 08:
	image_offset: int = StructType.uint32()  # 0c:
	image_length: int = StructType.uint32()  # 10:
	unknown_01: int = StructType.uint32()  # 14:
	unknown_02: int = StructType.uint32()  # 18:
	unknown_03: int = StructType.uint32()  # 1c:
	unknown_04: int = StructType.uint32()  # 20:


@dataclass(frozen=True)
class PhotonPreview(LittleEndianStruct):
	resolution_x: int = StructType.uint32()
	resolution_y: int = StructType.uint32()
	image_offset: int = StructType.uint32()
	image_length: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	unknown_02: int = StructType.uint32()
	unknown_03: int = StructType.uint32()
	unknown_04: int = StructType.uint32()


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
	
def _read_layer(width: int, height: int, layernum:int, data: bytes) -> png.Image:
	
	return read_rle1image(width, height, data)

def _read_layer_array(width: int, height: int, layernum:int, data: bytes):
	return read_rle1array(width, height, data)
	
def get_printarea(resolution,header,image):
	resolutionX = header.resolution_x
	resolutionY = header.resolution_y
	PixelSize = (header.bed_size_x_mm*1000)/resolutionX
	rows_with_white= np.max(image, axis=1)
	col_with_white= np.max(image, axis=0)
	row_low = np.argmax(rows_with_white)
	row_high = -np.argmax(rows_with_white[::-1])
	col_low = np.argmax(col_with_white)
	col_high = -np.argmax(col_with_white[::-1])
	minX = float(row_low*PixelSize/1000)
	maxX = float((resolutionY+row_high)*PixelSize/1000)
	minY = float(col_low*PixelSize/1000)
	maxY = float((resolutionX+col_high)*PixelSize/1000)
	width = float(maxX-minX)
	depth = float(maxY-minY)
	height = float(header.height_mm)
	results = {}
	results["printing_area"] = {"minX":minX, "maxX":maxX, "minY":minY,"maxY":maxY}
	results["dimensions"] = {"width":width, "depth":depth, "height":height}
	return results


@dataclass(frozen=True)
class PhotonFile(SlicedModelFile):
	@classmethod
	def read(self, path: pathlib.Path) -> "PhotonFile":
		with open(str(path), "rb") as file:
			photon_header = PhotonHeader.unpack(file.read(PhotonHeader.get_size()))
			
			file.seek(photon_header.param_offset)
			photon_param = PhotonParam.unpack(file.read(PhotonParam.get_size()))

			file.seek(photon_header.slicer_offset)
			photon_slicer = PhotonSlicer.unpack(file.read(PhotonSlicer.get_size()))

			file.seek(photon_slicer.machine_offset)
			printer_name = file.read(photon_slicer.machine_size).decode()

			end_byte_offset_by_layer = []
			for layer in range(0, photon_header.layer_count):
				file.seek(
					photon_header.layer_defs_offset + layer * PhotonLayerDef.get_size()
				)
				layer_def = PhotonLayerDef.unpack(file.read(PhotonLayerDef.get_size()))
				end_byte_offset_by_layer.append(
					layer_def.image_offset + layer_def.image_length
				)
			file.seek(photon_header.layer_defs_offset + 0 * PhotonLayerDef.get_size())
			first_layer = PhotonLayerDef.unpack(file.read(PhotonLayerDef.get_size()))
			
			file.seek(first_layer.image_offset)
			data = file.read(first_layer.image_length)
			results = {}
			image = _read_layer_array(
				photon_header.resolution_x,
				photon_header.resolution_y,
				0,
				data)
			try:
				imlayer = np.array(image)
				results = get_printarea(imlayer.shape,photon_header,imlayer)
			except:
				results = {}
				results["printing_area"] = {'minX': 0.0, 'minY': 0.0}
				results["dimensions"] = {'width':len(image), 'depth':len(image[0]) , 'height': photon_header.height_mm}
				

			return PhotonFile(
				filename=path.name,
				bed_size_mm=(
					round(photon_header.bed_size_x_mm, 4),
					round(photon_header.bed_size_y_mm, 4),
					round(photon_header.bed_size_z_mm, 4),
				),
				height_mm=photon_header.height_mm,
				layer_height_mm=photon_header.layer_height_mm,
				layer_count=photon_header.layer_count,
				resolution=(photon_header.resolution_x, photon_header.resolution_y),
				print_time_secs=photon_header.print_time,
				volume=photon_param.volume_ml,
				end_byte_offset_by_layer=end_byte_offset_by_layer,
				slicer_version=".".join(
					[
						str(photon_slicer.version_release),
						str(photon_slicer.version_major),
						str(photon_slicer.version_minor),
						str(photon_slicer.version_patch),
					]
				),
				printer_name=printer_name,
				printing_area = results["printing_area"],
				dimensions = results["dimensions"],
			)

	@classmethod
	def read_dict(self, path: pathlib.Path, metadata: dict) -> "PhotonFile":
		with open(str(path), "rb") as file:
			photon_header = PhotonHeader.unpack(file.read(PhotonHeader.get_size()))
			
			file.seek(photon_header.param_offset)
			photon_param = PhotonParam.unpack(file.read(PhotonParam.get_size()))

			file.seek(photon_header.slicer_offset)
			photon_slicer = PhotonSlicer.unpack(file.read(PhotonSlicer.get_size()))

			end_byte_offset_by_layer = []
			for layer in range(0, photon_header.layer_count):
				file.seek(
					photon_header.layer_defs_offset + layer * PhotonLayerDef.get_size()
				)
				layer_def = PhotonLayerDef.unpack(file.read(PhotonLayerDef.get_size()))
				end_byte_offset_by_layer.append(
					layer_def.image_offset + layer_def.image_length
				)
				
			return PhotonFile(
					filename=path.name,
					bed_size_mm=(
						round(photon_header.bed_size_x_mm, 4),
						round(photon_header.bed_size_y_mm, 4),
						round(photon_header.bed_size_z_mm, 4),
					),
					height_mm = photon_header.height_mm,
					layer_height_mm = metadata["layer_height_mm"],
					layer_count = metadata["layer_count"],
					resolution = (photon_header.resolution_x, photon_header.resolution_y),
					print_time_secs = metadata["estimatedPrintTime"],
					volume = metadata["filament"]["tool0"]["volume"],
					end_byte_offset_by_layer = end_byte_offset_by_layer,
					slicer_version=".".join(
						[
							str(photon_slicer.version_release),
							str(photon_slicer.version_major),
							str(photon_slicer.version_minor),
							str(photon_slicer.version_patch),
						]
					),
					printer_name = metadata["printer_name"],
					printing_area = metadata["printing_area"],
					dimensions = metadata["dimensions"],
				)

	@classmethod
	def read_preview(cls, path: pathlib.Path) -> png.Image:
		with open(str(path), "rb") as file:
			photon_header = PhotonHeader.unpack(file.read(PhotonHeader.get_size()))

			file.seek(photon_header.high_res_preview_offset)
			preview = PhotonPreview.unpack(file.read(PhotonPreview.get_size()))

			file.seek(preview.image_offset)
			data = file.read(preview.image_length)

			return _read_image(preview.resolution_x, preview.resolution_y, data)
