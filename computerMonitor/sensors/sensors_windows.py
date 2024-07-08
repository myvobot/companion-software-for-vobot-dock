import sys
import math
import mmap
import psutil
from win32api import *
import xml.etree.ElementTree as xml_tree
import clr  # Clr is from pythonnet package. Do not install clr package

def _read_data_with_aida64(length):
    with mmap.mmap(-1, length, tagname="AIDA64_SensorValues", access=mmap.ACCESS_READ) as mm:
        return mm.read()

def _decode(b):
    for encoding in (sys.getdefaultencoding(), "utf-8", "gbk"):
        try:
            return b.decode(encoding=encoding)
        except UnicodeDecodeError: pass
    return b.decode()

def _get_xml_data():
    # The size of the shared memory block is unknown.
    # When the length is too long, a permissionError will be thrown.
    # When the length is too short, the complete data cannot be obtained.
    # Therefore, the binary search method is used to find the length that does not throw an exception.
    buffer_size_options = [100 * i for i in range(10, 120)]  # ranges in [1k, 12k]
    low = 0
    high = len(buffer_size_options) - 1

    while low < high:
        mid = (low + high) // 2
        try:
            length = buffer_size_options[mid]
            data = _read_data_with_aida64(length)
            if data[-1] == 0:
                decoded = _decode(data.rstrip(b"\x00"))
                return f"<root>{decoded}</root>"
            else:
                low = mid
        except PermissionError:
            high = mid

def _get_data():
    data = {}
    data_tree = xml_tree.fromstring(_get_xml_data())

    for item in data_tree:
        if item.tag not in data: data[item.tag] = {}
        data[item.tag][item.find("label").text] = {
            "id": item.find("id").text,
            "value": item.find("value").text
        }
    return data


####################################################
# Import LibreHardwareMonitor dll to Python
lhm_dll = './external/LibreHardwareMonitor/LibreHardwareMonitorLib'
# noinspection PyUnresolvedReferences
clr.AddReference(lhm_dll)
# noinspection PyUnresolvedReferences
clr.AddReference('./external/LibreHardwareMonitor/HidSharp')
# noinspection PyUnresolvedReferences
from LibreHardwareMonitor import Hardware
File_information = GetFileVersionInfo('external/LibreHardwareMonitor/LibreHardwareMonitorLib.dll', "\\")

ms_file_version = File_information['FileVersionMS']
ls_file_version = File_information['FileVersionLS']

print("Found LibreHardwareMonitorLib %s" % ".".join([str(HIWORD(ms_file_version)), str(LOWORD(ms_file_version)),
                                                            str(HIWORD(ls_file_version)),
                                                            str(LOWORD(ls_file_version))]))
net_io = []

