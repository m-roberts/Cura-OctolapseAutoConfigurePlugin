# Copyright (c) 2022 Mike Roberts / m-roberts
# Copyright (c) 2020 Aldo Hoeben / fieldOfView

# The OctolapseAutoConfigurePlugin is released under the terms of the AGPLv3 or higher.

import time
import os.path
from typing import Any, cast, Dict, List, Optional, Set, TYPE_CHECKING
from PyQt5.QtCore import QCoreApplication

from UM.Job import Job
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack #For typing.
from UM.Version import Version

from cura.CuraApplication import CuraApplication
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager

if TYPE_CHECKING:
    from UM.OutputDevice.OutputDevice import OutputDevice

class OctolapseAutoConfigurePlugin(Extension):
    def __init__(self) -> None:
        super().__init__()

        self._application = CuraApplication.getInstance()
        self.settings_output = ""  # type: str

        self._scene = self._application.getController().getScene() #type: Scene

        self._all_extruders_settings = None #type: Optional[Dict[str, Any]] # cache for all setting values from all stacks (global & extruder) for the current machine

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
                self.settings_output = f.read()
        except:
            Logger.logException("e", "Could not load Octolapse settings file")
            return

        self._application.getOutputDeviceManager().writeStarted.connect(self._filterGcode)

    # Modified from CuraEngineBackend's 'StartSliceJob.py'
    def _buildReplacementTokens(self, stack: ContainerStack) -> Dict[str, Any]:
        """Creates a dictionary of tokens to replace in g-code pieces.

        This indicates what should be replaced in the start and end g-codes.
        :param stack: The stack to get the settings from to replace the tokens with.
        :return: A dictionary of replacement tokens to the values they should be replaced with.
        """

        result = {}
        for key in stack.getAllKeys():
            result[key] = stack.getProperty(key, "value")
            Job.yieldThread()

        # # Material identification in addition to non-human-readable GUID
        # result["material_id"] = stack.material.getMetaDataEntry("base_file", "")
        # result["material_type"] = stack.material.getMetaDataEntry("material", "")
        # result["material_name"] = stack.material.getMetaDataEntry("name", "")
        # result["material_brand"] = stack.material.getMetaDataEntry("brand", "")

        # # Renamed settings.
        # result["print_bed_temperature"] = result["material_bed_temperature"]
        # result["print_temperature"] = result["material_print_temperature"]
        # result["travel_speed"] = result["speed_travel"]

        # #Some extra settings.
        # result["time"] = time.strftime("%H:%M:%S")
        # result["date"] = time.strftime("%d-%m-%Y")
        # result["day"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][int(time.strftime("%w"))]
        # result["initial_extruder_nr"] = self._application.getExtruderManager().getInitialExtruderNr()

        # ALL POSSIBLE VALUES:
        #
        # result["layer_height"] = layer_height
        # result["smooth_spiralized_contours"] = smooth_spiralized_contours
        # result["magic_mesh_surface_mode"] = magic_mesh_surface_mode
        # result["machine_extruder_count"] = machine_extruder_count
        # result["speed_z_hop"] = speed_z_hop
        # result["retraction_amount"] = retraction_amount
        # result["retraction_hop"] = retraction_hop
        # result["retraction_hop_enabled"] = retraction_hop_enabled
        # result["retraction_enable"] = retraction_enable
        # result["retraction_speed"] = retraction_speed
        # result["retraction_retract_speed"] = retraction_retract_speed
        # result["retraction_prime_speed"] = retraction_prime_speed
        # result["speed_travel"] = speed_travel
        # result["max_feedrate_z_override"] = max_feedrate_z_override

        return result

    # Taken from CuraEngineBackend's 'StartSliceJob.py'
    def _cacheAllExtruderSettings(self):
        global_stack = cast(ContainerStack, self._application.getGlobalContainerStack())

        # NB: keys must be strings for the string formatter
        self._all_extruders_settings = {
            "-1": self._buildReplacementTokens(global_stack)
        }
        QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
        for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
            extruder_nr = extruder_stack.getProperty("extruder_nr", "value")
            self._all_extruders_settings[str(extruder_nr)] = self._buildReplacementTokens(extruder_stack)
            QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

    # Taken from CuraEngineBackend's 'StartSliceJob.py'
    def _expandGcodeTokens(self, value: str, default_extruder_nr: int = -1) -> str:
        """Replace setting tokens in a piece of g-code.

        :param value: A piece of g-code to replace tokens in.
        :param default_extruder_nr: Stack nr to use when no stack nr is specified, defaults to the global stack
        """
        if not self._all_extruders_settings:
            self._cacheAllExtruderSettings()

        try:
            # any setting can be used as a token
            fmt = GcodeStartEndFormatter(default_extruder_nr = default_extruder_nr)
            if self._all_extruders_settings is None:
                return ""
            settings = self._all_extruders_settings.copy()
            settings["default_extruder_nr"] = default_extruder_nr
            return str(fmt.format(value, **settings))
        except:
            Logger.logException("w", "Unable to do token replacement on start/end g-code")
            return str(value)

    def _filterGcode(self, output_device: "OutputDevice") -> None:
        gcode_dict = getattr(self._scene, "gcode_dict", None)

        if not gcode_dict:
            Logger.warning("Scene has no gcode to process")
            return

        # Use values from the first used extruder by default so we get the expected temperatures
        self.settings_output = self._expandGcodeTokens(
            self.settings_output,
            self._application.getExtruderManager().getInitialExtruderNr()
        )

        Logger.info("OctolapseAutoConfigurePlugin: self.settings_output:")
        Logger.info(self.settings_output)

        for plate_id in gcode_dict:
            gcode_dict[plate_id].insert(1, self.settings_output)

        Logger.info("OctolapseAutoConfigurePlugin: Filtered Gcode")

        setattr(self._scene, "gcode_dict", gcode_dict)
