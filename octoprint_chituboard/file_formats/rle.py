import numpy as np
import png, struct

REPEAT_RGB15_MASK: int = 1 << 5

def read_image(width: int, height: int, data: bytes) -> png.Image:
	""" 
	Decodes a RLE byte array from PhotonFile object to a pygame surface.
	Based on https://github.com/Reonarudo/pcb2photon/issues/2
	Encoding scheme:
	The color (R,G,B) of a pixel spans 2 bytes (little endian) and each 
	color component is 5 bits: RRRRR GGG GG X BBBBB
	If the X bit is set, then the next 2 bytes (little endian) masked
	with 0xFFF represents how many more times to repeat that pixel.
	"""
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data):
		# Combine 2 bytes Little Endian so we get RRRRR GGG GG X BBBBB (and advance read byte counter)
		color16 = int(struct.unpack_from("<H", data, i)[0])
		i += 2
		repeat = 1
		if color16 & REPEAT_RGB15_MASK:
			repeat += int(struct.unpack_from("<H", data, i)[0]) & 0xFFF
			i += 2
			
		# Retrieve color components and make pygame color tuple
		(r, g, b) = (
			(color16 >> 0) & 0x1F,
			(color16 >> 6) & 0x1F,
			(color16 >> 11) & 0x1F,
		)

		# If the X bit is set, then the next 2 bytes (little endian) 
		# masked with 0xFFF represents how many more times to repeat that pixel.
		while repeat > 0:
			array[-1] += [r, g, b]
			repeat -= 1

			x += 1
			if x == width:
				x = 0
				array.append([])

	array.pop()

	return png.from_array(array, "RGB;5")

def read_rle1image(width: int, height: int, data: bytes) -> png.Image:
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data) and len(array) < height+1:
		grey = struct.unpack_from("<B", data, i)[0]
		i += 1
		nr = grey & ~(1 << 7)  # turn highest bit of
		L = grey >> 7  # only read 1st bit
		repeat = 1
		if grey & ~(1 << 7):
			repeat = nr
	
		while repeat > 0:
			array[-1] += [L]
			repeat -= 1
	
			x += 1
			if x == width:
				x = 0
				array.append([])
	
	array.pop()
	return png.from_array(array, "L;1")
	
def read_rle4image(width: int, height: int, antialias: int, data: bytes) -> png.Image:
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
	return png.from_array(array, "L")

def read_rle7image(width: int, height: int, data: bytes) -> png.Image:
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data):
		grey = struct.unpack_from("<B", data, i)[0]
		# From each byte retrieve 
		# bit 7(MSB) (highest bit)  single unique pixel(0) or run(1)
		# bits 6:0(LSB) (lowest 7 bits) number of pixels of that color
		# If a run is present, its length is encoded in the following 1-4 bytes.
		code = grey
		repeat = 1
		if (grey & 0x80) == 0x80:
			# Its a run
			code = code & 0x7f# value of pixel 0-127
			i+=1
			# get the run length
			rlen = struct.unpack_from("<B", data, i)[0]
			if (rlen&0x80) == 0:
				# 7 bit run length
				repeat = rlen
				#print(i, repeat,type(repeat), L)
			elif (rlen&0xC0) == 0x80:
				# 14 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat = rlen&0x3f
				repeat = repeat << 8 | repeat2
				#print(i, repeat,type(repeat), L)
				i+=1
			elif (rlen&0xE0) == 0xC0:
				# 21 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat3 = struct.unpack_from("<B", data, i+2)[0]
				repeat = rlen&0x1F
				repeat = repeat << 8 | repeat2
				repeat = repeat << 8 | repeat3
				i += 2
			elif (rlen&0xF0) == 0xE0:
				# 28 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat3 = struct.unpack_from("<B", data, i+2)[0]
				repeat4 = struct.unpack_from("<B", data, i+3)[0]
				repeat = rlen&0xf
				repeat = repeat << 8 | repeat2
				repeat = repeat << 8 | repeat3
				repeat = repeat << 8 | repeat4
				i += 3
			else:
				return png.from_array(array, "L"), array

		# Bit extend from 7-bit to 8-bit greymap
		if (code != 0):
			code = ((code << 1) | 1)
			
		while repeat > 0:# and len(array) < height+1:
			array[-1] += [code]
			repeat -= 1

			x += 1
			if x == width:
				x = 0
				array.append([])
		i+=1
			
	array.pop()
	return png.from_array(array[0:-1], "L")


def read_rle1array(width: int, height: int, data: bytes):
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data) and len(array) < height+1:
		grey = struct.unpack_from("<B", data, i)[0]
		i += 1
		nr = grey & ~(1 << 7)  # turn highest bit of
		L = grey >> 7  # only read 1st bit
		repeat = 1
		if grey & ~(1 << 7):
			repeat = nr
	
		while repeat > 0:
			array[-1] += [L]
			repeat -= 1
	
			x += 1
			if x == width:
				x = 0
				array.append([])
	
	array.pop()
	return array
	
def read_rle4array(width: int, height: int, antialias: int, data: bytes):
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
	return array

def read_rle7array(width: int, height: int, data: bytes):
	array: List[List[int]] = [[]]

	(i, x) = (0, 0)
	while i < len(data):
		grey = struct.unpack_from("<B", data, i)[0]
		# From each byte retrieve 
		# bit 7(MSB) (highest bit)  single unique pixel(0) or run(1)
		# bits 6:0(LSB) (lowest 7 bits) number of pixels of that color
		# If a run is present, its length is encoded in the following 1-4 bytes.
		code = grey
		repeat = 1
		if (grey & 0x80) == 0x80:
			# Its a run
			code = code & 0x7f# value of pixel 0-127
			i+=1
			# get the run length
			rlen = struct.unpack_from("<B", data, i)[0]
			if (rlen&0x80) == 0:
				# 7 bit run length
				repeat = rlen
				#print(i, repeat,type(repeat), L)
			elif (rlen&0xC0) == 0x80:
				# 14 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat = rlen&0x3f
				repeat = repeat << 8 | repeat2
				#print(i, repeat,type(repeat), L)
				i+=1
			elif (rlen&0xE0) == 0xC0:
				# 21 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat3 = struct.unpack_from("<B", data, i+2)[0]
				repeat = rlen&0x1F
				repeat = repeat << 8 | repeat2
				repeat = repeat << 8 | repeat3
				i += 2
			elif (rlen&0xF0) == 0xE0:
				# 28 bit run length
				repeat2 = struct.unpack_from("<B", data, i+1)[0]
				repeat3 = struct.unpack_from("<B", data, i+2)[0]
				repeat4 = struct.unpack_from("<B", data, i+3)[0]
				repeat = rlen&0xf
				repeat = repeat << 8 | repeat2
				repeat = repeat << 8 | repeat3
				repeat = repeat << 8 | repeat4
				i += 3
			else:
				return png.from_array(array, "L"), array

		# Bit extend from 7-bit to 8-bit greymap
		if (code != 0):
			code = ((code << 1) | 1)
			
		while repeat > 0:# and len(array) < height+1:
			array[-1] += [code]
			repeat -= 1

			x += 1
			if x == width:
				x = 0
				array.append([])
		i+=1
			
	array.pop()
	return array