handle = Hardware.Computer()
handle.IsCpuEnabled = True
handle.IsGpuEnabled = True
handle.IsMemoryEnabled = True
handle.IsMotherboardEnabled = False
handle.IsControllerEnabled = False
handle.IsNetworkEnabled = True
handle.IsStorageEnabled = True
handle.Open()
for hardware in handle.Hardware:
    if hardware.HardwareType == Hardware.HardwareType.Cpu:
        print("Found CPU: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.Memory:
        print("Found Memory: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.GpuNvidia:
        print("Found Nvidia GPU: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.GpuAmd:
        print("Found AMD GPU: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.GpuIntel:
        print("Found Intel GPU: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.Storage:
        print("Found Storage: %s" % hardware.Name)
    elif hardware.HardwareType == Hardware.HardwareType.Network:
        net_io.append(hardware.Name)
        print("Found Network interface: %s" % hardware.Name)

def get_hw_and_update(hwtype, name = None):
    for hardware in handle.Hardware:
        if hardware.HardwareType == hwtype:
            if (name and hardware.Name == name) or not name:
                hardware.Update()
                return hardware
    return None

def get_net_interface_and_update(if_name):
    for hardware in handle.Hardware:
        if hardware.HardwareType == Hardware.HardwareType.Network and hardware.Name == if_name:
            hardware.Update()
            return hardware

    print("Network interface '%s' not found. Check names in config.yaml." % if_name)
    return None

def get_gpu_name():
    # Determine which GPU to use, in case there are multiple : try to avoid using discrete GPU for stats
    hw_gpus = []
    for hardware in handle.Hardware:
        if hardware.HardwareType == Hardware.HardwareType.GpuNvidia \
                or hardware.HardwareType == Hardware.HardwareType.GpuAmd \
                or hardware.HardwareType == Hardware.HardwareType.GpuIntel:
            hw_gpus.append(hardware)

    if len(hw_gpus) == 0:
        # No supported GPU found on the system
        print("No supported GPU found")
        return ""
    elif len(hw_gpus) == 1:
        # Found one supported GPU
        print("Found one supported GPU: %s" % hw_gpus[0].Name)
        return str(hw_gpus[0].Name)
    else:
        # Found multiple GPUs, try to determine which one to use
        amd_gpus = 0
        intel_gpus = 0
        nvidia_gpus = 0

        gpu_to_use = ""

        # Count GPUs by manufacturer
        for gpu in hw_gpus:
            if gpu.HardwareType == Hardware.HardwareType.GpuAmd:
                amd_gpus += 1
            elif gpu.HardwareType == Hardware.HardwareType.GpuIntel:
                intel_gpus += 1
            elif gpu.HardwareType == Hardware.HardwareType.GpuNvidia:
                nvidia_gpus += 1

        print("Found %d GPUs on your system (%d AMD / %d Nvidia / %d Intel). Auto identify which GPU to use." % (
            len(hw_gpus), amd_gpus, nvidia_gpus, intel_gpus))

        if nvidia_gpus >= 1:
            # One (or more) Nvidia GPU: use first available for stats
            gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuNvidia).Name
        elif amd_gpus == 1:
            # No Nvidia GPU, only one AMD GPU: use it
            gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuAmd).Name
        elif amd_gpus > 1:
            # No Nvidia GPU, several AMD GPUs found: try to use the real GPU but not the APU integrated in CPU
            for gpu in hw_gpus:
                if gpu.HardwareType == Hardware.HardwareType.GpuAmd:
                    for sensor in gpu.Sensors:
                        if sensor.SensorType == Hardware.SensorType.Load and str(sensor.Name).startswith("GPU Core"):
                            # Found load sensor for this GPU: assume it is main GPU and use it for stats
                            gpu_to_use = gpu.Name
        else:
            # No AMD or Nvidia GPU: there are several Intel GPUs, use first available for stats
            gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuIntel).Name

        if gpu_to_use:
            print("This GPU will be used for stats: %s" % gpu_to_use)
        else:
            print("No supported GPU found (no GPU with load sensor)")

        return gpu_to_use
gpu_name = get_gpu_name()

####################################################
class Cpu:
    @staticmethod
    def percentage(interval):
        # Attempting to retrieve data from AIDA64
        percent = _get_data().get("sys", {}).get("CPU Utilization", {}).get("value", math.nan)

        if percent is math.nan:
            cpu = get_hw_and_update(Hardware.HardwareType.Cpu)
            for sensor in cpu.Sensors:
                if sensor.SensorType == Hardware.SensorType.Load and str(sensor.Name).startswith("CPU Total"):
                    percent = float(sensor.Value)
        return (int(percent), "%")


    @staticmethod
    def temperature():
        # Attempting to retrieve data from AIDA64
        temp = _get_data().get("temp", {}).get("CPU Package", {}).get("value", math.nan)

        if temp is math.nan:
            cpu = get_hw_and_update(Hardware.HardwareType.Cpu)
            # By default, the average temperature of all CPU cores will be used
            for sensor in cpu.Sensors:
                if sensor.SensorType == Hardware.SensorType.Temperature and str(sensor.Name).startswith("Core Average"):
                    temp = float(sensor.Value)

            # If not available, the max core temperature will be used
            for sensor in cpu.Sensors:
                if temp is not math.nan: break
                if sensor.SensorType == Hardware.SensorType.Temperature and str(sensor.Name).startswith("Core Max"):
                    temp = float(sensor.Value)

            # If not available, the CPU Package temperature (usually same as max core temperature) will be used
            for sensor in cpu.Sensors:
                if temp is not math.nan: break
                if sensor.SensorType == Hardware.SensorType.Temperature and str(sensor.Name).startswith("CPU Package"):
                    temp = float(sensor.Value)

            # Otherwise any sensor named "Core..." will be used
            for sensor in cpu.Sensors:
                if temp is not math.nan: break
                if sensor.SensorType == Hardware.SensorType.Temperature and str(sensor.Name).startswith("Core"):
                    temp = float(sensor.Value)

        return (int(temp), "°")

class Gpu:
    @staticmethod
    def get_stats_LHM():
        gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuAmd, gpu_name)
        if gpu_to_use is None:
            gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuNvidia, gpu_name)
        if gpu_to_use is None:
            gpu_to_use = get_hw_and_update(Hardware.HardwareType.GpuIntel, gpu_name)
        if gpu_to_use is None:
            # GPU not supported
            return math.nan, math.nan

        used_mem = math.nan
        total_mem = math.nan
        temp = math.nan

        for sensor in gpu_to_use.Sensors:
            if sensor.SensorType == Hardware.SensorType.SmallData and str(sensor.Name).startswith("GPU Memory Used"):
                used_mem = float(sensor.Value)
            elif sensor.SensorType == Hardware.SensorType.SmallData and str(sensor.Name).startswith("D3D Dedicated Memory Used") and math.isnan(used_mem):
                # Only use D3D memory usage if global "GPU Memory Used" sensor is not available, because it is less
                # precise and does not cover the entire GPU: https://www.hwinfo.com/forum/threads/what-is-d3d-usage.759/
                used_mem = float(sensor.Value)
            elif sensor.SensorType == Hardware.SensorType.SmallData and str(sensor.Name).startswith("GPU Memory Total"):
                total_mem = float(sensor.Value)
            elif sensor.SensorType == Hardware.SensorType.Temperature and str(sensor.Name).startswith("GPU Core"):
                temp = float(sensor.Value)

        return (used_mem / total_mem * 100.0), temp

    @staticmethod
    def stats():
        # Attempting to retrieve data from AIDA64
        data = _get_data()
        gpu_info = {}
        for label, info in data.get("temp", {}).items():
            if not label.startswith("GPU"): continue
            title = label.split(" ")[0]
            if label == title + " Diode":
                if title not in gpu_info:
                    gpu_info[title] = {}
                gpu_info[title]["diode"] = info.get("value", math.nan)
                gpu_info[title]["utilization"] = data.get("sys", {}).get(title + " Utilization", {}).get("value", math.nan)
            elif label == title + " Hotspot":
                if title not in gpu_info:
                    gpu_info[title] = {}
                gpu_info[title]["hotspot"] = info.get("value", math.nan)
                gpu_info[title]["utilization"] = data.get("sys", {}).get(title + " Utilization", {}).get("value", math.nan)

        gpu_temp = math.nan
        gpu_usage = math.nan
        gpu_diode = math.nan
        gpu_hotspot = math.nan

        if gpu_info:
            for attr in gpu_info.values():
                gpu_diode = attr.get("diode", math.nan)
                gpu_diode = gpu_diode if gpu_diode != "TRIAL" else math.nan
                gpu_hotspot = attr.get("hotspot", math.nan)
                gpu_hotspot = gpu_hotspot if gpu_hotspot != "TRIAL" else math.nan
                gpu_usage = attr.get("utilization", math.nan)
                gpu_usage = gpu_usage if gpu_usage != "TRIAL" else math.nan
                if gpu_diode is not math.nan and gpu_usage is not math.nan:
                    break

            gpu_temp = gpu_diode if gpu_diode is not math.nan else gpu_hotspot
        else:
            gpu_usage, gpu_temp = Gpu.get_stats_LHM()

        try:
            gpu_usage = int(gpu_usage)
        except:
            gpu_usage = "-"

        try:
            gpu_temp = int(gpu_temp)
        except:
            gpu_temp = "-"

        return ((gpu_usage, "%"), (gpu_temp, "°"))


