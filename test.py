import re
# Find interesting strings in binaries.

data = open('./bin', "r").read()
strings = re.findall("[\x1f-\x7e]{6,}", data)
strings += [str(ws.decode("utf-16le")) for ws in re.findall("(?:[\x1f-\x7e][\x00]){6,}", data)]
for string in strings:
    print string

import frida

package_name = "com.example.muhzi.trial"


def get_messages_from_js(message, data):
    print message


def get_hook_code():

    return ''


process = frida.get_device_manager().get_device("emulator-5554").attach(package_name)
script = process.create_script(get_hook_code())
script.on('message', get_messages_from_js)
script.load()
from time import sleep
sleep(20)
# subprocess.check_call('adb -s 9ade2f68 shell su -c killall com.example.muhzi.trial'.split())
sleep(5)
process.detach()
