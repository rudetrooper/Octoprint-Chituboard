# coding=utf-8

import os, sys, glob
import re

from past.builtins import basestring, long
from octoprint.events import Events, eventManager
from octoprint.filemanager import FileDestinations, NoSuchStorage, valid_file_type, full_extension_tree
from octoprint.printer.standard import Printer
from octoprint.util import comm as comm
from octoprint.util import is_hidden_path, to_unicode
from octoprint.util import (
    CountedEvent,
    PrependableQueue,
    RepeatedTimer,
    ResettableTimer,
    TypeAlreadyInQueue,
    TypedQueue,
    bom_aware_open,
    chunks,
    filter_non_ascii,
    filter_non_utf8,
    get_exception_string,
    monotonic_time,
    sanitize_ascii,
    to_unicode,
)
from pathlib import Path
import quopri
import logging
from .file_formats.utils import get_file_format	

# ~ from octoprint.settings import settings

#################################################################################################
#                                   Sla printer class                                           #
#################################################################################################


""" 
TODO:
-bin to sd upload enable
-try to use sd upload
-block normal printing

-sd upload file transfer karpern and after settings decide whether serial upload / udp upload or move to flash image
(can't flash image be the same as an upload directory? )

-handle file handling as sd operations
-handle normal printing as printing from sd card

infos:
-webinterface sd upload action Location: http://192.168.178.67/api/files/sdcard/cfffp_~1.gco
	- uploads the file and automatically triggers an upload to the sd card
	- Deactivate autoprint

	octoprint\printer\standard.py:
		plugin_manager().get_hooks("octoprint.printer.sdcardupload")

	octoprint\server\api\files.py: (line 226)
		@api.route("/files/<string:target>", methods=["POST"]) #handles sd upload, select and starts stream and print

Scenario 1 : pi as flashdrive:

upload directory = mounted image / uploaddir separate from the image
normal serial communication

Scenario 2 : pi only connected via uart separate flshdrive on the printer:

-adaptation of the upload process for bin files
-no streaming and printing during the upload

"""


