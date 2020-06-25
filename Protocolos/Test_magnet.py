# #####################################################
# Imports
# #####################################################
from opentrons import protocol_api

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
    magdeck.engage(height = 25.0)
    robot.pause('Test')
    magdeck.disengage()