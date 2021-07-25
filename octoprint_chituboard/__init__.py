
#!/usr/bin/python
# coding=utf-8


import os, sys
import logging
import re

# ~ from .chitu_comm import chitu_comm
# ~ from .flash_drive_emu import flash_drive_emu
from .sla_analyser import sla_AnalysisQueue
from .sla_estimator import SLAPrintTimeEstimator
from .sla_printer import Sla_printer, gcode_modifier
from .sla_ui import *

import octoprint.plugin
import octoprint.util

from octoprint.settings import settings

import octoprint.filemanager
import octoprint.filemanager.util
from octoprint.filemanager import ContentTypeMapping
from octoprint.printer.estimation import PrintTimeEstimator

REGEX_XYZ0 = re.compile(r"(?P<axis>[XYZ])(?=[XYZ]|\s|$)")
REGEX_XYZE0 = re.compile(r"(?P<axis>[XYZE])(?=[XYZE]|\s|$)")
parse_m4000 = re.compile('B:(\d+)\/(\d+)')
regex_sdPrintingByte = re.compile(r"(?P<current>[0-9]+)/(?P<total>[0-9]+)")
"""Regex matching SD printing status reports.

Groups will be as follows:

  * ``current``: current byte position in file being printed
  * ``total``: total size of file being printed
"""

