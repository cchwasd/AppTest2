import pathlib
from dataclasses import dataclass
import os
import subprocess
from config.AppConfig import app_config
from adbutils import adb, AdbDevice
from adbutils._utils import APKReader
from common import the_paths


class ADevice:
    def __init__(self, serial=None):
        self.find_type = "findstr" if app_config.system_type == "Windows" else "grep"
        self.__serial = serial
    @property
    def get_serial(self):
        return self.__serial
    @get_serial.setter
    def set_serial(self, sno):
        self.__serial = sno

    def exec(self, command="", use_shell=True):
        cmd = f"adb -s {self.__serial} {command}"
        if use_shell:
             cmd = f"adb -s {self.__serial} shell {command}"
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True)
        # 获取输出和错误
        stdout, stderr = process.communicate()
        # 打印输出和错误
        # print(stdout.decode())
        if stderr:
            print(stderr.decode())
            # raise Exception(stderr.decode())
        return stdout.strip().decode()

    def get_device_state(self):
        """
        获取设备状态： offline | bootloader | device 等
        """
        return self.exec("get-state",False)

    def get_device_sno(self):
        """
        只有一个设备，获取设备id号，return serialNo
        """
        return self.exec("get-serialno",False)

    def get_android_os_version(self):
        """
        获取设备中的Android版本号，如4.2.2
        """
        return self.exec("getprop ro.build.version.release")

    def get_sdk_version(self):
        """
        获取设备SDK版本号
        """
        return self.exec("getprop ro.build.version.sdk")

    def get_device_model(self):
        """
        获取设备型号
        """
        return self.exec("getprop ro.product.model")

    def get_battery_level(self):
        """
        获取电池电量
        """
        level = self.exec(f"dumpsys battery | {self.find_type} level").split(": ")[-1]
        return int(level)

    def get_battery_status(self):
        """
        获取电池充电状态
        BATTERY_STATUS_UNKNOWN：未知状态
        BATTERY_STATUS_CHARGING: 充电状态
        BATTERY_STATUS_DISCHARGING: 放电状态
        BATTERY_STATUS_NOT_CHARGING：未充电
        BATTERY_STATUS_FULL: 充电已满
        """
        statusDict = {1: "BATTERY_STATUS_UNKNOWN",
                      2: "BATTERY_STATUS_CHARGING",
                      3: "BATTERY_STATUS_DISCHARGING",
                      4: "BATTERY_STATUS_NOT_CHARGING",
                      5: "BATTERY_STATUS_FULL"}
        status = self.exec(f"dumpsys battery | {self.find_type} status").split(": ")[-1]
        return statusDict[int(status)]

    def get_battery_temp(self):
        """
        获取电池温度
        """
        temp = self.exec(f"dumpsys battery | {self.find_type} temperature").split(": ")[-1]
        return int(temp) / 10.0

    def get_screen_size(self):
        """
        获取设备屏幕分辨率，return (width, high)
        """
        out = self.exec("wm size").split("\n")[-1].split(": ")[-1].split('x')
        return (int(out[0]), int(out[1]))


class AdbBar:
    devices: list = []
    def __init__(self, serial: str="", package: str=""):
        # self.device = ADevice(serial) # 自定义使用
        self.device: AdbDevice = adb.device(serial=serial) # 推荐使用adbutils 该第三方库提供的
        self.__package = package    # 用不到，当使用格式demo
        self.device_type = self.get_device_type(serial)

    def __str__(self):
        return f"{self.device},{self.device_type}"
    def __repr__(self):
        return f"{self.device},{self.device_type}"

    @property
    def package(self):
        return self.__package

    @package.setter
    def package(self, package: str):
        self.__package = package

    @classmethod
    def get_connected_devices(cls):
        result = os.popen("adb devices").read()
        devices = [item.split("\t")[0] for item in result.strip().split("\n") if "List of" not in item and "* daemon" not in item]
        cls.devices = devices
        return devices

    @classmethod
    def judge_device(cls, serial: str) -> bool:
        devices = cls.get_connected_devices()
        if serial in devices:
            return True
        return False

    @classmethod
    def get_device_type(cls, serial: str) -> str:
        """
        获取设备类型： emulator | default (phone) | tablet(平板) | wearable(穿戴设备)
        """
        dict_type = {"default": "phone", "tablet": "tablet", "wearable": "wearable"}
        result = os.popen(f"adb -s {serial} shell getprop ro.build.characteristics").read()
        return dict_type.get(result.strip(),"None")

    def check_adb_env(self):
        if "ANDROID_HOME" in os.environ.keys():
            os_name = app_config.system_type
            if os_name.lower() == "windows":
                adb_path = os.path.join(os.environ.get("ANDROID_HOME"), "platform-tools","adb.exe")
            elif os_name.lower() == "linux":
                adb_path = os.path.join(os.environ.get("ANDROID_HOME"), "platform-tools", "adb")
            if not os.path.exists(adb_path):
                result = os.popen("adb version").read()
                if "Installed as" in result:
                    for item in result.strip().split("\n"):
                        if item.startswith("Installed as "):
                            adb_path = item.strip().lstrip("Installed as ")
                            return True
            else:
                return True
        else:
            raise EnvironmentError("Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])

    def is_has_package(self, package_name):
        if self.device.serial and package_name in self.device.list_packages():
            return True
        return False

    def get_apk_file(self, package_name, savepath=""):
        """ 拉取 设备上已安装的app到本地 """
        if not all([self.device.serial, package_name]):
            return ""
        output = self.device.shell(["pm", "path", package_name])
        app_file = output.lstrip("package:")

        if not savepath:
            savepath = the_paths.get('resources')
        else:
            if isinstance(savepath, str):
                savepath = pathlib.Path(savepath)
        apk_bp, apk_sp = savepath / "base.apk", savepath / f"{package_name}.apk"

        self.device.sync.pull(app_file, apk_sp)
        return apk_sp

    def get_apk_info(self, apk_path):
        """获取 apk基本信息（package, version-name） """
        ar = APKReader(open(apk_path,"rb"))
        ar.dump_info()


AdbBar.devices = AdbBar.get_connected_devices()


if __name__ == '__main__':

    adber = AdbBar('f800062f')
    adber.package = "com.ss.android.ugc.aweme.lite"
    print(
        adber.devices, AdbBar.devices,
        adber.device.list_packages(),
        adber.is_has_package("com.ss.android.ugc.aweme.lite"),

    sep="\n")
    # sp = adber.get_apk_file(adber.package)
    apk_path = r"C:\MCodes\PyCodes\AppPro\resources\com.ss.android.ugc.aweme.lite.apk"
    adber.get_apk_info(apk_path)
    # adbder = ADevice('f800062f')
    # # print(adbder.exec("pm list packages"))
    # print(adbder.get_device_state(),adbder.get_device_sno(),
    #       adbder.get_device_model(),adbder.get_android_os_version(),adbder.get_sdk_version(),
    #       adbder.get_screen_size(),
    #       sep=";")