class Memory:
    @staticmethod
    def swap_percent():
        # Compute swap stats from virtual / physical memory stats
        # Attempting to retrieve data from AIDA64
        data = _get_data()
        mem_used = float(data.get("sys", {}).get("Used Memory", {}).get("value", math.nan))
        mem_available = float(data.get("sys", {}).get("Free Memory", {}).get("value", math.nan))
        virtual_mem_used = float(data.get("sys", {}).get("Used Virtual Memory", {}).get("value", math.nan))
        virtual_mem_available = float(data.get("sys", {}).get("Free Virtual Memory", {}).get("value", math.nan))

        if mem_used is math.nan or mem_available is math.nan or virtual_mem_used is math.nan or virtual_mem_available is math.nan:
            memory = get_hw_and_update(Hardware.HardwareType.Memory)
            for sensor in memory.Sensors:
                if sensor.SensorType != Hardware.SensorType.Data: continue
                if str(sensor.Name).startswith("Memory Used"):
                    mem_used = int(sensor.Value)
                elif str(sensor.Name).startswith("Memory Available"):
                    mem_available = int(sensor.Value)
                elif str(sensor.Name).startswith("Virtual Memory Used"):
                    virtual_mem_used = int(sensor.Value)
                elif str(sensor.Name).startswith("Virtual Memory Available"):
                    virtual_mem_available = int(sensor.Value)

        swap_used = virtual_mem_used - mem_used
        swap_available = virtual_mem_available - mem_available
        swap_total = swap_used + swap_available
        return (int(swap_used / swap_total * 100.0), "%")

    @staticmethod
    def virtual_percent():
        # Attempting to retrieve data from AIDA64
        precent = _get_data().get("sys", {}).get("Memory Utilization", {}).get("value", math.nan)

        if precent is math.nan:
            memory = get_hw_and_update(Hardware.HardwareType.Memory)
            for sensor in memory.Sensors:
                if sensor.SensorType == Hardware.SensorType.Load and str(sensor.Name).startswith("Memory"):
                    precent = float(sensor.Value)

        return (int(precent), "%")

    @staticmethod
    def virtual_used():
        # Attempting to retrieve data from AIDA64
        used = _get_data().get("sys", {}).get("Used Memory", {}).get("value", math.nan)

        if used is math.nan:
            memory = get_hw_and_update(Hardware.HardwareType.Memory)
            for sensor in memory.Sensors:
                if sensor.SensorType == Hardware.SensorType.Data and str(sensor.Name).startswith("Memory Used"):
                    used = int(sensor.Value * 1000000000.0) / (1024.0 ** 2)

        return (int(used), "MB")

    @staticmethod
    def virtual_free():
        # Attempting to retrieve data from AIDA64
        free = _get_data().get("sys", {}).get("Free Memory", {}).get("value", math.nan)

        if free is math.nan:
            memory = get_hw_and_update(Hardware.HardwareType.Memory)
            for sensor in memory.Sensors:
                if sensor.SensorType == Hardware.SensorType.Data and str(sensor.Name).startswith("Memory Available"):
                    free = int(sensor.Value * 1000000000.0) / (1024.0 ** 2)

        return (int(free), "MB")


