import pymodbus.client as ModbusClient
from pymodbus import Framer, ModbusException


class Drive:
    def __init__(self):
        self.client = ModbusClient.ModbusSerialClient(
            port="COM6",
            framer=Framer.ASCII,
            baudrate=57600,
            bytesize=8,
            parity="O",
            stopbits=1,
        )

        self.position = 0

        self.client.connect()

    def turn_on(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.__set_input(1, 1, rr.registers[0])

    def switch_off(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.__set_input(1, 0, rr.registers[0])

    @property
    def encoder_position(self):
        result = ""
        try:
            rr = self.client.read_holding_registers(1923, 2, slave=1)
            self.position = rr.registers[0]
            result = str(self.position)
        except ModbusException as exc:
            print(f"Received ModbusException({exc}) from library")
        return result

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

        rr = self.client.write_register(508, register, 1)

    def move_to_position(self, position):
        while not self.in_position:
            pass
        self.__set_position(position)
        self.__go_to_position()

    @property
    def in_position(self):
        rr = self.client.read_holding_registers(1549, 1, slave=1)
        return rr.registers[0] == 11
