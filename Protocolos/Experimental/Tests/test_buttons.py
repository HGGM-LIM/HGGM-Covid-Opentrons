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
    # for i in range(3):
    #     robot._hw_manager.hardware.set_lights(button = False, rails =  False)
    #     time.sleep(0.3)
    #     robot._hw_manager.hardware.set_lights(button = True, rails =  True)
    #     time.sleep(0.3)
    #     robot.comment('Actual height =' + str(i))
    # robot.pause('Test')
    tips300 = [robot.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['11']
    ]
    
    # -----------------------------------------------------
    # Pipettes
    # -----------------------------------------------------
    m300 = robot.load_instrument('p300_multi_gen2', 'right', tip_racks=tips300)

    robot._hw_manager.hardware.set_lights(button =(1,0,0), rails =  False)

    