class Disk:
    @staticmethod
    def disk_usage_percent():
        # Attempting to retrieve data from AIDA64
        sys_data = _get_data().get("sys", {})
        used_space = 0
        free_space = 0
        for label, info in sys_data.items():
            if label.endswith(" Used Space"):
                used_space += float(info.get("value", 0))
            elif label.endswith(" Free Space"):
                free_space += float(info.get("value", 0))

        if used_space == 0 or free_space == 0:
            percent = psutil.disk_usage("/").percent
        else:
            total_space = free_space + used_space
            percent = (used_space / total_space) * 100

        return (int(percent), "%")

    @staticmethod
    def disk_used():
        # Attempting to retrieve data from AIDA64
        sys_data = _get_data().get("sys", {})
        used_space = 0
        for label, info in sys_data.items():
            if label.endswith(" Used Space"):
                used_space += float(info.get("value", math.nan))

        if used_space == 0:
            # bytes -> GB
            used_space = psutil.disk_usage("/").used / (1024.0 ** 3)

        return (int(used_space), "GB")

    @staticmethod
    def disk_free():
        sys_data = _get_data().get("sys", {})
        free_space = 0
        for label, info in sys_data.items():
            if label.endswith(" Free Space"):
                free_space += float(info.get("value", math.nan))

        if free_space == 0:
            # bytes -> GB
            free_space = psutil.disk_usage("/").free / (1024.0 ** 3)
        return (int(free_space), "GB")

    @staticmethod
    def disk_total():
        # Attempting to retrieve data from AIDA64
        sys_data = _get_data().get("sys", {})
        used_space = 0
        free_space = 0
        for label, info in sys_data.items():
            if label.endswith(" Used Space"):
                used_space += float(info.get("value", 0))
            elif label.endswith(" Free Space"):
                free_space += float(info.get("value", 0))

        if used_space == 0 or free_space == 0:
            used_space = psutil.disk_usage("/").used / (1024.0 ** 3)
            free_space = psutil.disk_usage("/").free / (1024.0 ** 3)

        return (int(free_space + used_space), "GB")

