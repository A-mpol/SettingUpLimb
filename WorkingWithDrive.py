import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    Framer,
    ModbusException,
    pymodbus_apply_logging_config,
)


class Drive:
    def __init__(self, port="COM6", comm="serial", framer=Framer.ASCII):
        self.client = ModbusClient.ModbusSerialClient(
            port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,
            # strict=True,
            baudrate=57600,
            bytesize=8,
            parity="O",
            stopbits=1,
            # handle_local_echo=False,
        )

    def turn_on(self):
        self.client.connect()
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.set_input(1, 1, rr.registers[0])

    def switch_off(self):
        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.set_input(1, 0, rr.registers[0])
        self.client.close()

    def set_position(self, position):
        if position < 0:
            position = 0xFFFFFFFF + position + 1
        position701 = position & 0xFFFF
        position702 = (position >> 16) & 0xFFFF

        self.client.write_register(701, position701, 1)
        self.client.write_register(702, position702, 1)

        rr = self.client.read_holding_registers(508, 1, slave=1)
        self.set_input(3, 0, rr.registers[0])
        self.set_input(3, 1, rr.registers[0])

    def set_input(self, inp_number, inp_value, register):
        tmp = 1 << ((inp_number - 1) * 4)
        if inp_value:
            register = register | tmp
        else:
            tmp = ~tmp
            register = register & tmp

        self.client.write_register(508, register, 1)
