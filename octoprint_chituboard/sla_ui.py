

def setTabs(self):
    
    disabledTabs = self._settings.global_get(["appearance", "components", "disabled", "tab"])
    if disabledTabs == None:
        disabledTabs = []

    if self.hideTempTab:
        if "temperature" not in disabledTabs:
            disabledTabs.append("temperature")
    else:
        if "temperature" in disabledTabs:
            disabledTabs.remove("temperature")

    if self.hideControlTab:
        if "control" not in disabledTabs:
            disabledTabs.append("control")
    else:
        if "control" in disabledTabs:
            disabledTabs.remove("control")

    if self.hideGCodeTab:
        if "gcodeviewer" not in disabledTabs:
            disabledTabs.append("gcodeviewer")
    else:
        if "gcodeviewer" in disabledTabs:
            disabledTabs.remove("gcodeviewer")

    self._settings.global_set(["appearance", "components", "disabled", "tab"], disabledTabs)
