# Copyright (c) 2022 Mike Roberts / m-roberts
# Copyright (c) 2020 Aldo Hoeben / fieldOfView
# The OctolapseAutoConfigurePlugin is released under the terms of the AGPLv3 or higher.

from . import OctolapseAutoConfigurePlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": OctolapseAutoConfigurePlugin.OctolapseAutoConfigurePlugin()}
