/*
 * View model for OctoPrint-Sla_plugin
 *
 * Author: Philipp Herbrich
 * License: AGPLv3
 */
$(function() {
    function Sla_pluginViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        //~ self.filesViewModel = parameters[0];
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Sla_pluginViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        //dependencies: [ "filesViewModel" ],
        dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_sla_plugin, #tab_plugin_sla_plugin, ...
        elements: [ /* ... */ ]
    });
});
