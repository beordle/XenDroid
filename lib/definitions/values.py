# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


from lib.api.utils import get_rand_str, get_rand_mac_addr

# MOCK VALUES

MOCK_TM_SIMCOUNTRYISO = 'usa'

MOCK_TM_IMEI = get_rand_str(15)

MOCK_TM_MEID = get_rand_str(14)

MOCK_TM_SIMOPERATORNAME = "Verizon"

MOCK_TM_DEVICEID = get_rand_str(15)

MOCK_TM_DEVICESOFTWAREVERSION = '01'

MOCK_TM_SUBSCRIBERID = get_rand_str(15)

MOCK_TM_NETWORKOPERATOR = get_rand_str(5)

MOCK_TM_SIMSERIALNUMBER = get_rand_str(20)

MOCK_WIFI_MACADDRESS = get_rand_mac_addr()

MOCK_TM_SIMOPERATOR = MOCK_TM_NETWORKOPERATOR

MOCK_TM_NETWORKCOUNTRYISO = MOCK_TM_SIMCOUNTRYISO

MOCK_TM_NETWORKOPERATORNAME = MOCK_TM_SIMOPERATORNAME
