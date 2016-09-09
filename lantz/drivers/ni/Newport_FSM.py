# Demo code to control Newport FSM, based off of original by David J. Christle
# Original code here:
# https://github.com/dchristle/qtlab/blob/master/instrument_plugins/Newport_FSM.py

from lantz.drivers.ni.daqmx import System
from lantz.drivers.ni.daqmx import AnalogOutputTask, VoltageOutputChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel #CounterInputTask, CountEdgesChannel, DigitalOutputChannel, DigitalOutputTask

from lantz import Feat, DictFeat, Action

import numpy as np

from numpy import abs, ceil, pi, linspace, cos, ones

from time import sleep

from ctypes import c_uint32


class Newport_FSM(System):
    """
    Class for controlling Newport FSM using National Instruments DAQ.
    """

    def initialize(self):
        """
        Creates AO tasks for controlling FSM.
        """
        self.task = AnalogOutputTask('FSM')

        self.dev_name = 'dev1/'

        self.fsm_dimensions = {
            'x': {'micron_per_volt': 9.5768,
                  'min_v': -10.0,
                  'max_v': +10.0,
                  'default': 0.0,
                  'origin': 0.0,
                  'ao_channel': 'ao0'},
            'y': {'micron_per_volt': 7.1759,
                  'min_v': -10.0,
                  'max_v': +10.0,
                  'default': 0.0,
                  'origin': 0.0,
                  'ao_channel': 'ao1'}
        }

        self.ao_smooth_rate = 50000.0  # Hz
        self.ao_smooth_steps_per_volt = 1000.0  # steps/V
        #self.ao_smooth_steps_per_volt = 200.0  # steps/V
        self.count_task = None


        for dim in self.fsm_dimensions:
            chan_name = dim
            phys_chan = self.dev_name + self.fsm_dimensions[dim]['ao_channel']
            V_min = self.fsm_dimensions[dim]['min_v']
            V_max = self.fsm_dimensions[dim]['max_v']

            chan = VoltageOutputChannel(phys_chan, name=chan_name,
                                        min_max=(V_min, V_max), units='volts',
                                        task=self.task)



    def finalize(self):
        """
        Stops AO tasks for controlling FSM.
        """
        #self.task.stop()

    @Feat()
    def abs_position_pair(self):
        x_loc = abs_position_single['x']
        y_loc = abs_position_single['y']
        print('FSM at ({}um,{}um)'.format(x_loc, y_loc))
        return [x_loc, y_loc]

    @abs_position_pair.setter
    def abs_position_pair(self, xy_pos):
        """
        Sets absolute position of scanning mirror, as a micron pair.
        """
        abs_position_single['x'] = xy_pos[0]
        abs_position_single['y'] = xy_pos[1]
        print('Set FSM to ({}um,{}um).'.format(xy_pos[0], xy_pos[1]))
        return 0

    @DictFeat()
    def abs_position_single(self, dimension):
        """
        Returns absolute position of scanning mirror along dimension.
        """
        return 0

    @abs_position_single.setter
    def abs_position_single(self, dimension, pos):
        """
        Sets absolute position of scanning mirror along dimension to be pos.
        """
        return 0

    def convert_V_to_um(self, dim, V):
        """
        Returns micron position corresponding to channel voltage.
        """
        um = V * self.fsm_dimensions[dim]['micron_per_volt'] + (
            self.fsm_dimensions[dim]['origin'])
        return um

    def convert_um_to_V(self, um, dim):
        """
        Returns voltage corresponding to micron position.
        """
        V = (um - self.fsm_dimensions[dim]['origin']) / (
            self.fsm_dimensions[dim]['micron_per_volt'])
        return V

    def set_V_to_zero(self):
        """
        Sets output voltages to 0.
        """
        self.abs_position_pair = (self.convert_V_to_um(0, 'x'),
                                  self.convert_V_to_um(0, 'y'))

    def ao_smooth(self, x_init, x_final, channel):
        """
        Smooths output of DAQ to avoid hysteresis w/ moving FSM mirror.

        Copy of dchristle's algorithm. (I know what you're trying to do, and
        just stop.)
        """

        v_data = self.AO_smooth_func(x_init, x_final, channel)
        n_steps = v_data.size

        samp_arr = np.empty(n_steps * 2, dtype=float)

        if channel == 'x':
            samp_arr[0::2] = v_data
            samp_arr[1::2] = np.zeros(n_steps)
        else:
            samp_arr[0::2] = np.zeros(n_steps)
            samp_arr[1::2] = v_data



        print(samp_arr)
        print(n_steps)

        #samp_arr = 1.5


        self.task.configure_timing_sample_clock(source='OnboardClock', rate=self.ao_smooth_rate,
                                                sample_mode='finite',
                                                samples_per_channel=int(n_steps))

        self.task.write(data=samp_arr, auto_start=False, timeout=0, group_by='scan')


        try:
            self.task.start()
            print('Started FSM Scan')
            print('Expected scan time:{} sec'.format(n_steps*1.0/self.ao_smooth_rate))
            print('Number of scan points:{}'.format(n_steps))
            sleep(n_steps*1.0/self.ao_smooth_rate)
            self.task.stop()

        except:
            print('Failed in counter start phase...')


    def AO_smooth_func(self, x_init, x_final, channel):
        """
        :param x_min: minimum x coordinate (in microns) for scan
        :param x_max: maximum x coordinate (in microns) for scan
        :param channel: channel to scan over (i.e. x or y)

        :return: array of voltages to write
        """

        v_init = self.convert_um_to_V(x_init, channel)
        v_final = self.convert_um_to_V(x_final, channel)

        n_steps = int(ceil(abs(v_final - v_init) * self.ao_smooth_steps_per_volt))

        v_data = v_init * ones(n_steps) + (v_final - v_init) * (1.0 - cos(
            linspace(0.0, pi, n_steps))) / 2.0

        return v_data


    def fsm_line_generator(self, x_min, x_max, y_min, y_max, freq, input_voltage_chan):
        """
        Scan FSM by writing an array of points over analog out

        Args:
        :param ctrchan: (string) device channel for counter
        :param x_min: (float) minimum x position (in microns) for scan
        :param x_max: (float) maximum x position (in microns) for scan
        :param y_min: (float) minimum y position (in microns) for scan
        :param y_max: (float) maximum y position (in microns) for scan
        :param freq: (float) frequency for FSM scan

        :param input_voltage_chan: (str) device channel for analog input voltage to read (i.e. 'dev1/ai0')

        :return: returns a tuple containing two float arrays.
            The first array contains the x-y positions used for the scan.
            The second array contains the counts corresponding to each position.
        """
        v_data, nx_steps, ny_steps = self.generate_2D_scan_array(x_min, x_max, y_min, y_max)

        v_chunks = np.array_split(v_data, ny_steps)

        counts = np.zeros(nx_steps)

        if self.count_task is None:
            self.count_task = AnalogInputTask('voltage')
            counter_channel = VoltageInputChannel(input_voltage_chan)
            self.count_task.add_channel(counter_channel)

        sample_clock = 'OnboardClock'
        self.task.configure_timing_sample_clock(source=sample_clock, rate=freq,
                                                sample_mode='finite',
                                                samples_per_channel=nx_steps)

        self.count_task.configure_timing_sample_clock(source=sample_clock, rate=freq,
                                                sample_mode='finite',
                                                samples_per_channel=nx_steps)
        trigger_src = 'ai/StartTrigger'
        self.task.configure_trigger_digital_edge_start(trigger_src)


        for chunk in v_chunks:
            # Write the array of voltages that will be used to control the DAQ here.
            self.task.write(chunk, auto_start=False, timeout=0, group_by='scan')

            # Synchronize tasks to both start on the AnalogInput start trigger

            # This arms the trigger, thereby starting the AnalogOutputTask (FSM)
            # simultaneously with the AnalogInputTask
            self.task.start()


            scan_time = nx_steps*3.0/freq
            # Executing the read task executes the two tasks synchronously
            t_extra = 0.0 # can add grace period, probably unnecessary
            counts = self.count_task.read(samples_per_channel=nx_steps, timeout=scan_time + t_extra)

            yield np.ndarray.flatten(counts)

            self.task.stop()
            self.count_task.stop()

        return


    def generate_2D_scan_array(self, x_min, x_max, y_min, y_max):
        """
        Generates array of points to write to analog output for x, y channels

        Args:
        :param ctrchan: (string) device channel for counter
        :param x_min: (float) minimum x position (in microns) for scan
        :param x_max: (float) maximum x position (in microns) for scan
        :param y_min: (float) minimum y position (in microns) for scan
        :param y_max: (float) maximum y position (in microns) for scan

        """

        x_voltages = self.AO_smooth_func(x_min, x_max, 'x')
        nx_steps = x_voltages.size
        y_voltages = self.AO_smooth_func(y_min, y_max, 'y')
        ny_steps = y_voltages.size

        x_pts = self.convert_V_to_um('x', x_voltages)
        y_pts = self.convert_V_to_um('y', y_voltages)


        # Create a 2D array of tuples for the xy points in the scan.
        # Note that the AO smooth procedure means these points do not fall on a perfect grid
        # That's why I've calculated them here and returned them to be available to the user.

        # Note: change counts data type to be int, if using edge count APD
        count_tuple = np.dtype([('x', 'float'), ('y', 'float'), ('counts', 'float')])
        xy_pts = np.zeros([nx_steps, ny_steps], dtype=count_tuple)

        # This avoids a nested for loop (if you have large array of points, O(N^2))
        # I assumed that numpy does both of these operations relatively fast...
        xy_pts['x'] = np.tile(x_pts, ny_steps).reshape(nx_steps, ny_steps)
        xy_pts['y'] = np.repeat(y_pts, nx_steps).reshape(nx_steps, ny_steps)

        n_steps = (nx_steps + 1) * ny_steps
        v_data = np.zeros(2*n_steps)

        # Avoids piezo hysteresis by ensuring they always take data scanning in the same direction
        hyst_offset = 0.2 #volts, your MMV with this particular choice
        x_voltages = np.hstack([x_voltages[0] - hyst_offset, x_voltages])

        v_data[0::2] = np.tile(x_voltages, ny_steps) #scan in x repeatedly (x_min to x_max, x_min to x_max, ...)
        v_data[1::2] = np.repeat(y_voltages, nx_steps + 1) #scan in y slowly (y_min, y_min, ..., y_min+1, y_min+1, ..., y_max)


        return v_data, nx_steps, ny_steps


    def FSM_2D_counts(self, x_min, x_max, y_min, y_max, freq, input_voltage_chan):
        """
        Scan FSM by writing an array of points over analog out

        Args:
        :param ctrchan: (string) device channel for counter
        :param x_min: (float) minimum x position (in microns) for scan
        :param x_max: (float) maximum x position (in microns) for scan
        :param y_min: (float) minimum y position (in microns) for scan
        :param y_max: (float) maximum y position (in microns) for scan
        :param freq: (float) frequency for FSM scan

        :param input_voltage_chan: (str) device channel for analog input voltage to read (i.e. 'dev1/ai0')

        :return: returns a tuple containing two float arrays.
            The first array contains the x-y positions used for the scan.
            The second array contains the counts corresponding to each position.
        """

        x_voltages = self.AO_smooth_func(x_min, x_max, 'x')
        nx_steps = x_voltages.size
        y_voltages = self.AO_smooth_func(y_min, y_max, 'y')
        ny_steps = y_voltages.size

        x_pts = self.convert_V_to_um('x', x_voltages)
        y_pts = self.convert_V_to_um('y', y_voltages)


        # Create a 2D array of tuples for the xy points in the scan.
        # Note that the AO smooth procedure means these points do not fall on a perfect grid
        # That's why I've calculated them here and returned them to be available to the user.

        # Note: change counts data type to be int, if using edge count APD
        count_tuple = np.dtype([('x', 'float'), ('y', 'float'), ('counts', 'float')])
        xy_pts = np.zeros([nx_steps, ny_steps], dtype=count_tuple)

        # This avoids a nested for loop (if you have large array of points, O(N^2))
        # I assumed that numpy does both of these operations relatively fast...
        xy_pts['x'] = np.tile(x_pts, ny_steps).reshape(nx_steps, ny_steps)
        xy_pts['y'] = np.repeat(y_pts, nx_steps).reshape(nx_steps, ny_steps)

        n_steps = (nx_steps + 1) * ny_steps
        v_data = np.zeros(2*n_steps)

        # Avoids piezo hysteresis by ensuring they always take data scanning in the same direction
        hyst_offset = 0.2 #volts, your MMV with this particular choice
        x_voltages = np.hstack([x_voltages[0] - hyst_offset, x_voltages])

        v_data[0::2] = np.tile(x_voltages, ny_steps) #scan in x repeatedly (x_min to x_max, x_min to x_max, ...)
        v_data[1::2] = np.repeat(y_voltages, nx_steps + 1) #scan in y slowly (y_min, y_min, ..., y_min+1, y_min+1, ..., y_max)

        counts = np.zeros(n_steps)

        self.count_task = AnalogInputTask('voltage')
        counter_channel = VoltageInputChannel(input_voltage_chan)
        self.count_task.add_channel(counter_channel)


        # Synchronize tasks to both read at a rate, which is controlled by the internal DAQ clock.
        sample_clock = 'OnboardClock'
        self.task.configure_timing_sample_clock(source=sample_clock, rate=freq,
                                                sample_mode='finite',
                                                samples_per_channel=n_steps)

        self.count_task.configure_timing_sample_clock(source=sample_clock, rate=freq,
                                                sample_mode='finite',
                                                samples_per_channel=n_steps)

        # Write the array of voltages that will be used to control the DAQ here.
        self.task.write(v_data, auto_start=False, timeout=0, group_by='scan')

        # Synchronize tasks to both start on the AnalogInput start trigger
        trigger_src = 'ai/StartTrigger'
        self.task.configure_trigger_digital_edge_start(trigger_src)

        # This arms the trigger, thereby starting the AnalogOutputTask (FSM) simultaneously
        # with the AnalogInputTask
        self.task.start()

        print('Tasks configured.')


        try:
            print('Starting FSM Scan...')
            scan_time = n_steps*1.0/freq
            print('Expected scan time:{} sec'.format(scan_time))
            print('Number of scan points:{}'.format(n_steps))
            # Executing the read task executes the two tasks synchronously
            t_extra = 1.0 # adds 1 second grace period, probably unnecessary
            counts = self.count_task.read(samples_per_channel=n_steps, timeout=scan_time + t_extra)

            # Stop both tasks
            self.task.stop()
            self.count_task.stop()

        except:
            print('FSM: 2D Scan Failed in counter start phase.')

        counts = counts.reshape([nx_steps + 1, ny_steps])

        xy_pts['counts'] = counts[1:,:] #drop first column

        print(counts.shape)
        print(xy_pts.shape)

        # This then returns a FSM 2D scan image as a tuple (x_coord, y_coord, counts)
        return counts



        # Burst mode code below

        # Write the array of voltages that will be used to control the DAQ here.
        self.task.write(v_data, auto_start=False, timeout=0, group_by='scan')

        # Synchronize tasks to both start on the AnalogInput start trigger
        trigger_src = 'ai/StartTrigger'
        self.task.configure_trigger_digital_edge_start(trigger_src)

        # This arms the trigger, thereby starting the AnalogOutputTask (FSM) simultaneously
        # with the AnalogInputTask
        self.task.start()

        print('Tasks configured.')


        try:
            print('Starting FSM Scan...')
            scan_time = n_steps*1.0/freq
            print('Expected scan time:{} sec'.format(scan_time))
            print('Number of scan points:{}'.format(n_steps))
            # Executing the read task executes the two tasks synchronously
            t_extra = 1.0 # adds 1 second grace period, probably unnecessary
            counts = self.count_task.read(samples_per_channel=n_steps, timeout=scan_time + t_extra)

            # Stop both tasks
            self.task.stop()
            self.count_task.stop()

        except:
            print('FSM: 2D Scan Failed in counter start phase.')

        counts = counts.reshape([nx_steps + 1, ny_steps])

        xy_pts['counts'] = counts[1:,:] #drop first column

        print(counts.shape)
        print(xy_pts.shape)

        # This then returns a FSM 2D scan image as a tuple (x_coord, y_coord, counts)
        return counts







if __name__ == '__main__':
    with Newport_FSM() as inst:
        print('testing!')
        print('Sweep from -5.0 to 5.0')
        #inst.ao_smooth(-5.0, 5.0, 'x')
            # print('Sweep from 5.0 to -25.0')
            # inst.ao_smooth(5.0, -25.0, 'x')
            # sleep(1)
            # print('Sweep from -25.0 to 25.0')
            # inst.ao_smooth(-25.0, 25.0, 'x')
            # sleep(1)
            # inst.ao_smooth(-5.0, 5.0, 'y')
            # sleep(1)
            # inst.ao_smooth(5.0, -25.0, 'y')
            # sleep(1)
            # inst.ao_smooth(-25.0, 25.0, 'y')
            # sleep(1)

        print('testing 2D count and scan...')
        inst.FSM_2D_counts(-10.0, 10.0, -10.0, 10.0, 50000.0, 'dev1/ai0')

        print('derp derp derp derp!')
