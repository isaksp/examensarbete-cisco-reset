import serial
import datetime
import threading

ser = serial.Serial('/dev/tty.usbserial-A9ADVK2K', baudrate=9600, timeout=1, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, xonxoff=False)

def Read_from_port(ser):
    line_buffer = ""
    while ser.is_open == True:
        if ser.in_waiting > 0:
            # print(ser.read(ser.in_waiting), end="")
            chunk = ser.read(ser.in_waiting).decode("utf=8",errors = "ignore")
            line_buffer += chunk
            lines = line_buffer.split("\n")
            for line in lines[:-1]:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"{line}")
                with open("log.txt", "a") as f:
                    f.write(f"{timestamp} {line}\n")
            
            line_buffer = lines[-1]

threading.Thread(target=Read_from_port, args=(ser, ), daemon=True).start()


while True:
    # putt = input("\033[F")
    putt = input("")
    if putt == "q".lower():
        ser.send_break(1)
    else:
        ser.write(bytes(str(f"{putt}\r"), 'ISO-8859-1'))
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open("log.txt", "a") as f:
            f.write(f"{timestamp} {putt}\n")
