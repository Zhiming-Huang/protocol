import src


if ConnectionCreate(connectiontype, address):
    print("connected")

    if Data_transmission(controltype, address):
        print("transmit finished")

        if connection_close(connectiontype, address):
            print("Disconnected")