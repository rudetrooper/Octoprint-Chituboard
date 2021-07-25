#!/usr/bin/python
# -*- coding: utf-8 -*-

# import file analysis from mariner
# ~ from file_formats import SlicedModelFile
# ~ from file_formats.ctb import CTBFile
# ~ from file_formats.cbddlp import CBDDLPFile
# ~ from file_formats.fdg import FDGFile

from octoprint.filemanager.analysis import AbstractAnalysisQueue
import pprint
import struct
import yaml, time
import logging

class sla_AnalysisQueue(AbstractAnalysisQueue):
	"""
	A queue to analyze GCODE files. Analysis results are :class:`dict` instances structured as follows:
	
	.. list-table::
	:widths: 25 70
	
	- * **Key**
		* **Description**
	- * ``estimatedPrintTime``
		* Estimated time the file take to print, in seconds
	
	- * ``filament.volume``
		* The used volume in cm³
	
	- * ``printingArea``
		* Bounding box of the printed object in the print volume (minimum and maximum coordinates)
	
	- * ``printingArea.minX``
		* Minimum X coordinate of the printed object
	- * ``printingArea.maxX``
		* Maximum X coordinate of the printed object
	- * ``printingArea.minY``
		* Minimum Y coordinate of the printed object
	- * ``printingArea.maxY``
		* Maximum Y coordinate of the printed object
	- * ``printingArea.minZ``
		* Minimum Z coordinate of the printed object
	- * ``printingArea.maxZ``
		* Maximum Z coordinate of the printed object
	- * ``dimensions``
	
		* Dimensions of the printed object in X, Y, Z
	- * ``dimensions.width``
	
		* Width of the printed model along the X axis, in mm
	- * ``dimensions.depth``
		* Depth of the printed model along the Y axis, in mm
	- * ``dimensions.height``
		* Height of the printed model along the Z axis, in mm
	"""

	def __init__(self, finished_callback):
		AbstractAnalysisQueue.__init__(self, finished_callback)
		
		self._aborted = False
		self._reenqueue = False

			#if self._current.analysis:
			#	return self._current.analysis
		   

	def _do_analysis(self, high_priority=False):
		import sys

		import sarge
		import yaml
		
		if self._current.analysis and all(
			map(
				lambda x: x in self._current.analysis,
				("printingArea", "dimensions", "estimatedPrintTime", "filament"),
			)
		):
			return self._current.analysis
		
		# ~ self._aborted = False
		# ~ high_priority=True
		results = {}
		result = {}
		results = {'analysisPending': True}
		self._current_progress = 2
		self._currentProgress = 2
		self._logger.debug("#########################################")
		self._logger.debug("try analysis")
		self._logger.info(self._current)
		self._logger.debug("#########################################")
		self._logger.info(self._current.type)
		self._logger.info(self._currentProgress)
		self._logger.info("result: ", type(results), results)
		self._logger.info("results: ", results['analysisPending'])
		self._logger.debug("#########################################")
		# ~ self._logger.info(self._current.absolute_path)
		# ~ self._logger.info("#########################################")
		# ~ self._logger.info(self._current.printer_profile)
		# ~ self._logger.info("#########################################")
		# ~ self._logger.info("current Progress: " + self._current)
		self._logger.debug("#########################################")
		self._current_progress = 6
		self._currentProgress = 6
		self._logger.info("result: ", type(result), type(results), results)
		result["estimatedPrintTime"] = 6460
		self._logger.info("result: ", result)
		result["dimensions"] = {'width': 82.62, 'depth': 130.56, 'height': 150}
		self._logger.info("result: ", result)
		result["printingArea"] = {'minX': 5.0,'minY': 5.0, 'minZ': 5.0, 'maxX': 10.0, 'maxY': 10.0, 'maxZ': 10.0}
		result["filament"] = {}
		result["filament"]["tool0"] = {'length':10,'volume':10}
		self._logger.info("estimated print time: " + result["estimatedPrintTime"])
		self._logger.info("#########################################")
		self._logger.info("result: ", result)
		self._current_progress = 100
		return result
		# ~ self._logger.info(result["PrintTime"])
		# ~ self._logger.info(result["magic"])
		# ~ if self._current.analysis and isinstance(self._current.analysis, dict):
			# ~ return dict_merge(result, self._current.analysis)
		# ~ else:
			# ~ return result	

	def _do_abort(self, reenqueue=True):
		self._aborted = True
		self._reenqueue = reenqueue
		
		
