from lantz.driver import Driver
from lantz import Feat, DictFeat, Action

import socket

class Cryostation(Driver):


    def __init__(self, address, port=7773, timeout=20.0):
        super().__init__()
        self.address = address
        self.port = port

    def initialize(self):
        """
        Initialize function for Cryostation communication port, uses Python
        sockets library to open socket communication with Cryostation.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.address, self.port))
        self.socket.settimeout(2)

    def finalize(self):
        """
        Closes socket communication with Cryostation software.
        """
        self.socket.close()

    @Feat()
    def alarm_state(self):
        """
        Returns true or false, indicating the presence (T) or absence (F) of
        a system error.
        """
        return self.send_and_recv('GAS')

    @Feat()
    def chamber_pressure(self):
        """
        Returns the chamber pressure in mTorr, or -0.1 if the pressure is
        unavailable.
        """
        return float(self.send_and_recv('GCP'))

    @Feat()
    def platform_temperature(self):
        """
        Returns the current platform temperature in K, or -0.100 if the current
        temperature is unavailable.
        """
        return float(self.send_and_recv('GPT'))

    @Feat()
    def platform_stability(self):
        """
        Returns the platform stability in K, or -0.100 if unavailable.
        """
        return float(self.send_and_recv('GPS'))

    @Feat()
    def platform_heater_pow(self):
        """
        Returns the current platform heater power in W, or -0.100 if
        unavailable.
        """
        return float(self.send_and_recv('GPHP'))

    @Feat()
    def stage_1_temperature(self):
        """
        Returns the current stage 1 temperature in K, or -0.100 if the current
        temperature is unavailable.
        """
        return float(self.send_and_recv('GS1T'))

    @Feat()
    def stage_1_heater_pow(self):
        """
        Returns the current stage 1 heater power in W, or -0.100 if
        unavailable.
        """
        return float(self.send_and_recv('GS1HP'))

    @Feat()
    def stage_2_temperature(self):
        """
        Returns the current stage 2 temperature in K, or -0.100 if the current
        temperature is unavailable.
        """
        return float(self.send_and_recv('GS2T'))

    @Feat()
    def sample_stability(self):
        """
        Returns the sample stability in K, or -0.100 if unavailable.
        """
        return float(self.send_and_recv('GSS'))

    @Feat()
    def sample_temperature(self):
        """
        Returns the sample temperature in K, or -0.100 if unavailable.
        """
        return float(self.send_and_recv('GST'))

    @Feat()
    def temp_set_point(self):
        """
        Returns the temperature setpoint of the Cryostation software.
        """
        return float(self.send_and_recv('GTSP'))

    @temp_set_point.setter
    def temp_set_point(self, setpoint_kelvin):
        """
        Sets the temperature setpoint of the Cryostation software.
        """
        return self.send_and_recv('STSP{0:.2f}'.format(setpoint_kelvin))

    @Feat()
    def user_temperature(self):
        """
        Returns the user thermometer temperature in K, or -0.100 if unavailable.
        """
        return float(self.send_and_recv('GUT'))

    @Feat()
    def user_stability(self):
        """
        Returns the user thermometer stability in K, or -0.100 if unavailable.
        """
        return float(self.send_and_recv('GUS'))

    @Action()
    def start_cool_down(self):
        """
        Initializes cooldown to temperature setpoint.
        """
        return self.send_and_recv('SCD')

    @Action()
    def start_standby(self):
        """
        Puts the system into standby mode (see manual for details).
        """
        return self.send_and_recv('SSB')

    @Feat()
    def SToP(self):
        """
        Returns the status of the last command.

        If OK, the system cannot stop at this time.
        """
        return self.send_and_recv('STP')

    @Action()
    def start_warm_up(self):
        """
        Starts the system warmup to room temperature.
        """
        return self.send_and_recv('SWU')

    def send_and_recv(self, message):
        """
        Params:
            message = command to be sent to Cryostation
            return_bytes = number of bytes to be stripped off return string
        """
        buffer_size = 1024
        m1 = '0{}{}'.format(str(len(message)), message)

        self.socket.send(m1.encode())
        data = str()
        message = self.socket.recv(buffer_size)
        if message:
            data = message.decode()

        return data[2:]

def main():

    address = '192.168.1.100'
    port = 7773

    with Cryostation(address, port) as inst:
        print('Alarm state: {}'.format(inst.alarm_state))
        print('Chamber pressure: {}mTorr'.format(inst.chamber_pressure))

        print('Temperature and stabiity metrics')

        print('Platform temperature: {}K'.format(inst.platform_temperature))
        print('Platform stability: {}K'.format(inst.platform_stability))
        print('Stage 1 temperature: {}K'.format(inst.stage_1_temperature))
        print('Stage 2 temperature: {}K'.format(inst.stage_2_temperature))

        print('Sample temperature :{}K'.format(inst.sample_temperature))
        print('Sample stabiity: {}K'.format(inst.sample_stability))

        print('User temperature: {}K'.format(inst.sample_temperature))
        print('User stabiity: {}K'.format(inst.sample_stability))

        print('Heater metrics')
        print('Platform heater power: {}W'.format(inst.platform_heater_pow))
        print('Stage 1 heater power: {}W'.format(inst.stage_1_heater_pow))

        print('Testing temperature set point...')
        print('System set point: {}K'.format(inst.temp_set_point))
        inst.temp_set_point = 20.0
        print('System set point: {}K'.format(inst.temp_set_point))
        inst.temp_set_point = 3.2
        print('System set point: {}K'.format(inst.temp_set_point))

        print('Test system actions')
        print('Starting cooldown?: {}'.format(inst.start_cool_down()))
        print('Starting standby?: {}'.format(inst.start_standby()))
        print('Starting warmup?: {}'.format(inst.start_warm_up()))




if __name__ == '__main__':
    main()
