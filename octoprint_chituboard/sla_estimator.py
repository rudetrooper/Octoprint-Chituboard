import os
import re
from octoprint.filemanager import FileDestinations, NoSuchStorage, valid_file_type, full_extension_tree
from octoprint.printer.estimation import PrintTimeEstimator, TimeEstimationHelper
from .file_formats.utils import get_file_format	
from octoprint.settings import settings
from pathlib import Path
import octoprint.filemanager
import octoprint.filemanager.util

class SLAPrintTimeEstimator(PrintTimeEstimator):
	def __init__(self, job_type):
		self.stats_weighing_until = settings().getFloat(
			["estimation", "printTime", "statsWeighingUntil"]
		)
		self.validity_range = settings().getFloat(
			["estimation", "printTime", "validityRange"]
		)
		self.force_dumb_from_percent = settings().getFloat(
			["estimation", "printTime", "forceDumbFromPercent"]
		)
		self.force_dumb_after_min = settings().getFloat(
			["estimation", "printTime", "forceDumbAfterMin"]
		)
		
		threshold = None
		rolling_window = None
		countdown = None
		
		if job_type == "local" or job_type == "sdcard":
			# we are happy if the average of the estimates stays within 60s of the prior one
			threshold = settings().getFloat(
				["estimation", "printTime", "stableThreshold"]
			)
		
			if job_type == "sdcard":
				# we are interesting in a rolling window of roughly the last 15s, so the number of entries has to be derived
				# by that divided by the sd status polling interval
				interval = settings().getFloat(["serial", "timeout", "sdStatus"])
				if interval <= 0:
					interval = 1.0
				rolling_window = int(15 // interval)
				if rolling_window < 1:
					rolling_window = 1
		
				# we are happy when one rolling window has been stable
				countdown = rolling_window
		
		self._data = TimeEstimationHelper(
			rolling_window=rolling_window, countdown=countdown, threshold=threshold
		)

	def estimate(self, progress, printTime, cleanedPrintTime, statisticalTotalPrintTime, statisticalTotalPrintTimeType):
		"""
		Tries to estimate the print time left for the print job
	
		This is somewhat horrible since accurate print time estimation is pretty much impossible to
		achieve, considering that we basically have only two data points (current progress in file and
		time needed for that so far - former prints or a file analysis might not have happened or simply
		be completely impossible e.g. if the file is stored on the printer's SD card) and
		hence can only do a linear estimation of a completely non-linear process. That's a recipe
		for inaccurate predictions right there. Yay.
	
		Anyhow, here's how this implementation works. This method gets the current progress in the
		printed file (percentage based on bytes read vs total bytes), the print time that elapsed,
		the same print time with the heat up times subtracted (if possible) and if available also
		some statistical total print time (former prints or a result from the GCODE analysis).
	
		  1. First get an "intelligent" estimate based on the :class:`~octoprint.printer.estimation.TimeEstimationHelper`.
			 That thing tries to detect if the estimation based on our progress and time needed for that becomes
			 stable over time through a rolling window and only returns a result once that appears to be the
			 case.
		  2. If we have any statistical data (former prints or a result from the GCODE analysis)
			 but no intelligent estimate yet, we'll use that for the next step. Otherwise, up to a certain percentage
			 in the print we do a percentage based weighing of the statistical data and the intelligent
			 estimate - the closer to the beginning of the print, the more precedence for the statistical
			 data, the closer to the cut off point, the more precedence for the intelligent estimate. This
			 is our preliminary total print time.
		  3. If the total print time is set, we do a sanity check for it. Based on the total print time
			 estimate and the time we already spent printing, we calculate at what percentage we SHOULD be
			 and compare that to the percentage at which we actually ARE. If it's too far off, our total
			 can't be trusted and we fall back on the dumb estimate. Same if the time we spent printing is
			 already higher than our total estimate.
		  4. If we do NOT have a total print time estimate yet but we've been printing for longer than
			 a configured amount of minutes or are further in the file than a configured percentage, we
			 also use the dumb estimate for now.
	
		Yes, all this still produces horribly inaccurate results. But we have to do this live during the print and
		hence can't produce to much computational overhead, we do not have any insight into the firmware implementation
		with regards to planner setup and acceleration settings, we might not even have access to the printed file's
		contents and such we need to find something that works "mostly" all of the time without costing too many
		resources. Feel free to propose a better solution within the above limitations (and I mean that, this solution
		here makes me unhappy).
	
		Args:
			progress (float or None): Current percentage in the printed file
			printTime (float or None): Print time elapsed so far
			cleanedPrintTime (float or None): Print time elapsed minus the time needed for getting up to temperature
				(if detectable).
			statisticalTotalPrintTime (float or None): Total print time of past prints against same printer profile,
				or estimated total print time from GCODE analysis.
			statisticalTotalPrintTimeType (str or None): Type of statistical print time, either "average" (total time
				of former prints) or "analysis"
	
		Returns:
			(2-tuple) estimated print time left or None if not proper estimate could be made at all, origin of estimation
		"""
		# always reports 2h as printTimeLeft
		return 2 * 60 * 60, "estimate"
		
	def estimate_total(self, progress, printTime):
		if not progress or not printTime or not self._data:
			return None
		else:
			return self._data.update(printTime / progress)
        
        
# ~ def print_status() -> str:
    # ~ with ElegooMars() as elegoo_mars:
        # ~ selected_file = elegoo_mars.get_selected_file()
        # ~ print_status = elegoo_mars.get_print_status()

        # ~ if print_status.state == PrinterState.IDLE:
            # ~ progress = 0.0
            # ~ print_details = {}
        # ~ else:
            # ~ sliced_model_file = read_cached_sliced_model_file(
                # ~ FILES_DIRECTORY / selected_file
            # ~ )

            # ~ if print_status.current_byte == 0:
                # ~ current_layer = 1
            # ~ else:
                # ~ current_layer = (
                    # ~ sliced_model_file.end_byte_offset_by_layer.index(
                        # ~ print_status.current_byte
                    # ~ )
                    # ~ + 1
                # ~ )

            # ~ progress = (
                # ~ 100.0
                # ~ * none_throws(current_layer - 1)
                # ~ / none_throws(sliced_model_file.layer_count)
            # ~ )

            # ~ print_details = {
                # ~ "current_layer": current_layer,
                # ~ "layer_count": sliced_model_file.layer_count,
                # ~ "print_time_secs": sliced_model_file.print_time_secs,
                # ~ "time_left_secs": round(
                    # ~ sliced_model_file.print_time_secs * (100.0 - progress) / 100.0
                # ~ ),
            # ~ }

        # ~ return jsonify(
            # ~ {
                # ~ "state": print_status.state.value,
                # ~ "selected_file": selected_file,
                # ~ "progress": progress,
                # ~ **print_details,
            # ~ }
        # ~ )        
