import pymodbus.client as ModbusClient
from pymodbus import Framer, ModbusException


class Drive:
    def __init__(self, port="COM8", framer=Framer.ASCII, baudrate=57600, bytesize=8, parity="O", stopbits=1):
        self.client = ModbusClient.ModbusSerialClient(
            port,
            framer,
            baudrate,
            bytesize,
            parity,
            stopbits,
            strict=False
        )

        self._position = -1

    def connected(self):
        if self.client.connected:
            return True
        try:
            self.client.connect()
            self.turn_on()
            return True
        except:
            return False

    def turn_on(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.__set_input(1, 1, rr.registers[0])

    def switch_off(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.__set_input(1, 0, rr.registers[0])

    @property
    def encoder_position(self):
        try:
            rr = self.client.read_holding_registers(1923, 2, slave=1)
            self._position = (rr.registers[1] << 16) + rr.registers[0]
            return self._position
        except:
            print("Позиция привода не получена")
            return -1

    def __set_position(self, position):
        if position < 0:
            position = 0xFFFFFFFF + position + 1
        position701 = position & 0xFFFF
        position702 = (position >> 16) & 0xFFFF

        self.client.write_register(701, position701, 1)
        self.client.write_register(702, position702, 1)

    def __go_to_position(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.__set_input(3, 0, rr.registers[0])
        self.__set_input(3, 1, rr.registers[0])

    def __set_input(self, inp_number, inp_value, register):
        tmp = 1 << ((inp_number - 1) * 4)
        if inp_value:
            register = register | tmp
        else:
            tmp = ~tmp
            register = register & tmp

        self.client.write_register(508, register, 1)

    def move_to_position(self, position):
        self.__set_position(position)
        self.__go_to_position()

    @property
    def in_position(self):
        rr = self.client.read_holding_registers(1549, 1, slave=1)
        try:
            return rr.registers[0] == 11
        except:
            pass

    def change_speed(self, speed):
        self.client.write_register(733, speed, 1)
