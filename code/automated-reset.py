import serial
import datetime
import threading
import time

ser = serial.Serial('/dev/tty.usbserial-A9ADPXH5', baudrate=9600, timeout=1, parity=serial.PARITY_NONE, bytesize=8, stopbits=serial.STOPBITS_ONE, xonxoff=False)

def Read_from_port(ser,rommon_event ,image_event, prompt_event,multilayer_event , switch_break_event, l2l3_old_event, flash_init_event, read_only_prompt_event, test_prompt):
    line_buffer = ""
    while ser.is_open == True:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode("utf-8",errors = "ignore")
            line_buffer += chunk
            lines = line_buffer.split("\n")
            for line in lines[:-1]:
                
                #Checks if the router has entered rommon
                if "rommon" in line:
                    rommon_event.set()

                #Checks when break should be sent to router
                if "Rom image verified correctly" in line:
                    image_event.set()

                #Checks when break should be sent to Switch
                if "Send break" in line:
                    switch_break_event.set()
                
                #ML Switch? 
                if "(interrupted)" in line or "(Aborted)" in line:
                    multilayer_event.set()
                
                #Answears the yes no prompt
                if "Press RETURN to get started!" in line:
                    prompt_event.set()
                
                #black l2/l3 switch
                if "The system has been interrupted" in line:
                    l2l3_old_event.set()

                #Initiazling flash on black switches l2/l3
                if "...done Initializing Flash." in line:
                    flash_init_event.set()
                
                #Checks if read only
                if "read only file system" in line:
                    read_only_prompt_event.set()

                #Makes sure it can write to the switch
                if "test" in line:
                    test_prompt.set()

                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"{timestamp} {line}")
            
                with open("log.txt", "a") as f:
                    f.write(f"{timestamp} {line}\n")

            line_buffer = lines[-1]

test_reached = threading.Event()
read_only_prompt_reached = threading.Event()
switch_break_reached = threading.Event()
prompt_reached = threading.Event()
image_reached = threading.Event()
rommon_reached = threading.Event()
multilayer_reached = threading.Event()
l2l3_old_reached = threading.Event()
flash_init_reached = threading.Event()
threading.Thread(target=Read_from_port, args=(ser, rommon_reached, image_reached, prompt_reached, multilayer_reached, switch_break_reached, l2l3_old_reached, flash_init_reached, read_only_prompt_reached, test_reached), daemon=True).start()

while True:
    if switch_break_reached.is_set():
        ser.write(bytes(str(f"{ser.send_break()}\r"), "ISO-8859-1"))
        break
    elif image_reached.is_set():
        ser.write(bytes(str(f"{ser.send_break()}\r"), "ISO-8859-1"))
        if rommon_reached.is_set(): break
    elif multilayer_reached.is_set(): break
    elif l2l3_old_reached.is_set(): break

if switch_break_reached.is_set():
    time.sleep(1)
    ser.write(bytes(str(f"delete flash:config.text"), 'ISO-8859-1\r\n'))
    time.sleep(1)
    ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"delete flash:vlan.dat\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))

elif multilayer_reached.is_set():
    time.sleep(1)
    ser.write(bytes(str(f"SWITCH_IGNORE_STARTUP_CFG=1"), 'ISO-8859-1\r'))
    time.sleep(1)
    ser.write(bytes(str(f"\r"), 'ISO-8859-1\r'))
    time.sleep(1)
    ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"\r"), 'ISO-8859-1\r'))

elif l2l3_old_reached.is_set():
    time.sleep(1)
    ser.write(bytes(str(f"flash_init\r"), 'ISO-8859-1'))
    while not flash_init_reached.is_set():
        # time.sleep(5)
        # ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        if flash_init_reached.is_set(): break
    
    while True:
        time.sleep(1)
        ser.write(bytes(str(f"test\r"), 'ISO-8859-1'))
        if test_reached.is_set(): break
    
    time.sleep(1)
    ser.write(bytes(str(f"delete flash:config.text\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))
    time.sleep(1)

    if read_only_prompt_reached.is_set():
        time.sleep(1)
        ser.write(bytes(str(f"SWITCH_IGNORE_STARTUP_CFG=1"), 'ISO-8859-1\r'))
        time.sleep(1)
        ser.write(bytes(str(f"\r"), 'ISO-8859-1\r'))
        time.sleep(1)
        ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))
        time.sleep(1)
        ser.write(bytes(str(f"\r"), 'ISO-8859-1\r'))
    
    else:
        ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))
        time.sleep(1)
        ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))

else:
    ser.write(bytes(str(f"confreg 0x2142\r"), 'ISO-8859-1'))
    ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))

while True:

    if prompt_reached.is_set() and multilayer_reached.is_set() or prompt_reached.is_set() and l2l3_old_reached.is_set() and read_only_prompt_reached.is_set():
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"en\r"), 'ISO-8859-1'))
        time.sleep(1)
        ser.write(bytes(str(f"erase startup-config\r"), 'ISO-8859-1'))
        time.sleep(1)
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        time.sleep(1)
        ser.write(bytes(str(f"config t\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"no system ignore startupconfig switch all\r"), 'ISO-8859-1'))
        break

    elif prompt_reached.is_set() and switch_break_reached.is_set() or prompt_reached.is_set() and l2l3_old_reached.is_set() and not read_only_prompt_reached.is_set():
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"no\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        break

    elif prompt_reached.is_set() and rommon_reached.is_set():
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"en\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"erase startup-config\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"conf t\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"config-register 0x2102\r"), 'ISO-8859-1'))
        break

while True:
    ser.write(bytes(str(f"{input()}\r"), 'ISO-8859-1'))
