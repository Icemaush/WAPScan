# WAPScan v1.2 - Created by Reece Pieri and Joseph Micheli, 7/6/19.

# v1.1      - Complete overhaul/restructure of initial code.
# 9/6/19    - Added email functionality. Will send notification email if bandwidth limit is exceeded.
#           - Adjusted email format to display correct information and clearly.
#           - Added input validation for WAP IP address.
#           - Added config file for sensitive information and other variables.
#           - Updated bandwidth rate calculations to report correct values.
#           - Created loop to keep code refreshing data on a set tick rate variable (# of seconds).
#           - Adjusted formatting of data printed to console to be clearer.
#           - Added comments throughout code.

# v1.2      - Added tick counter to track number of ticks/refreshes
# 10/6/19   - Added offender list to store device data if bandwidth limit is exceeded and cancel notification email from
#             being sent if the device is still in the list. This prevents spamming of emails if a device exceeds the
#             bandwidth limit for extended periods of time.
#           - Added user input for bandwidth limit.

# Import modules.
import telnetlib
import re
from Email import Email
import config
import time
import math
import os
import ctypes


# ----- INITIALIZATION CODE ----- #
# Code to run on program startup. WIll run through this once, loop does not include this code.
# Contains variables for tickcounter, tickrate, bandwidth limit and offender release as well as WAP login details.
# Offender list stores IP address and captured tickcounter of devices that exceed bandwidth limit.
class ScanAP(object):
    def __init__(self):
        # WAP login details.
        self.version = 1.2
        self.old_bw_list = []
        self.offender_list = []
        self.tickcounter = 0
        self.tickrate = 3.0
        self.offender_release = 5
        self.username = str("admin").encode('ascii')
        self.password = str("P@ssw0rd").encode('ascii')
        ctypes.windll.kernel32.SetConsoleTitleW("WAPScan v" + str(self.version))
        print("\nWAPScan v" + str(self.version))
        print("-" * 55)
        self.host = input("Enter WAP IP address: ")
        self.bandwidth_limit = float(input("Enter bandwidth limit (Kbps): "))
        config.init()
        self.connect_to_wap()

    # ----- CONNECT TO WAP ----- #
    # Connect to WAP via Telnet and pull connected device information to store in a variable (output_info).
    # Increase tick counter by 1.
    def connect_to_wap(self):
        # Clears console text to refresh data.
        os.system('cls')
        # Try to connect to WAP and collect output data. Closes Telnet connection when finished.
        try:
            if self.password:
                tn = telnetlib.Telnet(self.host)
                tn.read_until(b"Username: ", timeout=3)
                tn.write(self.username + b"\n")
                tn.write(self.password + b"\n")
                tn.write(b"show dot11 associations all-client\n")
                tn.write(b"end\n")
            output = tn.read_until(b"end")
            tn.close()
            self.output_info = output.decode('ascii')

            # If tn.read_until times out after 3 seconds, search output for "Invalid input detected" (indicating user is
            # entering another Cicso device's IP address). If string is detected ask again for WAP IP address.
            if "Invalid input detected" in self.output_info:
                print("Unable to connect. Please enter a valid WAP IP address.")
                self.host = input("Enter WAP IP address: ")
                self.connect_to_wap()
            self.tickcounter += 1
            self.find_data()
        # If IP address is invalid ask again for WAP IP address.
        except:
            print("Unable to connect. Please enter a valid WAP IP address.")
            self.host = input("Enter WAP IP address: ")
            self.connect_to_wap()

    # ----- COLLECT DATA ----- #
    # Parse collected information to search for each device's IP address, MAC address and bandwidth usage.
    def find_data(self):
        # Finds IP addresses in WAP output.
        # As some addresses in output are listed as 0.0.0.0 we search for IP addresses matching the format xx.x.x.x to
        # avoid picking them up.
        ip_a = re.findall(r"\d{2,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", self.output_info)
        self.ip_list = ip_a

        # Find MAC addresses in WAP output.
        self.mac_list = re.findall(r"\w\w\w\w\.\w\w\w\w\.\w\w\w\w", self.output_info)

        # Find "bytes in" and "bytes out" in WAP output.
        self.bandwidth_list = []
        self.new_bw_list = []
        band_in = re.findall(r"Bytes Input {7}: \d{1,7}", self.output_info)
        band_out = re.findall(r"Bytes Output {5}: \d{1,7}", self.output_info)

        # ----- CALCULATES BANDWIDTH RATE ----- #
        # Equation: bytes in + bytes out = total bytes
        #           total bytes / 1000 = total kilobytes
        #           (new Kb - old Kb) / tickrate (in seconds) = bandwidth rate (in Kbps)
        # For each entry in ip_list gather bytes in and bytes out and workout total bytes in, then divide by 1000 to
        # get total Kb value. Add value to new_bw_list.
        count = 0
        for i in self.ip_list:
            bytesin = int(band_in[count].split(": ")[1])
            bytesout = int(band_out[count].split(": ")[1])
            totalbytes = int((bytesin + bytesout) / 1000)
            self.new_bw_list.append(totalbytes)
            count += 1

        # For each entry in ip_list:
        # - If there is an old Kb value to compare to, if old Kb is equal to new Kb, bandwidth will equal 0 Kbps.
        # - Otherwise, if (new Kb - old Kb) / tickrate > bandwidth limit (in Kbps), add value to config.exceeded_list to
        # be emailed. Device IP address and current tickcounter will be added to the offender list. On the next
        # run-through, if the device is still exceeding the bandwidth limit, the program checks the offender list for
        # the device. If the device is in the list, the program will not send another email. Once the device is removed
        # from the list it will be added again and another email will be sent.
        # - If bandwidth < bandwidth limit, add value to bandwidth list to be printed to console.
        count2 = 0
        cap_tick = []
        for i in self.ip_list:
            for offender in self.offender_list:
                if self.tickcounter == offender[1] + 20:
                    self.offender_list.remove(offender)
            cap_tick.append(self.tickcounter)
            if len(self.old_bw_list) == len(self.new_bw_list):
                if self.new_bw_list[count2] == self.old_bw_list[count2]:
                    self.bandwidth = 0
                    self.bandwidth_list.append(str(self.bandwidth) + " Kbps")
                else:
                    if (self.new_bw_list[count2] - self.old_bw_list[count2]) / self.tickrate > self.bandwidth_limit:
                        if len(self.offender_list) > 0:
                            ip = re.findall(r"\d{2,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", str(self.offender_list))
                            if str(self.ip_list[count2]) in ip:
                                self.bandwidth = math.floor((self.new_bw_list[count2] - self.old_bw_list[count2]) /
                                                            self.tickrate)
                                self.bandwidth_list.append(str(self.bandwidth) + " Kbps *")
                                count2 += 1
                                continue
                            else:
                                self.bandwidth = math.floor((self.new_bw_list[count2] - self.old_bw_list[count2]) /
                                                            self.tickrate)
                                self.bandwidth_list.append(str(self.bandwidth) + " Kbps *")
                                badtuple = (str(self.ip_list[count2]), str(self.mac_list[count2]),
                                            str(self.bandwidth_list[count2]))
                                config.exceeded_list.append(badtuple)
                                self.offender_list.append((str(self.ip_list[count2]), cap_tick[0]))
                        if len(self.offender_list) == 0:
                            self.bandwidth = math.floor((self.new_bw_list[count2] - self.old_bw_list[count2]) /
                                                        self.tickrate)
                            self.bandwidth_list.append(str(self.bandwidth) + " Kbps *")
                            badtuple = (str(self.ip_list[count2]), str(self.mac_list[count2]),
                                        str(self.bandwidth_list[count2]))
                            config.exceeded_list.append(badtuple)
                            self.offender_list.append((str(self.ip_list[count2]), cap_tick[0]))
                    else:
                        self.bandwidth = math.floor(
                            (self.new_bw_list[count2] - self.old_bw_list[count2]) / self.tickrate)
                        self.bandwidth_list.append(str(self.bandwidth) + " Kbps")
            else:
                self.bandwidth = 0
                self.bandwidth_list.append(str(self.bandwidth) + " Kbps")
            count2 += 1
        # Holds previous run-through bandwidth values to be compared to new bandwidth values. Resets after calculations.
        self.old_bw_list = []

        # Adds new bandwidth rates to old bandwidth rates list to be compared on next run-through.
        count3 = 0
        for i in self.new_bw_list:
            self.old_bw_list.append(self.new_bw_list[count3])
            count3 += 1
        self.print_to_console()

    # ----- LOOP CODE ----- #
    # Creates delay equal to tickrate variable after first run of code, then repeats.
    def repeat_scan(self):
        time.sleep(self.tickrate)
        self.connect_to_wap()

    # ----- PRINT DATA TO CONSOLE ----- #
    def print_to_console(self):
        print("\nWAPScan v" + str(self.version))
        print("-" * 55)
        print("Number of devices connected: " + str(len(self.ip_list)) + "\n")
        print("IP Address" + "\t" * 2 + "MAC Address" + "\t" * 2 + "Bandwidth Rate")

        # For each entry in ip_list, print data to console.
        count = 0
        for i in self.ip_list:
            print(self.ip_list[count] + "\t" * 2 + self.mac_list[count] + "\t" * 2 + self.bandwidth_list[count])
            count += 1

        # ----- INITIATE SENDING OF NOTIFICATION EMAIL ----- #
        # If config.exceed_list is populated, calls function to send notification email.
        if len(config.exceeded_list) > 1:
            print("\nSending notification email.")
            Email.send_email(self)
        else:
            heading_list = ["IP Address", "MAC Address", "Bandwidth Rate"]
            config.exceeded_list = [tuple(heading_list)]
        self.repeat_scan()


ScanAP()
