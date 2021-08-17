/*
 * View model for OctoPrint-Chituboard
 *
 * Author: Vikram Sarkhel
 * License: AGPLv3
 */
$(function() {
    function Sla_pluginViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        self.filesViewModel = parameters[0];
        // self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
        
        self.filesViewModel.enableAdditionalData = function (data) {
			console.log("plugin Octoprin-Chituboard called")
            return data["gcodeAnalysis"] || data["analysis"] || (data["prints"] && data["prints"]["last"]);
        };

        self.filesViewModel.toggleAdditionalData = function (data) {
            var entryElement = self.filesViewModel.getEntryElement(data);
            if (!entryElement) return;

            var additionalInfo = $(".additionalInfo", entryElement);
            additionalInfo.slideToggle("fast", function () {
                $(".toggleAdditionalData i", entryElement).toggleClass(
                    "fa-chevron-down fa-chevron-up"
                );
            });
        };
        self.filesViewModel.getAdditionalData = function (data) {
            var output = "";
            console.log("plugin Octoprin-Chituboard called getAdditionalData")
            if (data["gcodeAnalysis"]) {
				if (data["gcodeAnalysis"]["dimensions"]) {
                    var dimensions = data["gcodeAnalysis"]["dimensions"];
                    output +=
                        gettext("Model size") +
                        ": " +
                        _.sprintf(
                            "%(width).2fmm &times; %(depth).2fmm &times; %(height).2fmm",
                            dimensions
                        );
                    output += "<br>";
                }
                if (
                    data["gcodeAnalysis"]["filament"] &&
                    typeof data["gcodeAnalysis"]["filament"] === "object"
                ) {
                    var filament = data["gcodeAnalysis"]["filament"];
                    if (_.keys(filament).length === 1) {
                        output +=
                            gettext("Filament") +
                            ": " +
                            formatFilament(
                                data["gcodeAnalysis"]["filament"]["tool" + 0]
                            ) +
                            "<br>";
                    } else if (_.keys(filament).length > 1) {
                        _.each(filament, function (f, k) {
                            if (
                                !_.startsWith(k, "tool") ||
                                !f ||
                                !f.hasOwnProperty("length") ||
                                f["length"] <= 0
                            )
                                return;
                            output +=
                                gettext("Filament") +
                                " (" +
                                gettext("Tool") +
                                " " +
                                k.substr("tool".length) +
                                "): " +
                                formatFilament(f) +
                                "<br>";
                        });
                    }
                }
                output +=
                    gettext("Estimated print time") +
                    ": " +
                    (self.settingsViewModel.appearance_fuzzyTimes()
                        ? formatFuzzyPrintTime(
                              data["gcodeAnalysis"]["estimatedPrintTime"]
                          )
                        : formatDuration(data["gcodeAnalysis"]["estimatedPrintTime"])) +
                    "<br>";
                    
			} else if (data["analysis"]) {
                if (data["analysis"]["dimensions"]) {
                    var dimensions = data["analysis"]["dimensions"];
                    output +=
                        gettext("Model size") +
                        ": " +
                        _.sprintf(
                            "%(width).2fmm &times; %(depth).2fmm &times; %(height).2fmm",
                            dimensions
                        );
                    output += "<br>";
                }
                if (
                    data["analysis"]["filament"] &&
                    typeof data["analysis"]["filament"] === "object"
                ) {
                    var filament = data["analysis"]["filament"];
                    if (_.keys(filament).length === 1) {
                        output +=
                            gettext("Volume") +
                            ": " +
                            _.sprintf("%(volume).03f mL",
                            {volume: data["analysis"]["filament"]["tool" + 0]["volume"]})
                            +
                            "<br>";
                    } else if (_.keys(filament).length > 1) {
                        _.each(filament, function (f, k) {
                            if (
                                !_.startsWith(k, "tool") ||
                                !f ||
                                !f.hasOwnProperty("length") ||
                                f["length"] <= 0
                            )
                                return;
                            output +=
                                gettext("Filament") +
                                " (" +
                                gettext("Tool") +
                                " " +
                                k.substr("tool".length) +
                                "): " +
                                formatFilament(f) +
                                "<br>";
                        });
                    }
                }
                output +=
                    gettext("Estimated print time") +
                    ": " +
                    (self.settingsViewModel.appearance_fuzzyTimes()
                        ? formatFuzzyPrintTime(
                              data["analysis"]["estimatedPrintTime"]
                          )
                        : formatDuration(data["analysis"]["estimatedPrintTime"])) +
                    "<br>";
                if (data["analysis"]["layer_count"]) {
                    var layer_count = data["analysis"]["layer_count"];
                    output +=
                        gettext("Layer count") +
                        ": " +
                        _.sprintf("%(layer)02d",{layer: layer_count});
                    output += "<br>";
				}
				if (data["analysis"]["layer_height_mm"]) {
                    var layer_height = data["analysis"]["layer_height_mm"];
                    output +=
                        gettext("Layer height") +
                        ": " +
                        _.sprintf("%(layer).02f mm",{layer: layer_height});
                    output += "<br>";
				}
				if (data["analysis"]["printer_name"]) {
                    var printer_name = data["analysis"]["printer_name"];
                    output +=
                        gettext("Printer name") +
                        ": " +
                        printer_name;
                    output += "<br>";
				}
            }
            if (data["prints"] && data["prints"]["last"]) {
                output +=
                    gettext("Last printed") +
                    ": " +
                    formatTimeAgo(data["prints"]["last"]["date"]) +
                    "<br>";
                if (data["prints"]["last"]["printTime"]) {
                    output +=
                        gettext("Last print time") +
                        ": " +
                        formatDuration(data["prints"]["last"]["printTime"]);
                }
            }
            return output;
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Sla_pluginViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["filesViewModel", "settingsViewModel"],
        //~ dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_sla_plugin, #tab_plugin_sla_plugin, ...
        elements: ["#files_template_machinecode"]
    });
});
