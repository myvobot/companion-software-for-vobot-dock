import platform

# Determine the data source based on the computer operating system.
if platform.system() == 'Windows':
    import sensors.sensors_windows as sensors
else:
    import sensors.sensors_python as sensors

class CPU:
    @staticmethod
    def percentage():
        try:
            return sensors.Cpu.percentage(interval=1)
        except:
            return ("-", "%")

    @staticmethod
    def temperature():
        try:
            return sensors.Cpu.temperature()
        except:
            return ("-", "°")


class Gpu:
    @staticmethod
    def stats():
        try:
            return sensors.Gpu.stats()
        except:
            return (("-", "%"), ("-", "°"))


class Memory:
    @staticmethod
    def stats():
        try:
            swap_percent = sensors.Memory.swap_percent()
        except Exception:
            swap_percent = ("-", "%")

        try:
            virtual_percent = sensors.Memory.virtual_percent()
        except:
            virtual_percent = ("-", "%")

        try:
            virtual_used = sensors.Memory.virtual_used()
        except:
            virtual_used = ("-", "MB")

        try:
            virtual_free = sensors.Memory.virtual_free()
        except:
            virtual_free = ("-", "MB")

        return (swap_percent, virtual_used, virtual_free, virtual_percent)


class Disk:
    @staticmethod
    def stats():
        try:
            disk_used = sensors.Disk.disk_used()
        except:
            disk_used = ("-", "MB")

        try:
            disk_free = sensors.Disk.disk_free()
        except:
            disk_free = ("-", "MB")

        try:
            disk_usage = sensors.Disk.disk_usage_percent()
        except:
            disk_usage = ("-", "%")

        try:
            disk_total = sensors.Disk.disk_total()
        except:
            disk_total = ("-", "MB")

        return (disk_used, disk_free, disk_total, disk_usage)


class Net:
    @staticmethod
    def stats():
        return sensors.Net.stats(1)