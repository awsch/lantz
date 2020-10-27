from lantz import Feat, DictFeat, Action
from lantz.errors import InstrumentError
from lantz.messagebased import MessageBasedDriver

from time import sleep

class CLD1015(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n'
        }
    }

    COM_DELAY = 0.2

    def write(self, *args, **kwargs):
        super().write(*args, **kwargs)
        sleep(self.COM_DELAY)
        return

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    # @Feat()
    # def key_locked(self):
    #     return bool(int(self.query('OUTP:PROT:KEYL:TRIP?')))

    # @Feat(values={'C': 'CEL', 'F': 'FAR', 'K': 'K'})
    # def temperature_unit(self):
    #     self.t_unit = self.query('UNIT:TEMP?')
    #     return self.t_unit

    # @temperature_unit.setter
    # def temperature_unit(self, value):
    #     self.write('UNIT:TEMP {}'.format(value))

    # @Feat()
    # def temperature(self):
    #     return float(self.query('MEAS:SCAL:TEMP?'))

    # @Feat()
    # def temperature_setpoint(self):
    #     return float(self.query('SOUR2:TEMP?'))

    # @Action()
    # def read_error_queue(self):
    #     error = self.query('SYST:ERR:NEXT?')
    #     print(error)
    #     while(not 'No error' in error):
    #         error = self.query('SYST:ERR:NEXT?')
    #         print(error)

    @Feat(values={False: '0', True: '1'})
    def ld_state(self):
        return self.query('OUTP1:STAT?')

    @ld_state.setter
    def ld_state(self, value):
        self.write('OUTP1:STAT {}'.format(value))

    @Feat(units='A')
    def ld_current_setpoint(self):
        return float(self.query('SOUR:CURR?'))

    @Feat(limits=(0.0, 1.2))
    def ld_current(self):
        return float(self.query('MEAS:CURR?'))

    @ld_current.setter
    def ld_current(self, value):
        self.write('SOUR:CURR {:.5f}'.format(value))

    # @DictFeat(units='W', keys={'photodiode', 'pd', 'thermopile', 'tp', 'power meter'})
    # def ld_power(self, method):
    #     query = 'MEAS:POW{}?'
    #     ml = method.lower()
    #     if ml in {'photodiode', 'pd'}:
    #         method_val = 2
    #     elif ml in {'thermopile', 'tp', 'power meter'}:
    #         method_val = 3
    #     return float(self.query(query.format(method_val)))

    @Feat(values={False: '0', True: '1'})
    def tec_state(self):
        return self.query('OUTP2:STAT?')

    @tec_state.setter
    def tec_state(self, value):
        self.write('OUTP2:STAT {}'.format(value))

    @Action()
    def on(self):
        if self.tec_state:
            self.ld_state = 1
        else:
            return("error: temperature controller not on")
        # tol = 0.15 # This is the tolerance in C we wait to achieve
        # # logging.debug(__name__ + ' : turning laser on using shortcut on function')
        # self.tec_state = 1
        # tempSP = self.temperature_setpoint
        # sleep(1)
        # total_time = 0
        # within = 0
        # while within < 3: # Achieve tolerance for three seconds
        #     current_temp = self.temperature
        #     ## print 'Current temp %s' % current_temp
        #     if abs(current_temp-tempSP) < tol:
        #         within = within + 1
        #     else:
        #         within = 0
        #     sleep(1)
        #     total_time = total_time + 1
        #     # if total_time > 20:
        #     #     logging.error(__name__ + ' : did not achieve setpoint within 20 s, breaking')
        #     #     break

        # # now set the laser on
        # if total_time < 20:
        #     self.ld_state = 1
            # total_time = 0
            # within = 0
            # while within < 5: # Achieve tolerance for 5 seconds
            #     current_temp = self.do_get_temperature()
            #     ## print 'Current temp %s' % current_temp
            #     if abs(current_temp-tempSP) < tol:
            #       within = within + 1
            #     else:
            #      within = 0
            #     qt.msleep(1)
            #     total_time = total_time + 1
            #     if total_time > 20:
            #       logging.error(__name__ + ' : did not achieve setpoint within 20 s, breaking')
            #       self.set_source_status(0)
            #       qt.msleep(5)
            #       self.set_TEC_status(0)
            #       break
        # return

    @Action()
    def off(self):
        self.ld_state=0
        # sleep(5)
        # self.tec_state = 0
        # return

    # @Feat(values={False: '0', True: '1'})
    # def am_state(self):
    #     return self.query(':AM:STAT?')

    # @am_state.setter
    # def am_state(self, value):
    #     self.write(':AM:STAT {}'.format(value))

    # @Feat(values={'Internal', 'External'})
    # def am_source(self):
    #     return self.query(':AM:SOUR?')

    # @am_source.setter
    # def am_source(self, value):
    #     self.write(':AM:SOUR {}'.format(value))


if __name__ == '__main__':
    import logging
    import sys
    from lantz.log import log_to_screen
    log_to_screen(logging.CRITICAL)
    res_name = sys.argv[1]
    fmt_str = "{:<30}|{:>30}"
    on_time = 20
    # with ITC4020(res_name) as inst:
    #     print(fmt_str.format("Temperature unit", inst.temperature_unit))
    #     print(fmt_str.format("Device name", inst.query('*IDN?')))
    #     print(fmt_str.format("LD state", inst.ld_state))
    #     print(fmt_str.format("TEC state", inst.tec_state))
    #     print("Turning on TEC and LD...")
    #     inst.tec_state = True
    #     inst.ld_state = True
    #     print(fmt_str.format("LD power (via photodiode)", inst.ld_power['pd']))
    #     print(fmt_str.format("LD power (via thermopile)", inst.ld_power['tp']))
    #     print(fmt_str.format("LD state", inst.ld_state))
    #     print(fmt_str.format("TEC state", inst.tec_state))
    #     print(fmt_str.format("LD temperature", inst.temperature))
    #     print(fmt_str.format("LD power (via photodiode)", inst.ld_power['pd']))
    #     print(fmt_str.format("LD power (via thermopile)", inst.ld_power['tp']))
    #     sleep(on_time)
    #     print("Turning off TEC and LD...")
    #     inst.tec_state = False
    #     inst.ld_state = False
    #     print(fmt_str.format("LD state", inst.ld_state))
    #     print(fmt_str.format("TEC state", inst.tec_state))
