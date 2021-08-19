import pathlib
import struct, os
from dataclasses import dataclass
from typing import List
from typing import Mapping, Set, Type, Tuple
import numpy as np

import png
from typedstruct import LittleEndianStruct, StructType

from . import SlicedModelFile
from .rle import *

@dataclass(frozen=True)
class PwmsFileMark(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
	version: int = StructType.uint32()
	areaNum: int = StructType.uint32()
	header_offset: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	preview_offset: int = StructType.uint32()
	unknown_02: int = StructType.uint32()
	layer_defs_offset: int = StructType.uint32()
	unknown_03: int = StructType.uint32()
	layer_img_offset: int = StructType.uint32()
	
@dataclass(frozen=True)
class PwmsHeaderMark(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
	length: int = StructType.uint32()  # 04: Always 0x01

@dataclass(frozen=True)
class PwmsHeader(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
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
class PwmsPreviewMark(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
	image_length: int = StructType.uint32()

@dataclass(frozen=True)
class PwmsPreview(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
	image_length: int = StructType.uint32()
	resolution_x: int = StructType.uint32()
	unknown_01: int = StructType.uint32()
	resolution_y: int = StructType.uint32()

@dataclass(frozen=True)
class PwmsLayerMark(LittleEndianStruct):
	mark1: str = StructType.char()
	mark2: str = StructType.char()
	mark3: str = StructType.char()
	mark4: str = StructType.char()
	mark5: str = StructType.char()
	mark6: str = StructType.char()
	mark7: str = StructType.char()
	mark8: str = StructType.char()
	mark9: str = StructType.char()
	mark10: str = StructType.char()
	mark11: str = StructType.char()
	mark12: str = StructType.char()
	image_offset: int = StructType.uint32()
	layer_count: int = StructType.uint32()  # 04: Always 0x01

@dataclass(frozen=True)
class PwmsLayerDef(LittleEndianStruct):
	image_offset: int = StructType.uint32()
	image_length: int = StructType.uint32()
	lift_height: float = StructType.float32()
	lift_speed: float = StructType.float32()
	layer_exposure: float = StructType.float32()
	layer_height_mm: float = StructType.float32()

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
	
def _read_rle4image(width: int, height: int, antialias: int, data: bytes) -> png.Image:
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data):
		grey = struct.unpack_from("<B", data, i)[0]
		color = 0
		nr = grey & 0xf  # turn highest bit of
		L = grey >> 4  # only read 1st bit
		repeat = 1
		if L == 0x0:
			color = 0x00
			repeat = (nr*256) + struct.unpack_from("<B", data, i+1)[0]
			i += 1
		elif L == 0xf:
			color = 0xff - 1
			repeat = (nr*256) + struct.unpack_from("<B", data, i+1)[0]
			i += 1
		else:
			color = L << 4 | L
			color &= antialias
		i+=1

		while repeat > 0:
			array[-1] += [color]
			repeat -= 1

			x += 1
			if x == width:
				x = 0
				array.append([])

	array.pop()
	return png.from_array(array, "L"), array
	
def _read_layer(width: int, height: int, antialias: int, layernum:int, data: bytes) -> png.Image:	
	return read_rle4image(width, height, antialias, data)

def _read_layer_array(width: int, height: int, antialias: int, layernum:int, data: bytes):
	return read_rle4array(width, height, antialias, data)
	
def get_printarea(resolution,header,image, height):
	resolutionX = header.resolution_x
	resolutionY = header.resolution_y
	bed_size_x_mm = header.resolution_x*header.pixel_size/1000.0
	#PixelSize = (header.bed_size_x_mm*1000)/resolutionX
	PixelSize = header.pixel_size
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
	results = {}
	results["printing_area"] = {"minX":minX, "maxX":maxX, "minY":minY,"maxY":maxY}
	results["dimensions"] = {"width":width, "depth":depth, "height":float(height)}
	return results

	
EXTENSION_TO_BED_SIZE: Mapping[str, Tuple[str, float, float, float]] = {
	".pws": ("Anycubic Photon S", 68.04, 120.96, 165),
	".pw0": ("Anycubic Photon Zero", 55.44, 98.64, 150),
	".pwmo": ("Anycubic Photon Mono", 68.04, 120.96, 165),
	".pwms": ("Anycubic Photon Mono SE", 78, 130, 160),
	".pwmx": ("Anycubic Photon Mono X", 120, 192, 245),
}

def _get_printer_info(name):
	#file_ext = name.suffix
	(_, file_ext) = os.path.splitext(name)
	printer_info = EXTENSION_TO_BED_SIZE.get(file_ext.lower())

	assert printer_info is not None
	return printer_info

def _calc_print_time(header, layermark):
	"""
	Calculate print time using info from header and layercount
	Simplistic calculation since it doesn't account for the
	per layer override
	"""
	light_on_time = header.layer_exposure
	light_off_time = header.layer_off_time
	lift_height = header.lift_height
	lift_speed = header.lift_speed
	retract_speed = header.retract_speed
	retract_height = 0
	total_layers = layermark.layer_count
	bottom_light_on_time = header.bottom_exposure
	bottom_layers = header.bottom_count
	
	total_sec = light_on_time+light_off_time
	total_sec = total_sec*total_layers-bottom_layers
	bottom_sec = (bottom_light_on_time+light_off_time)*bottom_layers
	
	lift_time = lift_height/lift_speed
	lift_time = lift_time*total_layers
	
	retract_time = (lift_height + retract_height*2) / retract_speed
	retract_time = retract_time*total_layers
	
	return bottom_sec+total_sec+lift_time+retract_time

@dataclass(frozen=True)
class PwmsFile(SlicedModelFile):
	@classmethod
	def read(self, path: pathlib.Path) -> "PwmsFile":
		with open(str(path), "rb") as file:
			pwms_filemark = PwmsFileMark.unpack(file.read(PwmsFileMark.get_size()))
			
			file.seek(pwms_filemark.header_offset)
			pwms_header = PwmsHeader.unpack(file.read(PwmsHeader.get_size()))
			
			file.seek(pwms_filemark.layer_defs_offset)
			pwms_layermark = PwmsLayerMark.unpack(file.read(PwmsLayerMark.get_size()))
			
			printer_info = _get_printer_info(path.name)
			
			height_mm = pwms_header.layer_height_mm*pwms_layermark.layer_count
			
			end_byte_offset_by_layer = []
			for layer in range(0, pwms_layermark.layer_count):
				file.seek(
					pwms_filemark.layer_defs_offset + PwmsLayerMark.get_size() + layer * PwmsLayerDef.get_size()
				)
				layer_def = PwmsLayerDef.unpack(file.read(PwmsLayerDef.get_size()))
				end_byte_offset_by_layer.append(
					layer_def.image_offset + layer_def.image_length
				)
			print_time = _calc_print_time(pwms_header, pwms_layermark)
			
			file.seek(pwms_filemark.layer_defs_offset + PwmsLayerMark.get_size() +  0 * PwmsLayerDef.get_size())
			first_layer = PwmsLayerDef.unpack(file.read(PwmsLayerDef.get_size()))
			
			file.seek(first_layer.image_offset)
			data = file.read(first_layer.image_length)
			results = {}
			image = _read_layer_array(
				pwms_header.resolution_x,
				pwms_header.resolution_y,
				pwms_header.anti_alias_level,
				0,
				data)
			#try:
			imlayer = np.array(image)
			results = get_printarea(imlayer.shape,pwms_header,imlayer,height_mm)
			#except:
			#	results = {}
			#	results["printing_area"] = {'minX': 0.0, 'minY': 0.0}
			#	results["dimensions"] = {
			#		'width':len(image),
			#		'depth':len(image[0]),
			#		'height': pwms_header.layer_height_mm*pwms_layermark.layer_count}
			

			return PwmsFile(
				filename=path.name,
				bed_size_mm=(
					round(pwms_header.resolution_x*pwms_header.pixel_size/1000.0, 4),
					round(pwms_header.resolution_y*pwms_header.pixel_size/1000.0, 4),
					printer_info[3],
				),
				height_mm=round(pwms_header.layer_height_mm*pwms_layermark.layer_count, 4),
				layer_height_mm=pwms_header.layer_height_mm,
				layer_count=pwms_layermark.layer_count,
				resolution=(pwms_header.resolution_x, pwms_header.resolution_y),
				print_time_secs=_calc_print_time(pwms_header, pwms_layermark), # will have to calculate from file info
				volume=pwms_header.volume_ml,
				end_byte_offset_by_layer=end_byte_offset_by_layer,
				slicer_version="1.8.0.0",
				printer_name=printer_info[0],# Use filename ending to determine printer name
				printing_area = results["printing_area"],
				dimensions = results["dimensions"],
			)

	@classmethod
	def read_preview(cls, path: pathlib.Path) -> png.Image:
		with open(str(path), "rb") as file:
			pwms_filemark = PwmsFileMark.unpack(file.read(PwmsFileMark.get_size()))
			file.seek(pwms_filemark.preview_offset)
			pwms_preview = PwmsPreview.unpack(file.read(PwmsPreview.get_size()))
			# image offset is PWSpreview offset + pwmspreview.getsize()

			file.seek(pwms_header.high_res_preview_offset)
			preview = PwmsPreview.unpack(file.read(PwmsPreview.get_size()))

			file.seek(preview.image_offset)
			data = file.read(preview.image_length)

			return _read_image(preview.resolution_x, preview.resolution_y, data)