class Sla_printer(Printer):

	def __init__(self, fileManager, analysisQueue, printerProfileManager):
		self._logger = logging.getLogger(__name__)
		self._logger_job = logging.getLogger("{}.job".format(__name__))
		self._analysisQueue = analysisQueue
		self._fileManager = fileManager
		self._printerProfileManager = printerProfileManager
		self._sliced_model_file = None

		self.fileType = None
		self._logger.info("init Sla_printer object for global printer object")
		Printer.__init__(self, fileManager, analysisQueue, printerProfileManager)

	def select_file(self, path, sd, printAfterSelect=False, user=None, pos=None, *args, **kwargs):
		"""
		check if comm instance with printer is busy or streaming
		check if job is valid
		origin is file destinations.local but convert to sd print
		parse file path to path on disk
		
		Select file using gcode command via self._comm.selectFile()
		add tags = "source:plugin", "Plugin:Chituboard"
		modify self._updateProgressData
		modify s
		"""
		printTime = None
		if self._comm is None or (self._comm.isBusy() or self._comm.isStreaming()):
			self._logger.info("Cannot load file: printer not connected or currently busy")
			return
			
		origin = FileDestinations.SDCARD if sd else FileDestinations.LOCAL
		self.fileType = self.get_fileType(path)
		if sd:
			path_on_disk = "/" + path
			path_in_storage = path
			file_format = get_file_format("/home/pi/.octoprint/uploads/resin"+path_on_disk)
			sliced_model_file = file_format.read(Path("/home/pi/.octoprint/uploads/resin"+path_on_disk))
			printTime = sliced_model_file.print_time_secs
			self._logger.debug("print time: ", printTime)
			
		else:
			path_on_disk = self._fileManager.path_on_disk(origin, path)
			file_format = get_file_format(path_on_disk)
			try:
				fileData = self._fileManager.get_metadata(
						origin,
						path_on_disk,
					)
				
				sliced_model_file = file_format.read_dict(Path(path_on_disk),fileData["analysis"])
				self._logger.info("Metadata %s" % str(fileData))
			except Exception as inst:
				self._logger.debug("yaml load output failed, analysis type:", inst)
				sliced_model_file = file_format.read(Path(path_on_disk))	
			# ~ file_format = get_file_format(path_on_disk)
			# generate sliced_model_file by retrieving file metadata
			# add classmethod to create object using metadata dict
			# compute end_byte_offset_by_layer or layer table in at this time
			# add layer table and print params as optional dicts
			# ~ sliced_model_file = file_format.read(Path(path_on_disk))
			printTime = sliced_model_file.print_time_secs
			# ~ self._sliced_model_file = sliced_model_file
			self._logger.info("print time: ", printTime)
			self._logger.info("Path: %s" % path_on_disk)
			path_in_storage = self._fileManager.path_in_storage(origin, path_on_disk)
			path_on_disk = os.path.split(self._fileManager.path_on_disk(origin, path))[-1]
		self._sliced_model_file = sliced_model_file
		self._logger.debug("Path: %s" % path_on_disk)
		self._logger.debug("Path filename: %s" % os.path.split(path_on_disk)[-1])
		self._logger.debug("Printer state str: ", self._comm.getStateString())
		
		self._printAfterSelect = printAfterSelect
		self._posAfterSelect = pos
		sd = True
		# ~ Printer.select_file(self, path, sd, printAfterSelect, user, pos)
		self._comm.selectFile(
			path_on_disk,
			sd,
			user=user,
			tags=kwargs.get("tags",set()) | {"trigger:printer.commands", "trigger:printer.select_file","source:plugin", "Plugin:Chituboard", "filename:'%s'" % path_on_disk}
		)
		
		self._updateProgressData()#printTime=printTime)
		self._setCurrentZ(None)
		
	def unselect_file(self, *args, **kwargs):
		if self._comm is not None and (self._comm.isBusy() or self._comm.isStreaming()):
			return
			
		self._sliced_model_file = None
		self._comm.unselectFile()
		self._updateProgressData()
		self._setCurrentZ(None)
	
	def jog(self, axes, relative=True, speed=None, *args, **kwargs):
		"""G0 Z{z_dist_mm:.1f} F600 I0
		Finish copying jog method from octoprint.printer.standard.printer
		"""
		if isinstance(axes, basestring):
			# legacy parameter format, there should be an amount as first anonymous positional arguments too
			axis = axes

			if not len(args) >= 1:
				raise ValueError("amount not set")
			amount = args[0]
			if not isinstance(amount, (int, long, float)):
				raise ValueError(
					"amount must be a valid number: {amount}".format(amount=amount)
				)
			axes = {}
			axes[axis] = amount
		if not axes:
			raise ValueError("At least one axis to jog must be provided")
		
		command = "G1 {}".format(
			" ".join(["{}{}".format(axis.upper(), amt) for axis, amt in axes.items()])
		)
		
		if speed is None:
			printer_profile = self._printerProfileManager.get_current_or_default()
			speed = min([printer_profile["axes"][axis]["speed"] for axis in axes])
		
		if speed and not isinstance(speed, bool):
			command += " F{}".format(speed)
		
		if relative:
			commands = ["G91", command, "G90"]
		else:
			commands = ["G90", command]
		
		self.commands(commands, tags=kwargs.get("tags", set()) | {"trigger:printer.jog","source:plugin", "Plugin:Chituboard"})
		
	def home(self, axes, *args, **kwargs):
		"""
		chitusystems resin printers only have one moveable Z axis. G28 Z0
		"""
		if not isinstance(axes, (list, tuple)):
			if isinstance(axes, basestring):
				axes = [axes]
			else:
				raise ValueError(
					"axes is neither a list nor a string: {axes}".format(axes=axes)
					)
					
		self.commands("G28 Z0",tags=kwargs.get("tags", set()) | {"trigger:printer.home","source:plugin", "Plugin:Chituboard"})
			
	def cancel_print(self, user=None, *args, **kwargs):
		"""
		Stop printing tags=source:plugin, Plugin:Chituboard
		Intercepting and rewriting the gcode might be a better approach than overloading _comm.cancelprint
		intercept M400 instruction and send M33
		external_sd = true
		"""
		if self._comm is None:
			return
		if not self._comm.isOperational():
			return
		if not self._comm.isBusy() or self._comm._currentFile is None:
			# we aren't even printing, nothing to cancel...
			return
			
		self.on_comm_print_job_cancelling(user=user)
		with self._comm._jobLock:
			self._comm._changeState(self._comm.STATE_CANCELLING)
			# tell comm layer to cancel - will also trigger our cancelled handler
			# for further processing
			self.commands("M33",tags=kwargs.get("tags", set()) | {"trigger:printer.cancel_print", "source:plugin", "Plugin:Chituboard"})
			# Stuff from comm._cancel_preparation_done()
			self._comm._currentFile.done = True
			self._comm._recordFilePosition()
			self._comm._currentFile.pos = 0
			self._updateProgressData()
			self.on_comm_print_job_cancelled(suppress_script=True, user=user)
			self._comm._changeState(self._comm.STATE_OPERATIONAL)
			self.unselect_file()
			# ~ self._sliced_model_file = None
			# now make sure we actually do something, up until now we only filled up the queue
			self._comm._continue_sending()

	def pause_print(self, user=None, *args, **kwargs):
		"""
		Stop printing tags=source:plugin, Plugin:Chituboard
		Due to delay between when M25 is sent to printer and 
		when the comm layer records the current_File.pos the
		monitoring thread seems to think we just started printing
		due to an external trigger.
		
		There is a 3-5 second delay between when the command is sent
		and the printer actually actually responding.
		
		"""
		if self._comm is None:
			self._logger.info("paused print, _comm is None")
			return
		if self.is_paused():
			self._logger.info("paused print, print already paused")
			return
			
		self._logger.info("paused print, sent M25")
		try:
			with self._comm._jobLock:
				# tell comm layer to start pausing
				self._comm._changeState(self._comm.STATE_PAUSING)
				self.commands(
					"M25 I0",
					force=True,
					cmd_type = "pause_print",
					#on_sent=self._comm._changeState(self._comm.STATE_PAUSED),
					tags=kwargs.get("tags", set()) | {"trigger:printer.commands", "trigger:printer.pause_print", "source:plugin", "Plugin:Chituboard"})
				self._logger.info("paused print, sent M25")
				self.on_comm_print_job_paused(suppress_script=True, user=user)
				# now make sure we actually do something, up until now we only filled up the queue
				# ~ self._comm._continue_sending()
				self._logger.info("paused print, sent M25")
		except Exception:
			self._logger.exception("Error while trying to pause print")
			self._comm._trigger_error(get_exception_string(), "pause_print")	

	def resume_print(self, user=None, *args, **kwargs):
		"""
		Stop printing tags=source:plugin, Plugin:Chituboard
		Intercepting and rewriting the gcode might be a better approach than overloading _comm.cancelprint
		intercept M400 instruction and send M24
		external_sd = true
		"""
		if self._comm is None:
			return
		
		if not self.is_paused():
			return
		try:
			with self._comm._jobLock:
				# tell comm layer to start pausing
				self._comm._changeState(self._comm.STATE_RESUMING)
				self.commands("M24",
					force=True,
					on_sent=self._comm._changeState(self._comm.STATE_PRINTING),
					tags=kwargs.get("tags", set()) | {"trigger:printer.commands", "trigger:printer.resume_print", "source:plugin", "Plugin:Chituboard"})
				# ~ self._comm._changeState(self.STATE_PRINTING)
				self.on_comm_print_job_resumed(suppress_script=True, user=user)
				# now make sure we actually do something, up until now we only filled up the queue
				# ~ self._comm._continue_sending()
				self._logger.info("paused print, sent M25")
		except Exception:
			self._logger.exception("Error while trying to resume print")
			self._comm._trigger_error(get_exception_string(), "resume_print")

	def start_print(self, pos=None, user=None, *args, **kwargs):

		if self.fileType == "gcode": 
			Printer.start_print(self, pos, user)

		elif self.fileType == "sla_bin":
			"""
			Starts the currently loaded print job.
			Only starts if the printer is connected and operational, not currently printing and a printjob is loaded
			"""
			if (
				self._comm is None 
				or not self._comm.isOperational()
				or self._comm.isPrinting()
			):
				
				return

			with self._selectedFileMutex:
				if self._selectedFile is None:
					raise ValueError("No file selected for printing")
					return

			self._fileManager.delete_recovery_data()

			self._lastProgressReport = None
			self._updateProgressData()
			self._setCurrentZ(None)
			cur_file, tags = self.comm_start_print(pos=pos,
			user=user, external_sd=False)
			try:
				with self._comm._jobLock:
					self._comm._consecutive_not_sd_printing = 0

					self._comm._currentFile.start()
					self._comm._changeState(self._comm.STATE_STARTING)
					
					self._comm._callback.on_comm_print_job_started(suppress_script=True, user=user)
					
					# make sure to ignore the "file selected" later on, otherwise we'll reset our progress data
					self._comm._ignore_select = True
					
					self._logger.info(self._comm._currentFile)
					if self._selectedFile is None:
						self._comm.sendCommand(
							"M23 {filename}".format(
								filename=cur_file
							),
							cmd_type = "select_file",
							part_of_job=True,
							tags=tags)
							# ~ tags=tags | {"trigger:comm.start_print",}),
						self._logger.info("selected file")
						self._logger.info("current file pos: ", self._comm._currentFile.pos)
					self._logger.info("current file pos: ", self._comm._currentFile.pos)
					self._logger.info("is active: ", self._comm._active)
					self._logger.info("is starting: {} is printing: {}".format(self._comm.isStarting(), self._comm.isPrinting()))
					
					self._logger.info("starting print")
					self.commands(
						"M6030 '{filename}'".format(
							filename=cur_file
						),
						cmd_type = "start_print",
						# ~ part_of_job=True,
						on_sent=self._comm._changeState(self._comm.STATE_PRINTING),
						tags=tags)
						# ~ | {"trigger:comm.start_print",})
					self._logger.info("start print, send M6030 <filename>", str(user))
										
				# now make sure we actually do something, up until now we only filled up the queue
				self._comm._continue_sending()
				self._logger.info("start print, send M6030 <filename>, continue sending")
			except Exception:
				self._logger.exception("Error while trying to start printing")
				self._comm._trigger_error(get_exception_string(), "start_print")
				
	def comm_start_print(self, pos=None, tags=None, external_sd=False, user=None):
		
		self._comm._heatupWaitStartTime = None if not self._comm._heating else monotonic_time()
		self._comm._heatupWaitTimeLost = 0.0
		self._comm._pauseWaitStartTime = 0
		self._comm._pauseWaitTimeLost = 0.0
		
		self._logger.info("Start Print")
		self._logger.info("self._selectedFile: %s" % self._selectedFile)
		self._logger.info("self._selectedFile: %s" % self._selectedFile["filename"])
		cur_file = self._selectedFile["filename"]
		tags={"trigger:printer.commands", "trigger:printer.start_print", "source:plugin", "Plugin:Chituboard", "filename:'{}'".format(cur_file)}
		if "source:plugin" in tags:
			for tag in tags:
				if tag.startswith("plugin:"):
					self._logger.info(
						"Starting job on behalf of plugin {}".format(tag[7:])
					)
		elif "source:api" in tags:
			self._logger.info("Starting job on behalf of user {}".format(user))
		
		return cur_file, tags	
		
		
	def add_sd_file(self, filename, path, on_success=None, on_failure=None, *args, **kwargs):
		"""
		Todo: add method to properly upload SD files using the UART port.
		Basic outline of sd upload procedure in 
		https://www.improwis.com/projects/sw_PhotonControl/
		https://docs.google.com/document/d/14UBMO0Vhh9Lr0V3xcdetQ2_4UDnjFnho7OnbNxLOs3o/view#
		and photonsters github
		"""
		self.fileType = self.get_fileType(path)

		if self.fileType == "gcode": 
			ret = Printer.add_sd_file(self, filename, path, on_success, on_failure, *args, **kwargs)
		elif self.fileType == "sla_bin":
			on_success()
			print("printjob canceled")
			
	def commands(self, commands, 
		cmd_type=None, 
		part_of_job=False, 
		tags=None, 
		force=False,
		*args, **kwargs):
		"""
		Sends one or more gcode commands to the printer.
		"""
		if self._comm is None:
			return

		if not isinstance(commands, (list, tuple)):
			commands = [commands]

		if tags is None:
			tags = set()
		tags |= {"trigger:printer.commands"}
		
		for command in commands:
			self._comm.sendCommand(command, cmd_type=cmd_type, part_of_job=part_of_job, tags=tags, force=force)
			
	# ~ def on_comm_file_selected(self, full_path, size, sd, user=None):
		# ~ filename = None
		# ~ if full_path is not None:
			# ~ payload = self._payload_for_print_job_event(
				# ~ location=FileDestinations.SDCARD if sd else FileDestinations.LOCAL,
				# ~ print_job_file=full_path,
				# ~ print_job_user=user,
				# ~ action_user=user,
			# ~ )
			# ~ filename = Path(full_path).name
			# ~ eventManager().fire(Events.FILE_SELECTED, payload)
			# ~ self._logger_job.info(
				# ~ "Print job selected - origin: {}, path: {}, owner: {}, user: {}".format(
					# ~ payload.get("origin"),
					# ~ payload.get("path"),
					# ~ payload.get("owner"),
					# ~ payload.get("user"),
				# ~ )
			# ~ )
		# ~ else:
			# ~ eventManager().fire(Events.FILE_DESELECTED)
			# ~ self._logger_job.info(
				# ~ "Print job deselected - user: {}".format(user if user else "n/a")
			# ~ )
		# ~ estimatedprintTime = None
		# ~ if filename is not None:
			# ~ file_format = get_file_format("/home/pi/.octoprint/uploads/resin/"+filename)
			# ~ sliced_model_file = file_format.read(Path("/home/pi/.octoprint/uploads/resin/"+filename))
			# ~ estimatedprintTime = sliced_model_file.print_time_secs
			# ~ self._selectedFile["estimatedPrintTime"] = estimatedprintTime
			
		# ~ self._setJobData(full_path, size, sd, user=user)
		# ~ if self._selectedFile is not None:
			# ~ self._selectedFile["estimatedPrintTime"] = estimatedprintTime
			# ~ self._selectedFile["estimatedPrintTimeType"] = "analysis"
		# ~ self._stateMonitor.set_state(
			# ~ self._dict(
				# ~ text=self.get_state_string(),
				# ~ flags=self._getStateFlags(),
				# ~ error=self.get_error(),
			# ~ )
		# ~ )
		
		# ~ self._create_estimator()
		
		# ~ if self._printAfterSelect:
			# ~ self._printAfterSelect = False
			# ~ self.start_print(pos=self._posAfterSelect, user=user)
	
	def get_fileType(self,path):
		tree = full_extension_tree()["machinecode"]

		for key in tree:
			if valid_file_type(path,type=key):
				#self.fileType = key
				return key

		return None
	
	def get_current_layer(self):
		filepos = self.get_file_position()
		current_layer = "-"
		if filepos:
			filepos = filepos["pos"]
			if filepos == 0:
				current_layer = 1
			else:
				current_layer = (
					self._sliced_model_file.end_byte_offset_by_layer.index(filepos)+ 1
				)
		return current_layer

	def split_path(self, path):
		path = to_unicode(path)
		split = path.split(u"/")
		if len(split) == 1:
			return u"", split[0]
		else:
			return self.join_path(*split[:-1]), split[-1]


