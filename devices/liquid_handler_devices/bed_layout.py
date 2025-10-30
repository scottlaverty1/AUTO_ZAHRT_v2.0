# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------
from Wells import Well

class Bed_Layout():

    #The bed number has a fixed location of 1, 2, 3, 4, 5, 6 which needs to be fixed in the code; user should not be able to edit this
    #The rack_layout the user should need to input to make sure they use the correct layout
    def __init__(self, bed_number, rack_layout):

        #Sets the location bed number on the GX281 liquid handler
        # The far left is labeled 1 and far right is labeled 6
        self.bed_number=bed_number

        #Determines the layout of the racks, to feed into
        self.rack_layout=rack_layout

        self.wells={}
        self.X=[]
        self.Y=[]
        self.Z = None

        self.coordinates=[]

        self.x_offset = [] #[22.2, 141.8, 261.3, 380.9, 500.5, 620]

        self.num_wells=None

        if rack_layout == 204:
            self.X = [0, 31.8, 63.6]
            self.Y = [103.4, 135.2, 166.9, 198.7, 230.4, 262.1, 293.9,325.6,357.4]
            self.Z = 60
            self.num_wells = 27
            self.x_offset = [22.2, 141.8, 261.3, 380.9, 500.5, 620]
            [[self.coordinates.append([x + self.x_offset[self.bed_number - 1], y]) for y in self.Y] for x in self.X]

        elif rack_layout==207:
            self.X = [0, 19.3, 38.6, 57.9, 77.2]
            self.Y = [95, 114.3, 133.6, 152.9, 172.2, 191.5, 210.8, 230.1, 249.4, 268.7, 288, 307.3, 326.6, 345.9, 365]
            self.Z = 115
            self.num_wells = 75
            self.x_offset = [15, 134.6, 254.2, 373.8, 493.4, 613]
            [[self.coordinates.append([x + self.x_offset[self.bed_number - 1], y]) for y in self.Y] for x in self.X]

        elif rack_layout==209:
            self.X = [0, 16.6, 33.2, 49.8, 66.4, 83]
            for i in range(0,16):
                self.Y.append(93 + 17.7 * i)
            self.Z = 86
            self.num_wells = 96
            self.x_offset = [13, 132.6, 252.2, 371.8, 491.4, 611]
            self.stagger = 8.5
            for x_index, x in enumerate(self.X):
                for y in self.Y:
                    if x_index % 2 == 0:
                        self.coordinates.append([x + self.x_offset[self.bed_number - 1], y])
                    else:
                        self.coordinates.append([x + self.x_offset[self.bed_number -1], y + self.stagger])

        # This is our custom rack lay out used to match the 20 mL ender3 which only supports one bed layout
        # There is only one bed on the 3d printer liquid handler unlike the GX devices
        elif rack_layout == "304":
            self.X = [30.5, 71.5, 112.5, 153.5, 194.5]
            self.Y = [30.5, 71.5, 112.5, 153.5]
            self.Z = 10
            self.num_wells = 20
            [[self.coordinates.append([x, y]) for y in self.Y] for x in self.X]

        self.set_wells()

    # Can just fold this method into class initialization later on.
    def set_wells(self):

        # Assigns the bed layout as well as the x, y, and z positions of the liquid handler.
        if self.rack_layout == 204 or self.rack_layout == 207 or self.rack_layout == 209 or self.rack_layout == 304:
            print(f"Bed {self.bed_number} set to bed layout {self.rack_layout}")

        else:
            raise ValueError(f"Invalid bed layout type {self.rack_layout}. Currently supported types: 204, 207, 209, and 304.")


        
        for i in range(1, self.num_wells + 1):
            self.wells[i] = Well(i)

        for index, coordinate in enumerate(self.coordinates):
            self.wells[index+1].set_x(coordinate[0])
            self.wells[index+1].set_y(coordinate[1])
            self.wells[index+1].set_z(self.Z)

        return None

    def get_wells(self):
        return self.wells

    def get_well(self,index):
        return self.wells[index]