# ~ try:
	# ~ command = [
		# ~ sys.executable,
		# ~ "-m",
		# ~ "octoprint",
		# ~ "plugins",
		# ~ "CBD_plugins:slatest",
	# ~ ]
	# ~ command.append(self._current.absolute_path)
	# ~ self._logger.info("Invoking analysis command: {}".format(" ".join(command)))
	# ~ self._aborted = False
	# ~ p = sarge.run(
		# ~ command.append(self._current.absolute_path)

	# ~ self._logger.info("Invoking analysis command: {}".format(" ".join(command)))

	# ~ self._aborted = False
	# ~ p = sarge.run(
		# ~ command, close_fds=CLOSE_FDS, async_=True, stdout=sarge.Capture()
	# ~ )

	# ~ while len(p.commands) == 0:
		# ~ # somewhat ugly... we can't use wait_events because
		# ~ # the events might not be all set if an exception
		# ~ # by sarge is triggered within the async process
		# ~ # thread
		# ~ time.sleep(0.01)

	# ~ # by now we should have a command, let's wait for its
	# ~ # process to have been prepared
	# ~ p.commands[0].process_ready.wait()

	# ~ if not p.commands[0].process:
		# ~ # the process might have been set to None in case of any exception
		# ~ raise RuntimeError(
			# ~ "Error while trying to run command {}".format(" ".join(command))
		# ~ )

	# ~ try:
		# ~ # let's wait for stuff to finish
		# ~ while p.returncode is None:
			# ~ if self._aborted:
				# ~ # oh, we shall abort, let's do so!
				# ~ p.commands[0].terminate()
				# ~ raise AnalysisAborted(reenqueue=self._reenqueue)

			# ~ # else continue
			# ~ p.commands[0].poll()
	# ~ finally:
		# ~ p.close()

	# ~ output = p.stdout.text
	# ~ self._logger.debug("Got output: {!r}".format(output))command, close_fds=CLOSE_FDS, async_=True, stdout=sarge.Capture()
	# ~ )

	# ~ while len(p.commands) == 0:
		# ~ # somewhat ugly... we can't use wait_events because
		# ~ # the events might not be all set if an exception
		# ~ # by sarge is triggered within the async process
		# ~ # thread
		# ~ time.sleep(0.01)

	# ~ # by now we should have a command, let's wait for its
	# ~ # process to have been prepared
	# ~ p.commands[0].process_ready.wait()

	# ~ if not p.commands[0].process:
		# ~ # the process might have been set to None in case of any exception
		# ~ raise RuntimeError(
			# ~ "Error while trying to run command {}".format(" ".join(command))
		# ~ )
	# ~ try:
		# ~ # let's wait for stuff to finish
		# ~ while p.returncode is None:
			# ~ if self._aborted:
				# ~ # oh, we shall abort, let's do so!
				# ~ p.commands[0].terminate()
				# ~ raise AnalysisAborted(reenqueue=self._reenqueue)

			# ~ # else continue
			# ~ p.commands[0].poll()
	# ~ finally:
		# ~ p.close()

	# ~ output = p.stdout.text
	# ~ self._logger.info("Got output: {!r}".format(output))
# ~ except:
	# ~ self._logger.info("Could not open" + self._current)
# ~ finally:

# ~ def _do_analysis(self, high_priority=False):
# ~ self._logger.info("#########################################")
# ~ self._logger.info("try analysis")
# ~ self._logger.info(self._current)
# ~ self._logger.info("#########################################")
# ~ self._logger.info(self._current.type)
# ~ self._logger.info("#########################################")
# ~ self._logger.info(self._current.absolute_path)
# ~ self._logger.info("#########################################")
# ~ self._logger.info(self._current.printer_profile)
# ~ self._logger.info("#########################################")

# ~ sliced_model_file = CTBFile.read(self._current.absolute_path)

# ~ result = dict()

# ~ result["filename"] = sliced_model_file.filename
# ~ result["path"] = sliced_model_file.filename
# ~ result["estimatedPrintTime"] = sliced_model_file.print_time_secs
# ~ result["numberOfLayers"] = sliced_model_file.layer_count
# ~ result["layerHeightMilimeter"] = round(sliced_model_file.layer_height_mm, 4)

# ~ blocksize = 118 #filehead

# ~ with open(self._current.absolute_path, "rb") as f:
	# ~ buffer = f.read(blocksize)
	# ~ f.close()

# ~ result = dict()

