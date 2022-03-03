# OctolapseAutoConfigurePlugin

This plugin adds slicing settings to gcode files for Octolapse. No further configuration is required to get Octolapse to work with Cura.

The gcode script is based on an original created by tjjfvi (https://github.com/tjjfvi).


Forked from [`fieldOfView/Cura-LinearAdvanceSettingPlugin`](https://github.com/fieldOfView/Cura-LinearAdvanceSettingPlugin).

## Development Tips

Kill existing instances of Cura
Start Cura in the background
Monitor Cura log
```
(
    pgrep -f cura | xargs kill -9
    /Applications/Ultimaker\ Cura.app/Contents/MacOS/cura &
    tail -f ~/Library/Application\ Support/cura/4.13/cura.log | ag "\[MainThread\] UM\.Logger"
)
```

## TODO

* Replace placeholders (e.g. `; layer_height = {layer_height}`) somehow...
    https://github.com/Ultimaker/Cura/tree/master/docs
    Might be better to inject it into the `default_value` of `machine_start_gcode` on init - this will allow the placeholders to be replaced automatically
