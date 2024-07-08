import math
import GPUtil
import psutil
import platform
from enum import IntEnum, auto
try:
    import pyamdgpuinfo
except:
    pyamdgpuinfo = None

try:
    import pyadl
except:
    pyadl = None

class GpuType(IntEnum):
    UNSUPPORTED = auto()
    AMD = auto()
    NVIDIA = auto()

pnic_before = {}
DETECTED_GPU = GpuType.UNSUPPORTED


class Cpu:
    @staticmethod
    def percentage(interval):
        return (int(psutil.cpu_percent(interval=interval)), "%")

    @staticmethod
    def temperature():
        cpu_temp = 0
        sensors_temps = psutil.sensors_temperatures()
        if "coretemp" in sensors_temps:
            # Intel CPU
            cpu_temp = sensors_temps["coretemp"][0].current
        elif "k10temp" in sensors_temps:
            # AMD CPU
            cpu_temp = sensors_temps["k10temp"][0].current
        elif "cpu_thermal" in sensors_temps:
            # ARM CPU
            cpu_temp = sensors_temps["cpu_thermal"][0].current
        elif "zenpower" in sensors_temps:
            # AMD CPU with zenpower (k10temp is in blacklist)
            cpu_temp = sensors_temps["zenpower"][0].current
        return (int(cpu_temp), "°C")


class Gpu:
    @staticmethod
    def stats():
        global DETECTED_GPU
        if DETECTED_GPU == GpuType.AMD and GpuAmd.is_available():
            stats = GpuAmd.stats()
        elif DETECTED_GPU == GpuType.NVIDIA and GpuNvidia.is_available():
            stats = GpuNvidia.stats()
        else:
            stats = ("-", "-")
        return ((int(stats[0]), "%"), (int(stats[1]), "°C"))


class GpuNvidia:
    @staticmethod
    def stats():
        # Unlike other sensors, Nvidia GPU with GPUtil pulls in all the stats at once
        nvidia_gpus = GPUtil.getGPUs()

        try:
            memory_used_all = [item.memoryUsed for item in nvidia_gpus]
            memory_used_mb = sum(memory_used_all) / len(memory_used_all)
        except:
            memory_used_mb = math.nan

        try:
            memory_total_all = [item.memoryTotal for item in nvidia_gpus]
            memory_total_mb = sum(memory_total_all) / len(memory_total_all)
            memory_percentage = (memory_used_mb / memory_total_mb) * 100
        except:
            memory_percentage = math.nan


        try:
            temperature_all = [item.temperature for item in nvidia_gpus]
            temperature = sum(temperature_all) / len(temperature_all)
        except:
            temperature = math.nan

        return (memory_percentage, temperature)

    @staticmethod
    def is_available():
        try:
            return len(GPUtil.getGPUs()) > 0
        except:
            return False


class GpuAmd:
    @staticmethod
    def stats():
        if pyamdgpuinfo:
            # Unlike other sensors, AMD GPU with pyamdgpuinfo pulls in all the stats at once
            i = 0
            amd_gpus = []
            while i < pyamdgpuinfo.detect_gpus():
                amd_gpus.append(pyamdgpuinfo.get_gpu(i))
                i = i + 1

            try:
                memory_used_all = [item.query_vram_usage() for item in amd_gpus]
                memory_used_bytes = sum(memory_used_all) / len(memory_used_all)
            except:
                memory_used_bytes = math.nan

            try:
                memory_total_all = [item.memory_info["vram_size"] for item in amd_gpus]
                memory_total_bytes = sum(memory_total_all) / len(memory_total_all)
                memory_percentage = (memory_used_bytes / memory_total_bytes) * 100
            except:
                memory_percentage = math.nan

            try:
                temperature_all = [item.query_temperature() for item in amd_gpus]
                temperature = sum(temperature_all) / len(temperature_all)
            except:
                temperature = math.nan

            return (memory_percentage, temperature)
        elif pyadl:
            amd_gpus = pyadl.ADLManager.getInstance().getDevices()

            try:
                temperature_all = [item.getCurrentTemperature() for item in amd_gpus]
                temperature = sum(temperature_all) / len(temperature_all)
            except:
                temperature = math.nan

            return (math.nan, temperature)

    @staticmethod
    def is_available():
        try:
            if pyamdgpuinfo and pyamdgpuinfo.detect_gpus() > 0:
                return True
            elif pyadl and len(pyadl.ADLManager.getInstance().getDevices()) > 0:
                return True
            else:
                return False
        except:
            return False


class Memory:
    @staticmethod
    def swap_percent():
        return (int(psutil.swap_memory().percent), "%")

    @staticmethod
    def virtual_percent():
        return (int(psutil.virtual_memory().percent), "%")

    @staticmethod
    def virtual_used():
        return (int(psutil.virtual_memory().used / (1024.0 ** 2)), "MB")

    @staticmethod
    def virtual_free():
        return (int(psutil.virtual_memory().free / (1024.0 ** 2)), "MB")


class Disk:
    @staticmethod
    def disk_usage_percent():
        if platform.system() == "Darwin":
            try:
                return (int(psutil.disk_usage("/System/Volumes/Data").percent), "%")
            except: pass
        return (int(psutil.disk_usage("/").percent), "%")

    @staticmethod
    def disk_used():
        if platform.system() == "Darwin":
            try:
                return (int(psutil.disk_usage("/System/Volumes/Data").used / (1024.0 ** 3)), "GB")
            except: pass
        return (int(psutil.disk_usage("/").used / (1024.0 ** 3)), "GB")

    @staticmethod
    def disk_free():
        if platform.system() == "Darwin":
            try:
                return (int(psutil.disk_usage("/System/Volumes/Data").free / (1024.0 ** 3)), "GB")
            except: pass
        return (int(psutil.disk_usage("/").free / (1024.0 ** 3)), "GB")

    @staticmethod
    def disk_total():
        if platform.system() == "Darwin":
            try:
                return (int(psutil.disk_usage("/System/Volumes/Data").total / (1024.0 ** 3)), "GB")
            except: pass
        return (int(psutil.disk_usage("/").total / (1024.0 ** 3)), "GB")


class Net:
    @staticmethod
    def stats(interval):
        global pnic_before

        result = {}
        dl_rate = None
        # Get current counters
        pnic_after = psutil.net_io_counters(pernic=True)

        # Select the NIC with the highest download rate.
        for if_name, if_info in pnic_after.items():
            try:
                upload_rate = (if_info.bytes_sent - pnic_before[if_name].bytes_sent) / interval
                uploaded = if_info.bytes_sent
                download_rate = (if_info.bytes_recv - pnic_before[if_name].bytes_recv) / interval
                downloaded = if_info.bytes_recv
                if dl_rate is None or (download_rate > dl_rate):
                    result = {
                        "up_rate": (round(upload_rate / 1024.0, 1), "KB/s"), # Upload rate
                        "dl_rate": (round(download_rate / 1024.0, 1), "KB/s"), # Download rate
                        "uploaded": (round(uploaded / (1024.0 ** 2), 1), "MB"), # Amount of data uploaded
                        "downloaded": (round(downloaded / (1024.0 ** 2), 1), "MB") # Amount of data downloaded
                    }
                    dl_rate = download_rate
            # Interface might not be in pnic_before for now
            except: pass
            pnic_before.update({if_name: pnic_after[if_name]})
        return result