# ~ result["magic"] =                         hex(struct.unpack_from('<I', buffer[0:4])[0])
# ~ result["version"] =                       struct.unpack_from('<I', buffer[4:8])[0]
# ~ result["bedXmm"] =                        round(struct.unpack_from('<f', buffer[8:12])[0], 2)    
# ~ result["bedYmm"] =                        round(struct.unpack_from('<f', buffer[12:16])[0], 2)
# ~ result["bedZmm"] =                        round(struct.unpack_from('<f', buffer[16:20])[0], 2)
# ~ result["unknown1"] =                      struct.unpack_from('<I', buffer[20:24])[0]
# ~ result["unknown2"] =                      struct.unpack_from('<I', buffer[24:28])[0]
# ~ result["TotalHeightMilimeter"] =          round(struct.unpack_from('<f', buffer[28:32])[0], 2)
# ~ result["layerHeightMilimeter"] =          round(struct.unpack_from('<f', buffer[32:36])[0], 2)
# ~ result["exposureTimeSeconds"] =           round(struct.unpack_from('<f', buffer[36:40])[0], 2)
# ~ result["exposureBottomTimeSeconds"] =     round(struct.unpack_from('<f', buffer[40:44])[0], 2)
# ~ result["offTimeSeconds"] =                round(struct.unpack_from('<f', buffer[44:48])[0], 2)
# ~ result["bottomLayers"] =                  struct.unpack_from('<I', buffer[48:52])[0]
# ~ result["resolutionX"] =                   struct.unpack_from('<I', buffer[52:56])[0]
# ~ result["resolutionY"] =                   struct.unpack_from('<I', buffer[56:60])[0]
# ~ result["previewOneOffsetAddress"] =       struct.unpack_from('<I', buffer[60:64])[0]
# ~ result["layersDefinitionOffsetAddress"] = struct.unpack_from('<I', buffer[64:68])[0]
# ~ result["numberOfLayers"] =                struct.unpack_from('<I', buffer[68:72])[0]
# ~ result["previewTwoOffsetAddress"] =       struct.unpack_from('<I', buffer[72:76])[0]
# ~ result["printTime"] =                     struct.unpack_from('<I', buffer[76:80])[0]
# ~ result["projector"] =                     struct.unpack_from('<I', buffer[80:84])[0]
# ~ result["PrintParametersOffsetAddress"] =  struct.unpack_from('<I', buffer[84:88])[0]
# ~ result["PrintParametersize"] =            struct.unpack_from('<I', buffer[88:92])[0]
# ~ result["AntiAliasLevel"] =                struct.unpack_from('<I', buffer[92:96])[0]
# ~ result["lightPWM"] =                      struct.unpack_from('<H', buffer[96:98])[0]
# ~ result["BottomlightPWM"] =                struct.unpack_from('<H', buffer[98:100])[0]
# ~ result["EncryptionKey"] =                 struct.unpack_from('<I', buffer[100:104])[0]
# ~ result["SlicerOffset"] =                  struct.unpack_from('<I', buffer[104:108])[0]
# ~ result["SlicerSize"] =                    struct.unpack_from('<I', buffer[108:112])[0]
# ~ #required parameters
# ~ result["estimatedPrintTime"] = result["printTime"]
# ~ result["dimensions"] = {"width": result["bedXmm"], "depth": result["bedYmm"], "height": result["TotalHeightMilimeter"]}
# ~ result["printingArea"] = {"minX": 5.0,"minY": 5.0, "minZ": 5.0, "maxX": 10.0, "maxY": 10.0, "maxZ": 10.0}

# ~ with open(current, "rb") as f:
	# ~ f.seek(result["PrintParametersOffsetAddress"])
	# ~ printparameter = f.read(result["PrintParametersize"])
	# ~ f.close()

# ~ printparam = dict()
# ~ printparam["BottomLiftHeight"] = round(struct.unpack_from('<f', printparameter[0:4])[0],4)
# ~ printparam["BottomLiftSpeed"] =               round(struct.unpack_from('<f', printparameter[4:8])[0],4)
# ~ printparam["LiftHeight"] =                     round(struct.unpack_from('<f', printparameter[8:12])[0],4)
# ~ printparam["LiftSpeed"] =                  round(struct.unpack_from('<f', printparameter[12:16])[0],4)
# ~ printparam["RetractSpeed"] =                      round(struct.unpack_from('<f', printparameter[16:20])[0],4)
# ~ printparam["VolumeM1"] =                       round(struct.unpack_from('<f', printparameter[20:24])[0],2)
# ~ printparam["WeightG"] =                   round(struct.unpack_from('<f', printparameter[24:28])[0],2)
# ~ printparam["CostDollars"] =           round(struct.unpack_from('<f', printparameter[28:32])[0],4)
# ~ printparam["BottomLightOffDelay"] =                 round(struct.unpack_from('<f', printparameter[32:36])[0],4)
# ~ printparam["LightOffDelay"] =                  round(struct.unpack_from('<f', printparameter[36:40])[0],4)
# ~ printparam["BottomLayerCount"] =              struct.unpack_from('<I', printparameter[40:44])[0]
# ~ printparam["MysteriousID"] =                  struct.unpack_from('<I', printparameter[44:48])[0]
# ~ printparam["AntiAliasLevel"] =                struct.unpack_from('<f', printparameter[48:52])[0]
# ~ printparam["SoftwareVersionpatch"] =          struct.unpack_from('<I', printparameter[52:56])[0]
# ~ printparam["SoftwareVersionminor"] =          struct.unpack_from('<B', printparameter[56:60])[0]
# ~ result["filament"] = {"tool0":{"length":10,"voloume":printparam["VolumeM1"]}}
# ~ print("try analysis")
# ~ print(result)
# ~ self._logger.info(result["estimatedPrintTime"])

# ~ return result
# ~ else:
# ~ result = None
# ~ return result
