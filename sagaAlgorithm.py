# -*- coding: utf-8 -*-

"""
***************************************************************************
    sagaAlgorithm.py
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
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingOutputFile
                      )
from processing.core.parameters import getParameterFromString
from processing.tools.system import isWindows

from processing_saga import sagaUtils

pluginPath = os.path.dirname(__file__)


class SagaAlgorithm(QgsProcessingAlgorithm):

    def __init__(self, descriptionFile):
        super().__init__()

        self.descriptionFile = descriptionFile
        self._name = ""
        self._displayName = ""
        self._group = ""
        self._groupId = ""
        self._shortHelp = ""

        self.params = []

        self.defineCharacteristicsFromFile()

    def createInstance(self):
        return self.__class__(self.descriptionFile)

    def name(self):
        return self._name

    def displayName(self):
        return self._displayName

    def group(self):
        return self._group

    def groupId(self):
        return self._groupId

    def shortHelpString(self):
        return self._shortHelp

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "saga.svg"))

    def tr(self, text):
        return QCoreApplication.translate("SagaAlgorithm", text)

    def initAlgorithm(self, config=None):
        pass

    def defineCharacteristicsFromFile(self):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        pass
