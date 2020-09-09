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
    tips1000 = [
        robot.load_labware('opentrons_96_filtertiprack_1000ul', slot)
        for slot in ['5']
    ]

    p1000 = robot.load_instrument('p1000_single_gen2', 'left', tip_racks = tips1000)
    
    tubes = robot.load_labware('opentrons_24_tuberack_nest_2ml_screwcap', '3')

    p1000.pick_up_tip()

    p1000.aspirate(volume = 1,
                 location = tubes['A1'].bottom())

    #robot.pause('Test height')

    p1000.dispense(volume = 1,
                 location = tubes['A1'].top())

    #robot.pause('Test height')

    p1000.aspirate(volume = 1,
                 location = tubes['D6'].bottom())

    #robot.pause('Test height')

    p1000.dispense(volume = 1,
                 location = tubes['D6'].top())
    
    #robot.pause('Test height')

    p1000.return_tip()
    