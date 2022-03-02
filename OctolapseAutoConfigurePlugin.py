# Copyright (c) 2022 Mike Roberts / m-roberts
# Copyright (c) 2020 Aldo Hoeben / fieldOfView

# The OctolapseAutoConfigurePlugin is released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication
from UM.Logger import Logger
from UM.Version import Version

import os.path

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from UM.OutputDevice.OutputDevice import OutputDevice

class OctolapseAutoConfigurePlugin(Extension):
    def __init__(self) -> None:
        super().__init__()

        self._application = CuraApplication.getInstance()
        self.settings_output = list()  # type: List[str]

        try:
            api_version = self._application.getAPIVersion()
        except AttributeError:
            # UM.Application.getAPIVersion was added for API > 6 (Cura 4)
            # Since this plugin version is only compatible with Cura 3.5 and newer, and no version-granularity
            # is required before Cura 4.7, it is safe to assume API 5
            api_version = Version(5)

        if api_version >= Version("6.2.0"):  # v4.2
            settings_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_output.gcode")
        else:
            settings_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_output-legacy.gcode")

        try:
            with open(settings_output_path, "r", encoding = "utf-8") as f:
                self.settings_output = f.read().split("\n")
        except:
            Logger.logException("e", "Could not load Octolapse settings file")
            return

        self._application.getOutputDeviceManager().writeStarted.connect(self._filterGcode)

    def _filterGcode(self, output_device: "OutputDevice") -> None:
        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            gcode_dict[plate_id] = [f"{ele}\n" for ele in self.settings_output] + gcode_list

        setattr(scene, "gcode_dict", gcode_dict)
