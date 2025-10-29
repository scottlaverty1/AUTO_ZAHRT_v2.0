# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2024 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

class Well():

    def __init__(self, well_number, x=None, y=None, z=None):

        self.well_number=well_number

        self.x=x
        self.y=y
        self.z=z

    def set_well_labels(self,well_number):
        self.well_number=well_number

    def get_well_labels(self):
        return self.well_number

    def set_x(self,x):
        self.x=x

    def get_x(self):
        return self.x

    def set_y(self,y):
        self.y=y

    def get_y(self):
        return self.y

    def set_z(self,z):
        self.z=z

    def get_z(self):
        return self.z
