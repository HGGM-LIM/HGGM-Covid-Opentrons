""" Short description of this Python module.

Longer description of this module.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__authors__ = ["Jon Sicilia", "Alicia Arévalo","Luis Torrico", "Alejandro André", "Aitor Gastaminza", "Alex Gasulla", "Sara Monzon" , "Miguel Julian", "Eva González" , "José Luis Villanueva", "Angel Menendez Vazquez", "Nick"]
__contact__ = "aarevalo@hggm.es"
__copyright__ = "Copyright 2020, CovidRobots"
__date__ = "2020/06/01"
__license__ = "GPLv3"
__version__ = "1.0.0"


# #####################################################
# Imports
# #####################################################
from opentrons import protocol_api
from opentrons.types import Point, Location
import time
import math
import os
import subprocess
import json
import itertools
import numpy as np
from timeit import default_timer as timer
from datetime import datetime
import csv

# #####################################################
# Metadata
# #####################################################
metadata = {
    'protocolName': 'Template',
    'author': 'Alicia Arévalo (aarevalo@hggm.es)',
    'source': 'Hospital Gregorio Marañon',
    'apiLevel': '2.4',
    'description': ''
}

# #####################################################
# Protocol parameters
# #####################################################
NUM_SAMPLES = 96
RESET_TIPCOUNT = False
PROTOCOL_ID = "GM"
recycle_tip = False # Do you want to recycle tips? It shoud only be set True for testing
photosensitivity = False
# End Parameters to adapt the protocol

#Defined variables
##################
## global vars
## initialize robot object
robot = None
# default var for drop tip switching
switch = True
# initialize tip_log dictionary
tip_log = {}
tip_log['count'] = {}
tip_log['tips'] = {}
tip_log['max'] = {}
tip_log['used'] = {}
#pip speed
aspirate_default_speed = 1
dispense_default_speed = 1
blow_out_default_speed = 1

### Formulas info ###
'''
Where V : Volumen ; B: Area of base ; h : Height; r : Radius ; d : Diameter; A = Area

### General ###

V = B * h 

h = V / B

### Circular Cylinder ###

V = math.pi * r**2 * h

V = math.pi * d**2 * h / 4

 
### For hemispheres ###

h = r

r = d / 2

V = 2 * math.pi * r**3 / 3

V = math.pi * d**3 / 12

### For Cones ###

V = math.pi * r**2 * h / 3

h = 3 * V / (math.pi * r**2)

V = math.pi * d**2 * h / 12

h = 12 * V / (math.pi * d**2)

### Area of a circle ###

A = math.pi * r**2 

A = math.pi * d**2 / 4

'''
### End formulas info ###
### Start defautl robot values ###
'''
Well Bottom Clearances

Aspirate default: 1mm above the bottom

Dispense default: 1mm above the bottom

p20_single_gen2

Aspirate Default: 3.78 µL/s

Dispense Default: 3.78 µL/s

Blow Out Default: 3.78 µL/s

Minimum Volume: 1 µL

Maximum Volume: 20 µL

p300_single_gen2

Aspirate Default: 46.43 µL/s

Dispense Default: 46.43 µL/s

Blow Out Default: 46.43 µL/s

Minimum Volume: 20 µL

Maximum Volume: 300 µL

p1000_single_gen2

Aspirate Default: 137.35 µL/s

Dispense Default: 137.35 µL/s

Blow Out Default: 137.35 µL/s

Minimum Volume: 100 µL

Maximum Volume: 1000 µL

p20_multi_gen2

Aspirate Default: 7.6 µL/s

Dispense Default: 7.6 µL/s

Blow Out Default: 7.6 µL/s

Minimum Volume: 1 µL

Maximum Volume: 20 µL

p300_multi_gen2

Aspirate Default: 94 µL/s

Dispense Default: 94 µL/s

Blow Out Default: 94 µL/s

Minimum Volume: 20 µL

Maximum Volume: 300 µL
'''
### Enc defautl robot values ###

# #####################################################
# Common classes
# #####################################################
class Tube:

    """Summary
    
    Attributes:
        actual_volume (TYPE): Description
        base_type (TYPE): Description
        diameter (TYPE): Description
        height (TYPE): Description
        height_base (TYPE): Description
        max_volume (TYPE): Description
        name (TYPE): Description
        volume_base (TYPE): Description
    """
    
    def __init__(self, name, max_volume, actual_volume, diameter, 
                 base_type, height_base, min_height=0.5, reservoir = False):
        """Summary
        
        Args:
            name (String): Description
            max_volume (float): Description
            actual_volume (float): Description
            diameter (float): Description
            base_type (integer): 1 => Base type U (Hemisphere), 2 => Base type V (Cone), 3 => Base type flat (|_|)
            height_base (float): Description
        """
        self._name = name
        self._max_volume = max_volume
        self._actual_volume = actual_volume
        self._diameter = diameter
        self._base_type = base_type
        self._height_base = height_base
        self._min_height = min_height
        self._reservoir = reservoir

        if base_type == 1:
            self._volume_base = (math.pi * diameter**3) / 12
            self._height_base = diameter / 2
        elif base_type == 2:
            self._volume_base = (math.pi * diameter**2 * height_base) / 12
        else:
            self._volume_base = 0
            self._height_base = 0

    @property
    def reservoir(self):
        return self._reservoir
    
    @property
    def actual_volume(self):
        return self._actual_volume

    @actual_volume.setter
    def actual_volume(self, value):
        self._actual_volume = value

    def calc_height(self, aspirate_volume):
        volume_cylinder = self._actual_volume - self._volume_base
        if volume_cylinder <= aspirate_volume:
            height = self._min_height
        else:
            cross_section_area = (math.pi * self._diameter**2) / 4   
            height = ((self._actual_volume - aspirate_volume - self._volume_base) / cross_section_area) + self._height_base
            if height < self._min_height:
                height = self._min_height

        return height


class Reagent:
    def __init__(self, name, flow_rate_aspirate, flow_rate_dispense, 
        flow_rate_aspirate_mix, flow_rate_dispense_mix, delay_aspirate=0, 
        delay_dispense = 0, touch_tip_aspirate_speed = 20, 
        touch_tip_dispense_speed = 20):
        self._name = name
        self._flow_rate_aspirate = flow_rate_aspirate
        self._flow_rate_dispense = flow_rate_dispense
        self._flow_rate_blow_out = flow_rate_dispense
        self._flow_rate_aspirate_mix = flow_rate_aspirate_mix
        self._flow_rate_dispense_mix = flow_rate_dispense_mix
        self._delay_aspirate = delay_aspirate
        self._delay_dispense = delay_dispense
        self._touch_tip_aspirate_speed = touch_tip_aspirate_speed
        self._touch_tip_dispense_speed = touch_tip_dispense_speed

    @property
    def flow_rate_aspirate(self):
        return self._flow_rate_aspirate

    @property
    def flow_rate_dispense(self):
        return self._flow_rate_dispense

    @property
    def flow_rate_blow_out(self):
        return self._flow_rate_blow_out

    @property
    def flow_rate_aspirate_mix(self):
        return self._flow_rate_dispense_mix

    @property
    def flow_rate_dispense_mix(self):
        return self._flow_rate_dispense_mix

    @property
    def delay_aspirate(self):
        return self._delay_aspirate

    @property
    def delay_dispense(self):
        return self._delay_dispense

    @property
    def touch_tip_aspirate_speed(self):
        return self._touch_tip_aspirate_speed

    @property
    def touch_tip_dispense_speed(self):
        return self._touch_tip_dispense_speed
    
    
    

# Constants
TEXT_NOTIFICATIONS_DICT = {
    'start': f"Started process",
    'finish': f"Finished process",
    'close_door': f"Close the door",
    'replace_tipracks': f"Replace tipracks",
}



# #####################################################
# Global functions
# #####################################################
def notification(action):
    if not robot.is_simulating():
        robot.comment(TEXT_NOTIFICATIONS_DICT[action])

def check_door():
    if 'CLOSED' in str(robot._hw_manager.hardware.door_state):
        return True
    else:
        return False

def confirm_door_is_closed():
    if not robot.is_simulating():
        #Check if door is opened
        if check_door() == False:
            #Set light color to red and pause
            robot._hw_manager.hardware.set_lights(button = True, rails =  False)
            robot.pause()
            notification('close_door')
            time.sleep(5)
            confirm_door_is_closed()
        else:
            if photosensitivity==False:
                robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            else:
                robot._hw_manager.hardware.set_lights(button = True, rails =  False)

def start_run():
    notification('start')
    if photosensitivity==False:
        robot._hw_manager.hardware.set_lights(button = True, rails =  True)
    else:
        robot._hw_manager.hardware.set_lights(button = True, rails =  False)
    now = datetime.now()
    # dd/mm/YY H:M:S
    start_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return start_time

def finish_run():
    notification('finish')
    #Set light color to blue
    robot._hw_manager.hardware.set_lights(button = True, rails =  False)
    now = datetime.now()
    # dd/mm/YY H:M:S
    finish_time = now.strftime("%Y/%m/%d %H:%M:%S")
    if photosensitivity==False:
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            time.sleep(0.3)
    else:
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  False)
            time.sleep(0.3)
    return finish_time

def reset_tipcount(file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    if os.path.isfile(file_path):
        os.remove(file_path)

def retrieve_tip_info(pip,tipracks,file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    global tip_log
    if not tip_log['count'] or pip not in tip_log['count']:
        tip_log['count'][pip] = 0
        if not robot.is_simulating():
            folder_path = os.path.dirname(file_path)
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            if os.path.isfile(file_path):
                with open(file_path) as json_file:
                    data = json.load(json_file)
                    if "P1000" in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips1000' in data.keys() else data['tips1000']
                    elif 'P300' in str(pip) and 'Single-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips300' in data.keys() else data['tips300']
                    elif 'P300' in str(pip) and '8-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tipsm300' in data.keys() else data['tipsm300']
                    elif 'P20' in str(pip) and 'Single-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips20' in data.keys() else data['tips20']
                    elif 'P20' in str(pip) and '8-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tipsm20' in data.keys() else data['tipsm20']                        
        if "8-Channel" in str(pip):
            tip_log['tips'][pip] =  [tip for rack in tipracks for tip in rack.rows()[0]]
        else:
            tip_log['tips'][pip] = [tip for rack in tipracks for tip in rack.wells()]

        tip_log['max'][pip] = len(tip_log['tips'][pip])

    if not tip_log['used'] or pip not in tip_log['used']:
        tip_log['used'][pip] = 0

    return tip_log


def save_tip_info(file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    data = {}
    if not robot.is_simulating():
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                data = json.load(json_file)
            os.rename(file_path,file_path + ".bak")
        for pip in tip_log['count']:
            if "P1000" in str(pip):
                data['tips1000'] = tip_log['count'][pip]
            elif 'P300' in str(pip) and 'Single-Channel' in str(pip):
                data['tips300'] = tip_log['count'][pip]
            elif 'P300' in str(pip) and '8-Channel' in str(pip):
                data['tipsm300'] = tip_log['count'][pip]
            elif 'P20' in str(pip) and 'Single-Channel' in str(pip):
                data['tips20'] = tip_log['count'][pip]
            elif 'P20' in str(pip) and '8-Channel' in str(pip):
                data['tipsm20'] = tip_log['count'][pip]

        with open(file_path, 'a+') as outfile:
            json.dump(data, outfile)


def pick_up(pip,tiprack):
    ## retrieve tip_log
    global tip_log
    if not tip_log:
        tip_log = {}
    tip_log = retrieve_tip_info(pip,tiprack)
    if tip_log['count'][pip] == tip_log['max'][pip]:
        notification('replace_tipracks')
        robot.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
        confirm_door_is_closed()
        pip.reset_tipracks()
        tip_log['count'][pip] = 0
    pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
    # Optional only to prevente cacelations
    # save_tip_info()
    tip_log['count'][pip] += 1
    if "8-Channel" not in str(pip):
        tip_log['used'][pip] += 1
    else:
        tip_log['used'][pip] += 8


def drop(pip):
    global switch
    if recycle_tip:
        pip.return_tip()                           
    else:
        if "8-Channel" not in str(pip):
            side = 1 if switch else -1
            drop_loc = robot.loaded_labwares[12].wells()[0].top().move(Point(x=side*20))
            pip.drop_tip(drop_loc,home_after=False)
            switch = not switch
        else:
            drop_loc = robot.loaded_labwares[12].wells()[0].top().move(Point(x=20))
            pip.drop_tip(drop_loc,home_after=False)

def change_pip_speed(pip, reagent, mix=False):
    aspirate_default_speed = pip.flow_rate.aspirate
    dispense_default_speed = pip.flow_rate.dispense
    blow_out_default_speed = pip.flow_rate.blow_out

    if mix:
        pip.flow_rate.aspirate = reagent.flow_rate_aspirate_mix    
        pip.flow_rate.dispense = reagent.flow_rate_dispense_mix
    else:
        pip.flow_rate.aspirate = reagent.flow_rate_aspirate    
        pip.flow_rate.dispense = reagent.flow_rate_dispense
        
    pip.flow_rate.blow_out = reagent.flow_rate_blow_out

def restore_pip_speed(pip):
    pip.flow_rate.aspirate = aspirate_default_speed
    pip.flow_rate.dispense = dispense_default_speed
    pip.flow_rate.blow_out = blow_out_default_speed


# Function definitions
## General purposes
def divide_volume(volume,max_vol):
    num_transfers=math.ceil(volume/max_vol)
    vol_roundup=math.ceil(volume/num_transfers)
    last_vol=volume-vol_roundup*(num_transfers-1)
    vol_list=[vol_roundup for v in range(1,num_transfers)]
    vol_list.append(last_vol)
    return vol_list

def divide_destinations(l, n):
    # Divide the list of destinations in size n lists.
    for i in range(0, len(l), n):
        yield l[i:i + n]

# Function definitions
## Expecific for liquids
def custom_mix(pip, reagent, repetitions, volume, location, mix_height = 3, 
    source_height = 3):
    '''
    Function for mixing a given volume in the same location a x number of repetitions.
    source_height: height from bottom to aspirate
    mix_height: height from bottom to dispense
    '''
    change_pip_speed(pip=pip,
                    reagent = reagent, 
                    mix = True)

    if mix_height == 0:
        mix_height = 3

    pip.aspirate(volume = 1,
                 location = location.bottom(z=source_height))
    for _ in range(repetitions):
        pip.aspirate(volume = volume, 
                    location = location.bottom(z=source_height))
        pip.dispense(volume = volume, 
                    location = location.bottom(z=mix_height))

    pip.dispense(volume = 1, 
                location = location.bottom(z=mix_height))

    restore_pip_speed(pip=pip)
    
def distribute_custom(pip, reagent, tube_type, volume, src, dest, max_volume=0,
    extra_dispensal=0, disp_height=0, touch_tip_aspirate=False, 
    touch_tip_dispense = False):

    change_pip_speed(pip=pip,
                    reagent = reagent, 
                    mix = True)
    
    if max_volume == 0:
        max_volume = pip.max_volume
    
    if len(dest) > 1 or max_volume < (volume + extra_dispensal):
        max_trans_per_asp = (max_volume - extra_dispensal) // volume
    else:
        max_trans_per_asp = 1

    if max_trans_per_asp != 0:

        volume_per_asp = (max_trans_per_asp * volume) + extra_dispensal

        list_dest = list(divide_destinations(dest,max_trans_per_asp))

        for i in range(len(list_dest)):
            pickup_height = tube_type.calc_height(volume_per_asp)

            if tube_type.reservoir:
                tube_type.actual_volume -= (max_trans_per_asp * volume * 8)
            else:
                tube_type.actual_volume -= (max_trans_per_asp * volume)
            
            volume_per_asp = (len(list_dest[i]) * volume) + extra_dispensal

            pip.aspirate(volume=volume_per_asp, 
                        location=src.bottom(pickup_height))

            robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
            
            if touch_tip_aspirate:
                    pip.touch_tip(radius=1.0,
                                v_offset=-5,
                                speed=reagent.touch_tip_aspirate_speed)
            
            for d in list_dest[i]:

                pip.dispense(volume=volume,
                            location=d.bottom(disp_height))

                robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent    
                
                if touch_tip_dispense:
                    pip.touch_tip(radius=1.0,
                                v_offset=-5,
                                speed=reagent.touch_tip_dispense_speed)
            
            if extra_dispensal != 0:
                pip.blow_out(location=src.top())

    else:

        list_vol_per_well = divide_volume(volume,(max_volume - extra_dispensal))

        list_dest = dest

        for d in list_dest:

            for vol in list_vol_per_well:

                volume_per_asp = vol + extra_dispensal

                pickup_height = tube_type.calc_height(volume_per_asp)

                if tube_type.reservoir:
                    tube_type.actual_volume -= (vol * 8)
                else:
                    tube_type.actual_volume -= vol

                pip.aspirate(volume=volume_per_asp, 
                            location=src.bottom(pickup_height))

                robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
            
                if touch_tip_aspirate:
                    pip.touch_tip(radius=1.0,
                                v_offset=-5,
                                speed=reagent.touch_tip_aspirate_speed)
            
                pip.dispense(volume=vol,
                            location=d.bottom(disp_height),
                            rate=reagent.flow_rate_dispense)

                robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent    
               
                if touch_tip_dispense:
                    pip.touch_tip(radius=1.0,
                                v_offset=-5,
                                speed=reagent.touch_tip_dispense_speed)

                if extra_dispensal != 0:
                    pip.blow_out(location=src.top())

    restore_pip_speed(pip=pip)


def find_side(col):
    if col%2 == 0:
        side = -1 # left
    else:
        side = 1 # right
    return side


def remove_supernatant(pip, reagent, tube_type, volume, src, 
    dest, x_offset_src, max_volume=0, pickup_height=0.5, x_offset_dest=0, 
    disp_height=0):

    change_pip_speed(pip=pip,
                    reagent = reagent, 
                    mix = False)
    
    if max_volume == 0:
        max_volume = pip.max_volume

    s = src.bottom(pickup_height).move(Point(x = x_offset_src))

    d = dest.bottom(disp_height).move(Point(x = x_offset_dest))

    list_vol_per_round = divide_volume(volume,max_volume)

    for vol in list_vol_per_round:

        #pickup_height = tube_type.calc_height(volume_per_asp)

        if tube_type.reservoir:
            tube_type.actual_volume -= (vol * 8)
        else:
            tube_type.actual_volume -= vol

        pip.aspirate(volume=vol, 
                    location=s)

        robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
    
        pip.dispense(volume=vol,
                    location=d)

        pip.blow_out()

        robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent    

    restore_pip_speed(pip=pip)


def remove_supernatant_and_drop(pip, reagent, tube_type, volume, src, 
    x_offset_src, max_volume=0, pickup_height=0.5):

    change_pip_speed(pip=pip,
                    reagent = reagent, 
                    mix = False)
    
    if max_volume == 0:
        max_volume = pip.max_volume

    s = src.bottom(pickup_height).move(Point(x = x_offset_src))
    
    drop_loc = robot.loaded_labwares[12].wells()[0].top().move(Point(x=20))
    
    list_vol_per_round = divide_volume(volume,max_volume)
    
    if len(list_vol_per_round) != 1:

        for i, vol in enumerate(list_vol_per_round):

            if i != 0:
                pip.dispense(volume=pip.min_volume, 
                        location=src.top())                

            if tube_type.reservoir:
                tube_type.actual_volume -= (vol * 8)
            else:
                tube_type.actual_volume -= vol

            pip.aspirate(volume=vol, 
                        location=s)

            robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
        
            pip.dispense(volume=vol,
                        location=drop_loc)

            pip.blow_out()

            pip.aspirate(volume=pip.min_volume, 
                        location=drop_loc)
    else:
    
        if tube_type.reservoir:
            tube_type.actual_volume -= (volume * 8)
        else:
            tube_type.actual_volume -= volume

        pip.aspirate(volume=volume, 
                    location=s)

        robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
        
    drop(pip)
    
    restore_pip_speed(pip=pip)
   
def aspirate_wit_scrolling(pip, volume, src, 
    start_height = 0, stop_height = 0, x_offset_src = 0):

    start_point = src._depth if start_height == 0 else start_height

    stop_point = 0.0 if stop_height == 0 else stop_height

    max_asp = volume/pip.min_volume

    inc_step = (start_point - stop_point) / max_asp

    for h in reversed(np.arange(stop_point, start_point, inc_step)):
        s = src.bottom(h).move(Point(x = x_offset_src))
        pip.aspirate(volume=pip.min_volume, 
                location=s)



# #####################################################
# Protocol start
# #####################################################
def run(ctx: protocol_api.ProtocolContext):

    # Initial data
    global robot
    global tip_log

    # Set robot as global var
    robot = ctx

    # check if tipcount is being reset
    if RESET_TIPCOUNT:
        reset_tipcount()

    if not robot.is_simulating():
        # confirm door is close
        robot.comment(f"Please, close the door")
        confirm_door_is_closed()

        start = start_run()


    # Labware
    # Positions are:
    # 10    11      TRASH
    # 7     8       9
    # 4     5       6
    # 1     2       3

    # #####################################################
    # Common functions
    # #####################################################
    
    # -----------------------------------------------------
    # Execute step
    # -----------------------------------------------------
    def run_step(step):

        robot.comment(' ')
        robot.comment('###############################################')
        robot.comment('Step ' + str(step) + ': ' + STEPS[step]['Description'])
        robot.comment('===============================================')

        # Execute step?
        if STEPS[step]['Execute']:

            # Get start info
            elapsed = datetime.now()
            for i, key in enumerate(tip_log['used']):
                val = tip_log['used'][key]
                if i == 0: 
                    cl = val
                else:
                    cr = val

            # Execute function step
            STEPS[step]['Function']()

            # Wait
            if STEPS[step].get('wait_time'):
                robot.comment('===============================================')
                wait = STEPS[step]['wait_time']
                robot.delay(seconds = wait)

            # Get end info
            elapsed = datetime.now() - elapsed
            for i, key in enumerate(tip_log['used']):
                val = tip_log['used'][key]
                if i == 0: 
                    cl = val - cl
                else:
                    cr = val - cr
            # Stats
            STEPS[step]['Time:'] = str(elapsed)
            robot.comment('===============================================')
            robot.comment('Elapsed time: ' + str(elapsed))
            for i, key in enumerate(tip_log['used']):
                if i == 0: 
                    robot.comment('Tips "' + str(key) + '" used: ' + str(cl))
                else:
                    robot.comment('Tips "' + str(key) + '" used: ' + str(cr))

        # Dont execute step
        else:
            robot.comment('No ejecutado')

        # End
        robot.comment('###############################################')
        robot.comment(' ')

    # #####################################################
    # 1. Start defining deck
    # #####################################################

    # -----------------------------------------------------
    # Tips
    # -----------------------------------------------------
    tips20 = [
        robot.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['1', '2', '3', '4']
    ]
    tips300 = [robot.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['5', '6']
    ]

    tips1000 = [robot.load_labware('opentrons_96_filtertiprack_1000ul', slot)
        for slot in ['7']
    ]

    # -----------------------------------------------------
    # Pipettes
    # -----------------------------------------------------
    p20 = robot.load_instrument('p20_single_gen2', 'right', tip_racks=tips20)

    p300 = robot.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

    p1000 = robot.load_instrument('p1000_single_gen2', 'left', tip_racks=tips1000)

    m20 = robot.load_instrument('p20_multi_gen2', 'left', tip_racks=tips20)

    m300 = robot.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)

    ## retrieve tip_log
    retrieve_tip_info(p1000,tips1000)
    retrieve_tip_info(m300,tips300)

    if not p1000.hw_pipette['has_tip']:
        pick_up(p1000)

    # -----------------------------------------------------
    # Magnetic module + labware
    # -----------------------------------------------------
    # magdeck = robot.load_module('Magnetic Module Gen2', '10')
    # maglab = magdeck.load_labware('nest_1_reservoir_195ml', 'nest_1_reservoir_195ml')
    # magdeck.disengage()
    # magdeck.engage()

    # -----------------------------------------------------
    # Temperature module + labware
    # -----------------------------------------------------
    # tempdeck = robot.load_module('Temperature Module Gen2', '1')
    # templab = tempdeck.load_labware('nest_12_reservoir_15ml', 'nest_12_reservoir_15ml')
    # tempdeck.set_temperature(4)
    # tempdeck.deactivate()
    # tempdeck.start_set_temperature(4)

    # -----------------------------------------------------
    # Labware
    # -----------------------------------------------------
    labware_x = robot.load_labware('nest_12_reservoir_15ml', '4', 'reagent reservoir')
    labware_y = robot.load_labware('nest_12_reservoir_15ml', '5', 'reagent reservoir')

    buffer_rack = robot.load_labware('opentrons_6_tuberack_falcon_50ml_conical', '7',
        '6_tuberack_falcon source rack')

    protK_rack = ctx.load_labware('opentrons_24_tuberack_nest_2ml_screwcap', '9',
            'source tuberack ')
    
    dest_rack = ctx.load_labware('nest_96_wellplate_2ml_deep', '8', 'source tuberack ')

    # -----------------------------------------------------
    # Reagens
    # -----------------------------------------------------
    name_reagent = Reagent(name = 'AVL',
                    flow_rate_aspirate = 600,
                    flow_rate_dispense = 1000,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix =1000)

    easyMag_reagent = Reagent(name = 'EasyMag',
                    flow_rate_aspirate = 300,
                    flow_rate_dispense = 500,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix = 1000)

    lisis_reagent = Reagent(name = 'Lisis',
                    flow_rate_aspirate = 300,
                    flow_rate_dispense = 1,
                    flow_rate_aspirate_mix = 300,
                    flow_rate_dispense_mix = 300,
                    delay_aspirate=3,
                    touch_tip_dispense_speed=70

    # -----------------------------------------------------
    # Tubes
    # -----------------------------------------------------
    name_tube = Tube(name = 'Falcon 50mL Conical Centrifuge Tubes',
                max_volume = 50000,
                actual_volume = 50000,
                diameter = 27.81, # avl1.diameter
                base_type = 2,
                height_base = 18)    

    protK_tube = Tube(name = 'Generic opentrons 24 tuberack nest 2ml Tubes',
                actual_volume = 1900,
                max_volume = 2000,
                diameter = 8.7, # avl1.diameter
                base_type = 2,
                height_base = 4)   

    wash1_tube = Tube(name = 'reservoir 15ml plate',
                actual_volume = 1250, 
                max_volume = 1875, # 15000 / 8 => Max reservoir plate / num rows
                diameter = 8.7, 
                base_type = 3,
                height_base = 0)     
				
    pool_tube = Tube(name = 'nest_1_reservoir_195ml',
                actual_volume = 195000, 
                max_volume = 195000, 
                diameter = 99.68, 
                base_type = 3,
                height_base = 0,
                min_height = 3,
                reservoir = True)
                
    swim = Tube(name = 'nest_12_reservoir_15ml',
                actual_volume = 15000, 
                max_volume = 15000, 
                diameter = 26.68, 
                base_type = 3,
                height_base = 0,
                reservoir = True)
                
    mmix_tube = Tube(name = 'nest_96_wellplate_100ul_pcr_full_skirt',
                actual_vol = 45, 
                max_vol = 100, # 15000 / 8 => Max reservoir plate / num rows
                diameter = 5.34,
                base_type = 2,
                height_base = 14.78)
                
    x = elution_dest_rack.columns()[i][0].top().point.x
	x = 14.36
    y = 345.65
    z = 120
            
    loc = Location(Point(x, y, z), 'Warning')
    m20.move_to(location = loc)
                
   
    # #####################################################
    # 2. Steps definition
    # #####################################################

    # -----------------------------------------------------
    # Step n: ....
    # -----------------------------------------------------
    def step1():
        robot.comment('1')
        p1000.pick()
        p1000.drop()

    # -----------------------------------------------------
    # Step n: ....
    # -----------------------------------------------------
    def step2():
        robot.comment('2')

    # -----------------------------------------------------
    # Step n: ....
    # -----------------------------------------------------
    def step3():
        robot.comment('3')
        m300.pick()
        m300.drop()

    # -----------------------------------------------------
    # Step n: ....
    # -----------------------------------------------------
    def step4():
        robot.comment('4')

    # -----------------------------------------------------
    # Step n: ....
    # -----------------------------------------------------
    def step5():        
        robot.comment('5')

    # -----------------------------------------------------
    # Execution plan
    # -----------------------------------------------------
    STEPS = {
        1:{'Execute': True,  'Function': step1, 'Description': 'Mix beads'},
        2:{'Execute': False, 'Function': step2, 'Description': 'Transfer lysis'},
        3:{'Execute': True,  'Function': step3, 'Description': 'Wait with magnet OFF', 'wait_time': 600}, 
        4:{'Execute': True,  'Function': step4, 'Description': 'Incubate wait with magnet ON', 'wait_time': 300},
        5:{'Execute': True,  'Function': step5, 'Description': 'Remove supernatant'}
    }

    # #####################################################
    # 3. Execute every step!!
    # #####################################################
    for step in STEPS:
        run_step(step)

    # track final used tip
    save_tip_info()

    # -----------------------------------------------------
    # Stats
    # -----------------------------------------------------
    if not robot.is_simulating():
        end = finish_run()

        robot.comment('===============================================')
        robot.comment('Start time:   ' + str(start))
        robot.comment('Finish time:  ' + str(end))
        robot.comment('Elapsed time: ' + str(datetime.strptime(end, "%Y/%m/%d %H:%M:%S") - datetime.strptime(start, "%Y/%m/%d %H:%M:%S")))
        for key in tip_log['used']:
            val = tip_log['used'][key]
            robot.comment('Tips "' + str(key) + '" used: ' + str(val))
        robot.comment('===============================================')


	# -----------------------------------------------------
    # Pause to empty trash
    # -----------------------------------------------------
    def trash():
        x = 14.36
        y = 345.65
        z = 180
        loc = Location(Point(x, y, z), 'Warning')
        m300.move_to(location = loc)
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            time.sleep(0.3)
        robot.pause('Vaciar cubeta de puntas')