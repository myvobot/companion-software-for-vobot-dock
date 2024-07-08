import re
import json
import time
import socket
import threading
import udp_server
from stats import *
import tkinter as tk
from tkinter import messagebox


def is_valid_ip(ip):
    # Regular expression pattern for IP address
    pattern = r'^((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))$'

    # Match the pattern using the match() method from re module
    if re.match(pattern, ip):
        # IP address format is valid
        return True
    else:
        # IP address format is invalid
        return False

def get_cpu_info():
    return {
        "usage": CPU.percentage(), # CPU usage
        "temperature": CPU.temperature() # CPU temperature
    }

def get_gpu_info():
    info = Gpu.stats()
    return {
        "usage": info[0], # GPU usage
        "temperature": info[1] # GPU temperature
    }

def get_memory_info():
    info = Memory.stats()
    return {
        "swap": info[0], # Percentage of current system swap space usage
        "usage": info[3], # Percentage of current system memory usag
        "free": info[2], # Available memory amount in the current system
        "used": info[1], # Used memory amount in the current system
    }

def get_disk_info():
    info = Disk.stats()
    return {
        "usage": info[3], # Disk usage
        "total": info[2], # Total size of the disk
        "used": info[0], # Used size of the disk
        "free": info[1] # Available size of the disk
    }

class GUI:

    def __init__(self):
        self.T = None
        self.device_ip = ""
        self.root = tk.Tk()
        self.root.title('Computer Monitor')
        self.running = False
        self.initial_interface()

    def initial_interface(self):
        # Initial interface
        self.root.geometry("320x120")
        self.root.resizable(False, False)

        label = tk.Label(self.root, text="Device IP:", anchor="center")
        label.place(x=20, y=21, width=80, height=30)

        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.place(x=100, y=21, width=198, height=30)

        btn = tk.Button(self.root, text="Start", takefocus=False, command=self.start)
        btn.place(x=19, y=74, width=70, height=25)

        btn = tk.Button(self.root, text="Clear", takefocus=False, command=lambda: self.ip_entry.delete(0,tk.END))
        btn.place(x=228, y=74, width=70, height=25)

    def run_interface(self):
        # Interface during runtime
        self.root.geometry("600x190")
        self.root.resizable(False, False)

        self.log_text = tk.Text(self.root)
        self.log_text.place(x=0, y=0, width=600, height=143)
        self.log_text.bind("<KeyPress>", lambda e: "break")
        self.log_text.insert(1.0, f'device IP:{self.device_ip}' + '\n')

        btn = tk.Button(self.root, text="Stop", takefocus=False, command=self.stop)
        btn.place(x=260, y=161, width=80, height=25)

    def win_clean(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def broadcast(self):
        udp_server.init()
        while self.running:
            try:
                text = ""
                try:
                    device_info = {
                        "NET": Net.stats(),
                        "CPU": get_cpu_info(),
                        "GPU": get_gpu_info(),
                        "Memory": get_memory_info(),
                        "Disk": get_disk_info(),
                        "dev_ip": self.device_ip,
                        "IP": socket.gethostbyname(socket.gethostname())
                    }
                    udp_server.send(bytes(json.dumps(device_info), 'utf-8'))
                    text = f"Successfully sent."
                except Exception as e:
                    text = "fail in send[" + str(e) + "]."

                try:
                    self.log_text.insert(1.0, f'{text}' + '\n')
                except: pass

                time.sleep(5)
            except RuntimeError:
                break
        self.T = None

    def start(self):
        self.device_ip = self.ip_entry.get()
        if is_valid_ip(self.device_ip):
            udp_server.unicast_ip = self.device_ip
            self.win_clean()
            self.running = True
            self.run_interface()
            if self.T is None:
                self.T = threading.Thread(target=self.broadcast)
                self.T.start()
        else:
            self.ip_entry.delete(0,tk.END)
            messagebox.showwarning("Invalid IP", "IP format error, please try again")

    def stop(self):
        self.running = False
        self.win_clean()
        self.initial_interface()
        self.ip_entry.insert(0, self.device_ip)

if __name__ == '__main__':
    gui = GUI()
    gui.root.mainloop()