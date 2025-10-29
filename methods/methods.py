# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# Do not replicate or redistribute without permission
# All rights reserved.
# ------------------------------------------------------------------------------

import os
import pandas as pd
import shutil
import time
import csv
from datetime import datetime
import threading
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent.parent))
print(Path.cwd().parent)
from ..devices.liquid_handler_devices.ender3_liquid_handlers import Ender3LiquidHandler
from ..devices.liquid_handler_devices.gx_liquid_handlers import GX281
from ..devices.liquid_handler_devices.bed_layout import bed_layout
from ..devices.valves.vici_valves import ViciValve
from ..devices.temperature_controllers.tc720 import TC720
from ..devices.pump_devices.phd_ultra_pumps import PhdUltraPump
from ..devices.pump_devices.vici_m6_pumps import VICI_M6_Pumps
from ..devices.uv_detectors.ocean_optics import Ocean_Optics_UV_vis

class GeneralExperimentMethod:
    def __init__(self, input_file, instrument_config_file, output_dir="Methods//Outputs",
                 output_file="Experimental_Log", delay=0.5):
        # Load the CSV file
        self.input_file = input_file
        self.method = pd.read_csv(self.input_file)
        self.delay = delay  # Global delay parameter

        # Dictionary to store bed layouts for each bed (1-6)
        self.bed_layouts = {}

        # The following will store all the experimental Data generated

        # Start time for experiment logging
        self.start_time = datetime.now()

        # Create output directory with the date of the experimental run
        date_str = self.start_time.strftime('%Y_%m_%d')
        self.output_dir = os.path.join(output_dir, date_str)
        os.makedirs(self.output_dir, exist_ok=True)  # Create directory if it doesn't exist

        # output_file will be used to create a subdirectory to story all the results
        self.experiment_subdir = os.path.join(self.output_dir,
                                              f"{self.start_time.strftime('%Y_%m_%d_%H-%M-%S')}_{output_file}")
        os.makedirs(self.experiment_subdir, exist_ok=True)  # Create the experiment subdirectory

        # Track instruments and VICI valves
        self.instruments = {}
        self.vici_valves = {}

        # Load instrument configuration and initialize devices
        self.instrument_config_file = instrument_config_file
        self.instrument_config = self.load_instrument_config(self.instrument_config_file)
        self.initialize_instruments(self.instrument_config)

        # track every launched pump job
        self._pump_threads = []

        # Copy the input file to the experiment subdirectory
        shutil.copy(self.input_file, os.path.join(self.experiment_subdir, os.path.basename(self.input_file)))

        # Set log filename with timestamp
        self.log_filename = os.path.join(self.experiment_subdir,
                                         f"{self.start_time.strftime('%Y_%m_%d_%H-%M-%S')}_{output_file}.csv")

        # Initialize CSV log file with headers
        with open(self.log_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time', 'Component', 'Action', 'Parameters', 'Output', "Notes"])

    def load_instrument_config(self, config_file):
        """
        Loads the instrument configuration CSV and returns a DataFrame.
        The CSV should contain columns such as InstrumentType, DeviceNumber, Name, COMPort, OtherParams.
        """
        try:
            config_df = pd.read_csv(config_file)
            print(f"Loaded instrument configuration from {config_file}")
            return config_df
        except Exception as e:
            print(f"Error loading instrument configuration: {e}")
            return None

    def initialize_instruments(self, config_df):
        """
        Initializes instrument objects based on the configuration DataFrame.
        The instruments are stored in self.instruments and also set as attributes on self.
        """
        self.instruments = {}
        if config_df is None:
            print("No instrument configuration available.")
            return

        # Loop through each instrument defined in the config file
        for _, row in config_df.iterrows():
            instrument_type = row['InstrumentType'].strip()
            device_number = str(row['DeviceNumber']).strip() if not pd.isna(row['DeviceNumber']) else ""
            com_port = row['COMPort'].strip() if not pd.isna(row['COMPort']) else None
            # Use the provided output_dir for instruments that need it (e.g., UV detector)
            other_params = row['OtherParams'] if 'OtherParams' in row else None

            # Create a unique attribute name for the instrument (e.g., "GX281_1", "Pump_1")
            attr_name = f"{instrument_type}_{device_number}" if device_number else instrument_type

            # Instantiate the instrument based on its type
            if instrument_type == "GX281":
                obj = GX281()
            elif instrument_type == "Pump":
                obj = VICI_M6_Pumps(port=com_port)
            elif instrument_type in ("Valve6Way", "Valve10Way", "Valve24Way"):
                # pick the right string for ViciValve
                valve_type = {
                    "Valve6Way": "6-way",
                    "Valve10Way": "10-way",
                    "Valve24Way": "24-way"
                }[instrument_type]
                obj = ViciValve(port=com_port, valve_type=valve_type)
                try:
                    valve_id = int(device_number)
                    self.vici_valves[valve_id] = obj
                except ValueError:
                    print(f"Invalid valve ID: {device_number}")
            elif instrument_type == "Temperature":
                obj = TC720(port=com_port)
            elif instrument_type == "HarvardPump":
                obj = PhdUltraPump(port=com_port)
            else:
                print(f"Unknown instrument type: {instrument_type}")
                continue

            # Store the instrument in the dictionary and as an attribute for easy access
            self.instruments[attr_name] = obj
            setattr(self, attr_name, obj)
            print(f"Initialized {attr_name} on COM Port {com_port if com_port else 'N/A'}")

    # The role of this script is to log all the experimental data to a csv to be recorded and plotted out in the future.
    def log_to_csv(self, component, action, params, output, notes=""):
        elapsed_time = round((datetime.now() - self.start_time).total_seconds(), 2)
        with open(self.log_filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([elapsed_time, component, action, params, output, notes])

    def run_experiment(self):
        self.log_to_csv(0, "load_method", f"input={self.input_file}", f"Loading input file: {self.input_file}")

        try:
            # Iterate through each row in the CSV file and execute the commands
            for index, row in self.method.iterrows():

                component = row['Component']
                action = row['Action']
                params = row['Parameters']
                notes = row['Notes']

                try:
                    self.delay = float(row['delay']) if 'delay' in row and not pd.isna(row['delay']) else 0.5
                except ValueError:
                    self.delay = 0.5  # Default delay if conversion fails

                if component.upper() == "SYNC" and action == "wait_for_pumps":
                    self.wait_for_pumps()
                    continue
                elif component == 'GX-281':
                    self.execute_gx281(action, params)
                elif component == 'Pump':
                    self.execute_pump(action, params)
                elif component == "HarvardPump":
                    self.execute_harvard_pump(action, params)
                elif component in ('VICI-6Way', 'VICI-10Way', 'VICI-24Way'):
                    self.execute_vici_valve(action, params)
                elif component == 'Temperature':
                    self.execute_temperature(action, params)
                else:
                    self.log_to_csv(component, action, params, "Error: Invalid Component")

                time.sleep(self.delay)

            self.wait_for_pumps()
            self.close_all_connections()

        except:
            self.log_to_csv('', '', '', "Error: Experiment failed stopping exerpiment"
                                        "and closing connections to all instruments")
            self.close_all_connections()

    def execute_gx281(self, action, params):
        # Use the dynamically set attribute (assuming device number 1)
        gx281 = self.instruments.get("GX281_1")
        if gx281 is None:
            self.log_to_csv('GX-281', action, params, "Error: GX-281 not found")
            return

        if action == 'set_bedlayout':
            bed, rack_layout = self.extract_bed_rack_layout(params)
            self.set_bedlayout(bed, rack_layout)
            self.log_to_csv('GX-281', action, params, f"Setting bed {bed} to bed layout {rack_layout}")

        elif action == 'move_home':
            gx281.home()  # move to home
            self.log_to_csv('GX-281', action, "", "Homing GX281")


        elif action == 'move_z_height':
            z_coord = self.extract_height(params)
            gx281.move_z(z_coord)
            self.log_to_csv('GX-281', action, params, f"Moving needle to z height {z_coord}")


        elif action == 'move_xy':
            bed, well = self.extract_bed_well(params)

            # Moved the needle up in case this was not already done ahead of time to avoid breaking the needle
            # If broken need to recallibrate the needle
            gx281.move_z(125)
            time.sleep(1)
            self.log_to_csv('GX-281', action, params,
                            f"Moving GX281 needle up before moving xy coordinates: coordinates: {125}")

            x, y = self.get_coords_for_bed_well(bed, well)
            gx281.move_xy(x, y)
            self.log_to_csv('GX-281', action, params, f"Moving GX281 to bed {bed} well {well}: coordinates: {x, y}")

        elif action == 'move_z':
            bed, well = self.extract_bed_well(params)

            z = self.get_z_for_bed_well(bed, well)
            gx281.move_z(z)
            self.log_to_csv('GX-281', action, params, f"Moving GX281 needle on {bed} well {well}: coordinates: {z}")

        else:
            print("Issue executing GX281")
            self.log_to_csv('GX-281', action, params, "Error: Issue executing GX281")

    def execute_pump(self, action, params):
        # 1 – pull the numbers out of the CSV row
        flow_rate, volume, pump_id = self.extract_flow_rate_volume(params)

        # 2 – grab the pump object
        pump = self.instruments.get(f"Pump_{int(pump_id)}")
        if pump is None:
            self.log_to_csv('Pump', action, params,
                            f"Error: Pump with ID {pump_id} not found")
            return

        # 3 – validate the action BEFORE we launch a thread
        if action not in ("aspirating", "dispensing"):
            print("Error: Invalid action – must be aspirating or dispensing")
            self.log_to_csv('Pump', action, params,
                            "Error: Invalid action")
            return

        if action in ['aspirating', 'dispensing']:
            if flow_rate <= 0 or volume <= 0:
                self.log_to_csv('Pump', action, params,f"{action} a volume of {volume} uL "
                                                       f"at a flow rate of {flow_rate} uL/min" 
                                                       f"had either a flow rate of 0 or a volume of zero "
                                                       f"and command was skipped")
                return

        est_time = abs(volume) / (abs(flow_rate) / 60)  # seconds

        # 5 – worker that actually drives the syringe pump
        def _vici_job():
            try:
                pump.start()
                pump.set_flow_rate(abs(flow_rate), action)  # driver uses |rate|
                pump.pump_solution(volume)  # <-- blocks here
                pump.stop()
                self.log_to_csv(
                    "Pump", action, params,
                    f"{action} {abs(volume)} µL @ {flow_rate} µL/min on Pump {pump_id}",
                    notes=f"≈{est_time:.1f} s"
                )
            except Exception as e:
                self.log_to_csv("Pump", action, params,
                                f"Error in VICI thread: {e}")

        # 6 – launch, record, move on
        thread = threading.Thread(target=_vici_job, daemon=True)
        thread.start()
        self._pump_threads.append(thread)

        self.log_to_csv("Pump", action, params,
                        f"Started async {action} on Pump {pump_id}",
                        notes=f"exp. {est_time:.1f} s")

    def execute_harvard_pump(self, action, params):
        syringe, volume, rate, harvard_pump_id = self.extract_harvard_params(action, params)
        hp_key = f"HarvardPump_{harvard_pump_id}"
        pump: PhdUltraPump = self.instruments.get(hp_key)

        if pump is None:
            self.log_to_csv("HarvardPump", action, params,
                            f"Error: Harvard pump {harvard_pump_id} not found")
            return

        try:
            if action == "select_syringe":
                pump.select_syringe(syringe)
                self.log_to_csv("HarvardPump", action, params,
                                f"Loaded {syringe} mL syringe")

            elif action == "infuse":
                def _harvard_job():
                    try:
                        pump.infuse_volume(volume, rate)  # blocks in thread
                        self.log_to_csv("HarvardPump", action, params,
                                        f"Infusion done on HarvardPump {harvard_pump_id}")
                    except Exception as e:
                        self.log_to_csv("HarvardPump", action, params, f"Error in Harvard thread: {e}")

                thread = threading.Thread(target=_harvard_job, daemon=True)
                thread.start()
                self._pump_threads.append(thread)
                self.log_to_csv("HarvardPump", action, params, f"Started async infusion {volume} µL @ {rate} µL/min")

            elif action == "stop":
                pump.stop()
                self.log_to_csv("HarvardPump", action, params, "Stopped")

            else:
                raise ValueError("unknown action")

        except Exception as exc:
            self.log_to_csv("HarvardPump", action, params, f"Error: {exc}")

    def wait_for_pumps(self):
        """Block until every launched pump thread ends, then reset list."""
        for t in self._pump_threads:
            t.join()
        self.log_to_csv(0, "wait_for_pumps", "", "All pumps finished")
        self._pump_threads.clear()  # ready for the next batch

    def execute_vici_valve(self, action, params):
        """
        action: 'go_to_position' or 'move_home'
        params: 'position=3,valve_id=1' or 'valve_id=-1'
        """

        # If position doesn't change it was unsuccessful in moving to this position
        if action == 'go_to_position':
            position, valve_id = self.extract_position_and_valve_ids(params)
            if position is None:
                self.log_to_csv('VICI', action, params, 'Error: position missing ' + str(position))
                return

            # Selects the Valve ID to switch positions with
            targets = self.vici_valves.values() if valve_id == -1 else [self.vici_valves.get(valve_id)]
            for valve in targets:
                if valve:
                    valve.go_to_position(position)
                    self.log_to_csv('VICI', action, params, f"Moved valves {valve_id} to {position}")

                    current = valve.check_current_position()
                    note = f"Valve {valve_id if valve_id != -1 else valve_id} now at {current}"
                    self.log_to_csv('VICI', 'check_position', f"valve_id={valve_id}", current, notes=note)

        # Selects the Vici Valve to move home
        elif action == 'move_home':
            valve_id = self.extract_valve_ids(params)
            targets = self.vici_valves.values() if valve_id == -1 else [self.vici_valves.get(valve_id)]
            for valve in targets:
                if valve:
                    valve.move_home()
                    self.log_to_csv('VICI', action, params, f"Homed valves {valve_id}")

                    current = valve.check_current_position()
                    note = f"Valve {valve_id if valve_id != -1 else valve_id} now at {current}"
                    self.log_to_csv('VICI', 'check_position', f"valve_id={valve_id}", current, notes=note)

    def execute_temperature(self, action, params):
        if action == 'set_temperature':
            temp, temp_id = self.extract_temperature(params)
            temp_key = f"Temperature_{int(temp_id)}"
            temp_ctrl = self.instruments.get(temp_key)

            if temp_ctrl is None:
                self.log_to_csv('Temperature', action, params,
                                f"Error: Temperature controller with ID {temp_id} not found")
                return

            temp_ctrl.set_temperature(temp)

            print(f"Temperature Controller set to {temp}")
            print(f"Temperature Controller {temp_id} set to {temp}")
            self.log_to_csv('Temperature', action, params, f"Temperature Controller set to {temp}")
            # Future commands should return a bit value to check that it set the temperature correctly
            # Currently the temperature controller is not capable of setting to negative values and should be programmed later

    def set_bedlayout(self, bed, rack_layout):
        # Set the layout for the specific bed with the given rack_layout
        bed_layout = Bed_Layout(bed_number=bed, rack_layout=rack_layout)  # Assuming "Reactants" as bed_type
        self.bed_layouts[bed] = bed_layout
        print(f"Bed {bed} layout set with rack_layout {rack_layout}")

    # Helper functions to extract parameters from the parameter string
    def extract_bed_rack_layout(self, params):
        param_dict = {key.strip(): int(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return param_dict['bed'], param_dict['rack_layout']

    def extract_bed_well(self, params):
        param_dict = {key.strip(): int(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return int(param_dict['bed']), int(param_dict['well'])

    def extract_height(self, params):
        param_dict = {key.strip(): int(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return param_dict['height']

    def extract_flow_rate_volume(self, params):
        param_dict = {key.strip(): float(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return param_dict['flow_rate'], param_dict['volume'], param_dict['pump_id']

    def extract_harvard_params(self, action, params):
        param_dict = {key.strip(): float(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}

        pump_id = int(param_dict['pump_id'])

        if action == "select_syringe":
            syringe = int(param_dict['syringe'])
            return syringe, None, None, pump_id

        elif action == "infuse":
            volume = float(param_dict['volume'])
            rate = float(param_dict['rate'])
            return None, volume, rate, pump_id

        elif action == "stop":
            return None, None, None, pump_id

        else:
            raise ValueError(f"unknown HarvardPump action '{action}'")

    def extract_temperature(self, params):
        param_dict = {key.strip(): int(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return float(param_dict['temp']), int(param_dict['temp_id'])

    def extract_position_and_valve_ids(self, params):
        # Extract valve_id(s) from the parameters
        param_dict = {key.strip(): int(float(value.strip())) for key, value in
                      (param.split('=') for param in params.split(','))}
        return param_dict['position'], param_dict['valve_id']

    def extract_valve_ids(self, params):
        # Extract valve_id(s) from the parameters
        param_dict = {key.strip(): int(value.strip()) for key, value in
                      (param.split('=') for param in params.split(','))}
        return param_dict['valve_id']

    def get_coords_for_bed_well(self, bed, well):
        x = self.bed_layouts[bed].get_well(well).get_x()
        y = self.bed_layouts[bed].get_well(well).get_y()
        # Return the X and Y coordinates based on the bed and well
        return x, y

    def get_z_for_bed_well(self, bed, well):
        z = self.bed_layouts[bed].get_well(well).get_z()
        # Return Z coordinate based on the bed and well number
        return z  # Example; replace with actual logic

    def close_all_connections(self):
        """
        Close serial connections on all initialized instruments.
        """
        for name, inst in self.instruments.items():
            if hasattr(inst, 'close') and callable(inst.close):
                try:
                    inst.close()
                    print(f"Closed connection for {name}")
                except Exception as e:
                    print(f"Failed to close {name}: {e}")