REGEX_XYZ0 = re.compile(r"(?P<axis>[XYZ])(?=[XYZ]|\s|$)")
REGEX_XYZE0 = re.compile(r"(?P<axis>[XYZE])(?=[XYZE]|\s|$)")
parse_m4000 = re.compile('B:(\d+)\/(\d+)')
regex_sdPrintingByte = re.compile(r"(?P<current>[0-9]+)/(?P<total>[0-9]+)")
"""Regex matching SD printing status reports.

Groups will be as follows:

  * ``current``: current byte position in file being printed
  * ``total``: total size of file being printed
"""

class gcode_modifier():
	def __init__(self):
		# ~ self._printer = PrinterInterface
		self._logged_replacement = {}
		self._logger = logging.getLogger("octoprint.plugin")
		pass

	def get_gcode_send_modifier(self, comm_instance, phase, cmd, cmd_type, gcode,subcode=None , tags=None, *args, **kwargs):
		if cmd.upper().startswith('M110'): #suppress line reset
			return (None, )
		# ~ elif gcode == "M105":
			# ~ return "M4000", cmd_type
		# ~ elif gcode == "M25" and "trigger:comm.cancel" in tags:
			# ~ return "M33", cmd_type
		else:
			return None
	
	def get_gcode_queuing_modifier(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
		if gcode == "M105" and cmd_type == "temperature_poll":
			return "M4000", cmd_type
		elif gcode == "M25" and "trigger:comm.cancel" in tags:
			return "M33", cmd_type
	
		