class Net:
    @staticmethod
    def stats(interval):
        # Select the NIC with the highest download rate.
        sys_data = _get_data().get("sys", {})
        label_to_index = [(" Download Rate", 0), (" Upload Rate", 2), (" Total Download", 1), (" Total Upload", 3)]
        stats_dict = {} # {key: [dl rate, downloaded, up rate, uploaded]}
        target = ""

        # Attempting to retrieve data from AIDA64
        dl_rate = None
        for label, info in sys_data.items():
            key = label.split(" ")[0]
            for item in label_to_index:
                if label.endswith(item[0]):
                    value = float(info.get("value", 0))
                    if item[0] == " Download Rate" and (dl_rate is None or dl_rate < value):
                        dl_rate = value
                        target = key
                    if key not in stats_dict:
                        stats_dict[key] = [0, 0, 0, 0]
                    stats_dict[key][item[1]] = value
                    break

        if not stats_dict:
            dl_rate = None
            for if_name in net_io:
                net_if = get_net_interface_and_update(if_name)
                if net_if is None: continue
                uploaded, downloaded, upload_rate, download_rate = [-1] * 4
                for sensor in net_if.Sensors:
                    if sensor.SensorType == Hardware.SensorType.Data and str(sensor.Name).startswith("Data Uploaded"):
                        uploaded = round(int(sensor.Value * 1000000000.0) / (1024.0 ** 2), 1)
                    elif sensor.SensorType == Hardware.SensorType.Data and str(sensor.Name).startswith("Data Downloaded"):
                        downloaded = round(int(sensor.Value * 1000000000.0) / (1024.0 ** 2), 1)
                    elif sensor.SensorType == Hardware.SensorType.Throughput and str(sensor.Name).startswith("Upload Speed"):
                        upload_rate = round(int(sensor.Value) / 1024.0, 1)
                    elif sensor.SensorType == Hardware.SensorType.Throughput and str(sensor.Name).startswith("Download Speed"):
                        download_rate = round(int(sensor.Value) / 1024.0, 1)
                if download_rate == -1: continue
                # {key: [dl rate, downloaded, up rate, uploaded]}
                stats_dict[if_name] = [download_rate, downloaded, upload_rate, uploaded]
                if dl_rate is None or dl_rate < download_rate:
                    target = if_name

        res = stats_dict.get(target, ["-", "-" , "-", "-"])
        result = {
                    "up_rate": (res[2], "KB/s"), # Upload rate
                    "dl_rate": (res[0], "KB/s"), # Download rate
                    "uploaded": (res[3], "MB"), # Amount of data uploaded
                    "downloaded": (res[1], "MB") # Amount of data downloaded
                }
        return result
