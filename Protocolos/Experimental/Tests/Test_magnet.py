# #####################################################
# Imports
# #####################################################
from opentrons import protocol_api
import numpy as np

# #####################################################
# Metadata
# #####################################################

metadata = {
    'protocolName': 'Magnet test',
    'apiLevel': '2.4',
    'description': ''
}

# #####################################################
# Protocol start
# #####################################################
def run(robot: protocol_api.ProtocolContext):

    # -----------------------------------------------------
    # Magnetic module + labware
    # -----------------------------------------------------
    magdeck = robot.load_module('Magnetic Module Gen2', '1')
    maglab = magdeck.load_labware('nest_96_wellplate_2ml_deep', 'nest_96_wellplate_2ml_deep')
    #magdeck.engage(height = 7)

    for i in np.arange(0.0,25.0,0.1):
        magdeck.engage(height = i)
        robot.comment('Actual height =' + str(i))
        robot.pause('Test')
    magdeck.disengage()