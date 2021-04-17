Import("env")
import os
import sys
import subprocess
import hashlib
import fnmatch
import time
import re
import melodyparser

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from git import Repo
except ImportError:
    sys.stdout.write("Installing GitPython")
    install("GitPython")
    from git import Repo

build_flags = env['BUILD_FLAGS']

try:
    from git import Repo
except ImportError:
    env.Execute("$PYTHONEXE -m pip install GitPython")
    from git import Repo

build_flags = env['BUILD_FLAGS']

UIDbytes = ""
define = ""

def print_error(error):
    time.sleep(1)
    sys.stdout.write("\033[47;31m%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
    sys.stdout.write("\033[47;31m!!!             ExpressLRS Warning Below             !!!\n")
    sys.stdout.write("\033[47;31m%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
    sys.stdout.write("\033[47;30m  %s \n" % error)
    sys.stdout.write("\033[47;31m%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
    sys.stdout.flush()
    time.sleep(3)
    raise Exception('!!! %s !!!' % error)


def parse_flags(path):
    try:
        with open(path, "r") as _f:
            for define in _f:
                define = define.strip()
                if define.startswith("-D"):
                    if "MY_BINDING_PHRASE" in define:
                        bindingPhraseHash = hashlib.md5(define.encode()).digest()
                        UIDbytes = (str(bindingPhraseHash[0]) + "," + str(bindingPhraseHash[1]) + "," + str(bindingPhraseHash[2]) + ","+ str(bindingPhraseHash[3]) + "," + str(bindingPhraseHash[4]) + "," + str(bindingPhraseHash[5]))
                        define = "-DMY_UID=" + UIDbytes
                        sys.stdout.write("\u001b[32mUID bytes: " + UIDbytes + "\n")
                        sys.stdout.flush()
                    if "MY_STARTUP_MELODY=" in define:
                        defineValue = define.split('"')[1::2][0].split("|") # notes|bpm|transpose
                        transposeBySemitones = int(defineValue[2]) if len(defineValue) > 2 else 0
                        parsedMelody = melodyparser.parseMelody(defineValue[0].strip(), int(defineValue[1]), transposeBySemitones)
                        define = "-DMY_STARTUP_MELODY_ARR=\"" + parsedMelody + "\""
                    if "MY_WIFI_PASSWORD=" in define:
                        defineValue = define.split('"')[1::2][0]
                        define = "-DMY_WIFI_PASSWORD=\"\\\"" + defineValue + "\\\"\""
                    if "MY_TX_SSID=" in define:
                        defineValue = define.split('"')[1::2][0]
                        define = "-DMY_TX_SSID=\"\\\"" + defineValue + "\\\"\""
                    if "MY_RX_SSID=" in define:
                        defineValue = define.split('"')[1::2][0]
                        define = "-DMY_RX_SSID=\"\\\"" + defineValue + "\\\"\""
                    build_flags.append(define)
    except IOError:
        print("File '%s' does not exist" % path)

parse_flags("user_defines.txt")

print("build flags: %s" % env['BUILD_FLAGS'])

# Handle any negated flags i.e. !-Dxxxx remove -Dxxxx from flags
for line in build_flags:
    for flag in re.findall("!-D\s*[^\s]+", line):
        build_flags = [x.replace(flag[1:],"") for x in build_flags]
build_flags = [x.replace("!", "") for x in build_flags]

git_repo = Repo(os.getcwd(), search_parent_directories=True)
git_root = git_repo.git.rev_parse("--show-toplevel")
ExLRS_Repo = Repo(git_root)
sha = ExLRS_Repo.head.object.hexsha
build_flags.append("-DLATEST_COMMIT=0x"+sha[0]+",0x"+sha[1]+",0x"+sha[2]+",0x"+sha[3]+",0x"+sha[4]+",0x"+sha[5])

env['BUILD_FLAGS'] = build_flags

print("build flags: %s" % env['BUILD_FLAGS'])

if not fnmatch.filter(env['BUILD_FLAGS'], '*-DRegulatory_Domain*'):
    print_error('Please define a Regulatory_Domain in user_defines.txt')

if fnmatch.filter(env['BUILD_FLAGS'], '*-DENABLE_TELEMETRY*') and not fnmatch.filter(env['BUILD_FLAGS'], '*-DHYBRID_SWITCHES_8*'):
    print_error('Telemetry requires HYBRID_SWITCHES_8')

if fnmatch.filter(env['BUILD_FLAGS'], '*PLATFORM_ESP32*'):
    sys.stdout.write("\u001b[32mBuilding for ESP32 Platform\n")
elif fnmatch.filter(env['BUILD_FLAGS'], '*PLATFORM_STM32*'):
    sys.stdout.write("\u001b[32mBuilding for STM32 Platform\n")
elif fnmatch.filter(env['BUILD_FLAGS'], '*PLATFORM_ESP8266*'):
    sys.stdout.write("\u001b[32mBuilding for ESP8266/ESP8285 Platform\n")
    if fnmatch.filter(env['BUILD_FLAGS'], '-DAUTO_WIFI_ON_INTERVAL*'):
        sys.stdout.write("\u001b[32mAUTO_WIFI_ON_INTERVAL = ON\n")
    else:
        sys.stdout.write("\u001b[32mAUTO_WIFI_ON_INTERVAL = OFF\n")

if fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_AU_915*'):
    sys.stdout.write("\u001b[32mBuilding for SX1276 915AU\n")

elif fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_EU_868*'):
    sys.stdout.write("\u001b[32mBuilding for SX1276 868EU\n")

elif fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_AU_433*'):
    sys.stdout.write("\u001b[32mBuilding for SX1278 433AU\n")

elif fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_EU_433*'):
    sys.stdout.write("\u001b[32mBuilding for SX1278 433AU\n")

elif fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_FCC_915*'):
    sys.stdout.write("\u001b[32mBuilding for SX1276 915FCC\n")

elif fnmatch.filter(env['BUILD_FLAGS'], '*Regulatory_Domain_ISM_2400*'):
    sys.stdout.write("\u001b[32mBuilding for SX1280 2400ISM\n")

time.sleep(1)

# Set upload_protovol = 'custom' for STM32 MCUs
#  otherwise firmware.bin is not generated
stm = env.get('PIOPLATFORM', '') in ['ststm32']
if stm:
    env['UPLOAD_PROTOCOL'] = 'custom'

