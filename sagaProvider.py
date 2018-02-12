# -*- coding: utf-8 -*-

"""
***************************************************************************
    sagaProvider.py
    ---------------------
    Date                 : February 2018
    Copyright            : (C) 2018 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'February 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import Qgis, QgsProcessingProvider, QgsMessageLog

from processing.core.ProcessingConfig import ProcessingConfig, Setting

from processing_saga.sagaAlgorithm import SagaAlgorithm
from processing_saga import sagaUtils

pluginPath = os.path.dirname(__file__)


class SagaProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

        self.algs = []
        self.exportCommand = ""

    def id(self):
        return "sagagis"

    def name(self):
        return "SAGA GIS"

    def longName(self):
        version = sagaUtils.version()
        return "SAGA GIS ({})".format(version) if version is not None else "SAGA GIS"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "saga.svg"))

    def load(self):
        resamplingMethods = []
        with open(os.path.join(pluginPath, "iosettings.txt")) as f:
            line = f.readline().strip()
            resamplingMethods = line.split(";")

            self.exportCommand = f.readline().strip()

        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(),
                                            sagaUtils.SAGA_ACTIVE,
                                            self.tr("Activate"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            sagaUtils.SAGA_EXECUTABLE,
                                            self.tr("SAGA executable"),
                                            sagaUtils.sagaExecutable(),
                                            valuetype=Setting.FILE))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            sagaUtils.SAGA_RESAMPLING,
                                            self.tr("Resampling method"),
                                            resamplingMethods[0],
                                            valuetype=Setting.SELECTION,
                                            options=resamplingMethods))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            sagaUtils.SAGA_VERBOSE,
                                            self.tr("Log commands output"),
                                            False))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(sagaUtils.SAGA_ACTIVE)
        ProcessingConfig.removeSetting(sagaUtils.SAGA_EXECUTABLE)
        ProcessingConfig.removeSetting(sagaUtils.SAGA_VERBOSE)

    def isActive(self):
        return ProcessingConfig.getSetting(sagaUtils.SAGA_ACTIVE)

    def setActive(self, active):
        ProcessingConfig.setSettingValue(sagaUtils.SAGA_ACTIVE, active)

    def defaultVectorFileExtension(self, hasGeometry=True):
        return "shp"

    def defaultRasterFileExtension(self):
        return "sdat"

    def supportedOutputRasterLayerExtensions(self):
        return ["sgrd"]

    def supportedOutputVectorLayerExtensions(self):
        return ["shp"]

    def supportsNonFileBasedOutput(self):
        return False

    def loadAlgorithms(self):
        self.algs = []
        folder = sagaUtils.descriptionPath()

        for descriptionFile in os.listdir(folder):
            if descriptionFile.endswith("txt"):
                try:
                    alg = SagaAlgorithm(os.path.join(folder, descriptionFile))
                    if alg.name().strip() != '':
                        self.algs.append(alg)
                    else:
                        QgsMessageLog.logMessage(self.tr("Could not load SAGA algorithm from file: {}".format(descriptionFile)),
                                                 self.tr("Processing"), Qgis.Critical)
                except Exception as e:
                    QgsMessageLog.logMessage(self.tr("Could not load SAGA algorithm from file: {}\n{}".format(descriptionFile, str(e))),
                                             self.tr("Processing"), Qgis.Critical)

        for a in self.algs:
            self.addAlgorithm(a)

    def tr(self, string, context=""):
        if context == "":
            context = "SagaProvider"
        return QCoreApplication.translate(context, string)
