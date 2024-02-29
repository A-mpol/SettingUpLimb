def set_input(inp_number, inp_value):
    register = read_register(adress)

    tmp = 1 << ((inp_number - 1) * 4)
    if inp_value:
        register = register | tmp
    else:
        tmp = ~tmp
        register = register & tmp

    write_register(adress, register)