class Chituboard(   octoprint.plugin.SettingsPlugin,
					octoprint.plugin.SimpleApiPlugin,
					octoprint.plugin.AssetPlugin,
					octoprint.plugin.TemplatePlugin,
					octoprint.plugin.StartupPlugin,
					octoprint.plugin.EventHandlerPlugin,
					octoprint.plugin.ShutdownPlugin
					):

	firmware_version = "V4.13"
	finished_print = None
	
	def __init__(self, **kwargs):
		super(Chituboard, self).__init__(**kwargs)
		self._initialized = False
		self.gcode_modifier = gcode_modifier()
		self._logged_replacement = {}
		self._logger = logging.getLogger("octoprint.plugins.Chituboard")
		
	def _initialize(self):
		if self._initialized == True:
			return
		self._logger.info("Plugin active, working around broken 'CBD make it' firmware")

		self._initialized = True
		
		# ~ self.hideTempTab = self._settings.get_boolean(["hideTempTab"])
		# ~ self.hideControlTab = self._settings.get_boolean(["hideControlTab"])
		# ~ self.hideGCodeTab = self._settings.get_boolean(["hideGCodeTab"])
		# ~ setTabs(self)
		self._settings.global_set(["serial", "helloCommand"], self._settings.get(["helloCommand"]))
		# ~ self._settings.global_set(["serial", "pausingCommands"], self._settings.get(["pauseCommand"]))
		self._settings.global_set(["serial", "disconnectOnErrors"], False)
		self._settings.global_set(["serial", "sdAlwaysAvailable"], False)
		self._settings.global_set(["serial", "capabilities", "autoreport_sdstatus"], False)
		self._settings.global_set(["serial", "capabilities", "autoreport_temp"], False)
		self._settings.global_set(["serial", "firmwareDetection"], False)
		self._settings.global_set(["serial", "baudrate"], self._settings.get(["defaultBaudRate"]))
		self._settings.global_set(["serial", "exclusive"], False)
		self._settings.global_set(["serial", "unknownCommandsNeedAck"], True)
		self._logger.info("Octoprint_SLA-plugin startup: load settings finished")
		#add raspberry uart to the avaliable ports
		# ~ ports = self._settings.global_get(["serial", "additionalPorts"])
		# ~ if "/dev/ttyS0" not in ports:
			# ~ ports.append("/dev/ttyS0")
		# ~ self._settings.global_set(["serial", "additionalPorts"], ports)


	##############################################
	#		allowed file extesions part		 #
	##############################################
	
	@property
	def allowed(self):
		if self._settings is None:
			#self._logger.info("settings is none: %s " % self._settings.get(["allowedExten"]))
			return str("cbddlp, photon, ctb, fdg, pws, pw0, pwms, pwmx")
		else:
			#self._logger.info("add Extensions: %s " % self._settings.get(["allowedExten"]))
			return str(self._settings.get(["allowedExten"]))
	

	def get_extension_tree(self, *args, **kwargs):
		self._logger.debug("add Extensions: %s " % self.allowed)
		return dict(machinecode=dict(sla_bin=ContentTypeMapping(self.allowed.replace(" ", "").split(","), "application/octet-stream")))


	##############################################
	#				change ui				   #
	##############################################

	def get_template_configs(self):
		# Todo: create modelviewer similar to octoprint Gcode viewer.
		return [dict(type="tab", name="SLA-control", replaces="control" , div="control" ,template="sla_plugin_tab.jinja2", custom_bindings=False)]
				# ~ dict(type="tab", name="Modelview", template="Modeleditor.jinja2" , custom_bindings=False)
				# ~ dict(type="settings", template="sla_plugin_settings.jinja2", custom_bindings=False)
	

	def analysis_commands(self,*args, **kwargs):
		import click
		@click.command(name="sla_analysis")
		@click.argument("name", default=None)
		def sla_analysis(name):
			"""
			Analyze files created in chitubox, photon workshop and Lychee.
			Will be used in analysis queue once I read documentation for sarge
			"""
			# ~ click.echo("{} {}!".format(greeting, name))
			import time, yaml
			from pathlib import Path
			from octoprint.util import monotonic_time
			start_time = monotonic_time()
			from .file_formats.utils import get_file_format
			if os.path.isabs(name):
				# ~ click.echo("{}!".format(test))
				file_format = get_file_format(name)
				sliced_model_file = file_format.read(Path(name))
				click.echo("DONE:{}s".format(monotonic_time() - start_time))
				click.echo("RESULTS:")
				result = {
					"filename": sliced_model_file.filename,
					"path": name,
					"bed_size_mm": list(sliced_model_file.bed_size_mm),
					"height_mm": round(sliced_model_file.height_mm, 4),
					"layer_count": sliced_model_file.layer_count,
					"layer_height_mm": round(sliced_model_file.layer_height_mm, 4),
					"resolution": list(sliced_model_file.resolution),
					"print_time_secs": sliced_model_file.print_time_secs,
					"total_time": sliced_model_file.print_time_secs/60,
					# ~ "end byte offset by layer": sliced_model_file.end_byte_offset_by_layer,
					"printer name": sliced_model_file.printer_name
					}
				click.echo(yaml.safe_dump(result,default_flow_style=False, indent=2, allow_unicode=True))
			else:
				click.echo("ERROR: not absolute path, nothing to analyse")
				sys.exit(0)	

		return [sla_analysis]

	##############################################
	#				  Settings				  #
	##############################################

	def get_settings_defaults(self):
		return dict(
			allowedExten = 'cbddlp, photon, ctb, fdg, pws, pw0, pwms, pwmx',
			defaultBaudRate = 115200,
			additionalPorts = "/dev/ttyS0",
			workAsFlashDrive = True, #false printer use separate flash drive
			flashFirstRun = False,
			flashDriveImageSize = 4,#GB
			chitu_comm = False,
			hideTempTab = False,
			hideControlTab = False,
			hideGCodeTab = False,
			useHeater = False,
			heaterTemp = 30,# C
			heaterTime = 20,#min
			resinGauge = False,
			enableLight = False, #ir cam light
			mainpowerSwitch = None,#net/gpio
			photonFileEditor = False,
			tempSensorPrinter = None,#1wire/ntc
			tempSensorBed = None,#1wire/ntc
			helloCommand = "M4002",
			pauseCommand = "M25")
	
	

	def on_after_startup(self):
		self._logger.info("Octoprint-Chituboard plugin startup")
		# ~ self._initialize()

	##############################################
	#				UDP Upload				  #
	##############################################
	# use code from https://github.com/MarcoAntonini/chitubox-file-receiver/blob/master/chitubox-file-receiver.py
		#if self._settings.get(["chitu_comm"]):
			#TODO: check if we can write to watched folder
			#self.Chitu_comm = chitu_comm(self)
			#self.Chitu_comm.start_listen_reqest()
			#self._logger.info("chitubox udp reciver enabeled")


		#more at octoprint/settings.py
	#def on_shutdown(self):
		#self.Chitu_comm.shutdownService()

	##############################################
	#			   File analysis				#
	##############################################
	# ~ def get_sla_analysis_factory(*args, **kwargs):
		# ~ return dict(sla_bin=sla_AnalysisQueue)

	##############################################
	#			   Estimatorfactory			 #
	##############################################
	# ~ def get_sla_estimator_factory(*args, **kwargs):
		# ~ return SLAPrintTimeEstimator


	##############################################
	#			   Printerfactory			   #
	##############################################
	def get_sla_printer_factory(self,components):
		"""
		Replace octoprint standard.py with new version
		"""
		self.sla_printer = Sla_printer(components["file_manager"],components["analysis_queue"],components["printer_profile_manager"])
		return self.sla_printer
		
	##############################################
	#               Plugin Update                #
	##############################################

	def get_update_information(self):
	
		return {
			"Chituboard": {
			"displayName": "Chituboard",
			"displayVersion": self._plugin_version,
			"type": "github_commit",
			"user": "rudetrooper",
			"repo": "Octoprint-Chituboard",
			"current": self._plugin_version,
			"pip": "https://github.com/rudetrooper/Octoprint-Chituboard/archive/{target_version}.zip",
			}
			}
		
	REGEX_XYZ0 = re.compile(r"(?P<axis>[XYZ])(?=[XYZ]|\s|$)")
	REGEX_XYZE0 = re.compile(r"(?P<axis>[XYZE])(?=[XYZE]|\s|$)")
	fix_M114 = re.compile(r"C: ")
	parse_m4000 = re.compile('B:(\d+)\/(\d+)')
	regex_sdPrintingByte = re.compile(r"(?P<current>[0-9]+)/(?P<total>[0-9]+)")
	"""Regex matching SD printing status reports.

	Groups will be as follows:

	  * ``current``: current byte position in file being printed
	  * ``total``: total size of file being printed
	"""
		
	def get_gcode_receive_modifier(self, comm_instance, line, *args, **kwargs):
		line = self._rewrite_wait_to_busy(line)
		line = self._rewrite_identifier(line)
		line, end_msg = self._rewrite_print_finished(line)
		line = self._rewrite_start(line)
		line = self._rewrite_m4000_response(line)
		line = self._rewrite_m114_response(line)
		line = self._rewrite_error(line)
		if end_msg == True:
			try:
				# for some reason the printer doesn't properly 
				self._printer._comm._changeState(self._printer._comm.STATE_OPERATIONAL)
				self._printer._comm._currentFile = None
			except Exception:
				self._logger.exception("Error while changing state")
		return line
	
	def _rewrite_m4000_response(self,line):
		"""
		convert M4000 response to M105 report temp response
		needed for octoprint comm layer _monitor loop
		"""
		if "B:0/0" in line:
			m = parse_m4000.search(line)
			# ~ rewritten = line.replace("B:0/0", "T:0 /0 B:{} /{}" % (m.group(1), m.group(2)))
			rewritten = line.replace("ok B:0/0", "T:21.21 /0.0 B:20.32 /0.0")
			rewritten = "T:21.21 /0.0 B:20.32 /0.0"
			self._log_to_terminal(rewritten)
			# ~ self._log_replacement("temperature poll",line, rewritten, only_once=True)
			return rewritten
		else:
			return line
	
	def _rewrite_m114_response(self,line):
		"""
		firmware returns incorrectly formatted M114 response
		Firmware response to M114
		ok C: X:0.000000 Y:0.000000 Z:60.000000 E:0.000000
		strip C: from line
		"""
		if "C: X:" in line:
			rewritten = self.fix_M114.sub("", line)
			self._log_to_terminal(rewritten)
			return rewritten
		else:
			return line
		
	def _rewrite_wait_to_busy(self, line):
		# firmware wrongly assumes "wait" to mean "busy", fix that
		# Used Code from Foosel Octoprint-FixCBDFirmware plugin
		if line == "wait" or line.startswith("wait"):
			self._log_replacement("wait", "wait", "echo:busy processing", only_once=True)
			return "echo:busy processing"
		else:
			return line
	
	def _rewrite_start(self, line):
		if line.startswith('ok V'): # proceed hello command # ok V4.2.20.3_LCDM
			# harvest firmware version to generate a proper aswer to M115
			self.firmware_version = line[3:]
			self._log_replacement("start command",line, "ok start", only_once=True)	
			return 'ok start' + line
		return line
		
	def _rewrite_error(self, line):
		"""
		printer provides incorrectly formatted M27 response
		when not printing. Replace message to trigger cancel
		print behavior in comm.py monitoring loop
		'Error:It's not printing now!' -> 'Not SD printing'
		"""
		if "not printing now" in line:
			if self._printer.is_printing() or self._printer.is_finishing():
				self.finished_print = None
				self._log_replacement("Not SD printing", line, "Not SD printing", only_once=True)
				self._printer.unselect_file()
				self._printer._comm._changeState(self._printer._comm.STATE_OPERATIONAL)
			
				self._logger.debug("printer now operational")
			return "Not SD printing"
		else:
			return line
		
	def _rewrite_identifier(self, line):
		# change identifier to signal stuff is fixed so that printer safety no longer triggers
		rewritten = None
		if "CBD make it" in line:
			# ~ rewritten = line.replace("CBD make it", "CBD made it, foosel fixed it")
			rewritten = line.replace("CBD make it.", "FIRMWARE_NAME:{} PROTOCOL_VERSION:{} ".format("CBD made it", self.firmware_version))
		elif "ZWLF make it" in line:
			rewritten = line.replace("ZWLF make it", "FIRMWARE_NAME:{} PROTOCOL_VERSION:{} ".format("ZWLF made it", self.firmware_version))

		if rewritten:
			self._log_replacement("identifier", line, rewritten)
			return rewritten
		return line
		
	def _rewrite_end_msg(self,line):
		"""
		Unfortunately Chituboard resin printers don't send a standard "Done printing file"
		message after finishing the print.
		Possible ending messages:
		at the end of  End read
		"""
		if "End read" in line:
			try:
				self._printer._comm._changeState(self._printer._comm.STATE_FINISHING)
				self._printer._comm._currentFile.done = True
				self._printer._comm._currentFile.pos = 0
				self._printer._comm._callback.on_comm_print_job_done()

			except Exception:
				self._logger.exception("Error while changing state")
			return line + "\r\n Done printing file", True
		else:	
			return line, False
			
	def _rewrite_print_finished(self,line):
		"""
		Unfortunately Chituboard resin printers don't send a standard "Done printing file"
		message after finishing the print.
		Need to manually generate this proper message.
		For some reason passing 'Done printing file' to line doesn't trigger
		- temporary fix: manually trigger file unselect to stop SD polling
		"""
		if "SD printing byte" in line:
			# answer to M27, at least on Marlin, Repetier and Sprinter: "SD printing byte %d/%d"
			match = self.regex_sdPrintingByte.search(line)
			if match:
				try:
					current = int(match.group("current"))
					total = int(match.group("total"))
					self._logger.info(line)
				except Exception:
					self._logger.exception(
						"Error while parsing SD status report"
					)
				else:
					if current == total != 0:
						if self.finished_print == None:
							self.finished_print = 1
							self._logger.info("finished print = None")
							return line, False
						elif self.finished_print == 1:
							self._logger.info("finished print = 1")
							self._logger.info("Done printing file")
							self._log_replacement("Done printing file", line, "Done printing file", only_once=True)
							line = "Done printing file"
							self.finished_print = None
							return line, True
						elif self.finished_print == 2:
							# ~ self._printer._comm._changeState(self._printer._comm.STATE_OPERATIONAL)
							self._logger.info("printer now operational")
							self._printer.unselect_file()
							# ~ self._printer._comm._currentFile = None
							self.finished_print == None
							return line, False
						else:
							return line, False
		return line, False
		
	def _log_replacement(self, t, orig, repl, only_once=False):
		# Used Code from Foosel Octoprint-FixCBDFirmware plugin
		if not only_once or not self._logged_replacement.get(t, False):
			self._logger.info("Replacing {} with {}".format(orig, repl))
			self._logged_replacement[t] = True
			if only_once:
				self._logger.info(
					"Further replacements of this kind will be logged at DEBUG level."
				)
		else:
			self._logger.debug("Replacing {} with {}".format(orig, repl))
		self._log_to_terminal("{} -> {}".format(orig, repl))
		
	def _log_to_terminal(self, *lines, **kwargs):
		# Used Code from Foosel Octoprint-FixCBDFirmware plugin
		prefix = kwargs.pop(b"prefix", "Repl:")
		if self._printer:
			self._printer.log_lines(
				*list(map(lambda x: "{} {}".format(prefix, x), lines))
			)


__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = Chituboard()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.queuing": (__plugin_implementation__.gcode_modifier.get_gcode_queuing_modifier,1),
		"octoprint.filemanager.extension_tree"  : __plugin_implementation__.get_extension_tree,
		# ~ "octoprint.filemanager.analysis.factory": __plugin_implementation__.get_sla_analysis_factory,
		"octoprint.printer.factory"			 : (__plugin_implementation__.get_sla_printer_factory,1),
		# ~ "octoprint.printer.estimation.factory"  : __plugin_implementation__.get_sla_estimator_factory,
		# ~ "octoprint.comm.protocol.gcode.sending" : __plugin_implementation__.gcode_modifier.get_gcode_send_modifier,
		"octoprint.comm.protocol.gcode.received": (__plugin_implementation__.get_gcode_receive_modifier,1),
		"octoprint.cli.commands": __plugin_implementation__.analysis_commands
		#"octoprint.comm.protocol.gcode.error": handle_error
	}
