# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import os
import re
import json
import logging

from lib.definitions.constants import ROOT_DIR
from lib.definitions.classes import MonitoringModule

from lib.definitions.exceptions import (
    XenDroidFridaError, XenDroidModuleError
)


class ScriptFactory(object):
    """
    This class generates the JavaScript scripts that frida injects
    for Android Java API instrumentation
    """
    values_module = __import__('lib.definitions.values', fromlist=['*'])

    def __init__(self, hook_def):

        """
        :param hook_def: JSON object that defines a method hook
        """
        self.cls_name = hook_def['class']
        self.method_name = hook_def['method']
        self.method_params_types = hook_def['params']
        self.hooked_params = hook_def['hooked_params']
        self.hook_category = hook_def['category']

        self.method_params = ', '.join(
            ['param{}'.format(x) for x in range(len(self.method_params_types))]
        )

    def __get_hook_code(self, _hook_handler=str(), used_classes=str(), return_capture=None):
        base_hook_code = \
                """
                try {
                    const hook_cls = Java.use("%s");
                    %s
                    // Load the hook
                    hook_cls.%s.overload(%s).implementation = function (%s) {
                        var hookData = {
                            "Category" : "%s",
                            "Class" : "%s",
                            "Method" : "%s"
                        };
                        %s
                        send(JSON.stringify(hookData));
                        var ret_val;
                        %s
                        return ret_val;
                    };
                } catch(e) { setTimeout(function() { throw e; }, 0); }
                """

        overload_args = ', '.join(['"{}"'.format(x) for x in self.method_params_types])

        for param_name in self.hooked_params:

            param_num = self.hooked_params[param_name]
            if not re.search('[.[]', self.method_params_types[param_num]):
                tmp = 'hookData["{}"] = param{};'
            elif self.method_params_types[param_num].startswith('[L'):
                tmp = 'hookData["{}"] = Arrays.deepToString(param{});'
            elif self.method_params_types[param_num] == '[B':
                tmp = 'hookData["{}"] = String.$new(param{}).toString();'
            elif self.method_params_types[param_num] == 'java.io.File':
                tmp = 'hookData["{}"] = param{}.getAbsolutePath();'
            else:
                tmp = 'hookData["{}"] = param{}.toString();'

            _hook_handler += tmp.format(param_name, param_num)

        if return_capture is None:
            return_capture = 'ret_val = this.%s(%s);' % (self.method_name, self.method_params)

        return base_hook_code % (self.cls_name, used_classes, self.method_name,
                                 overload_args, self.method_params, self.hook_category,
                                 self.cls_name, self.method_name, _hook_handler,
                                 return_capture)

    def _get_hook_code_for_android_telephony_TelephonyManager(self):
        if self.method_name.startswith('get'):
            mock_val = getattr(
                self.values_module, 'MOCK_TM_' + self.method_name[3:].upper(), str()
            )
            return self.__get_hook_code(
                return_capture='ret_val = String.$new("%s");' % mock_val
            )
        else:
            return self.__get_hook_code()

    def _get_hook_code_for_android_net_wifi_WifiInfo(self):
        if self.method_name == 'getMacAddress':
            mock_val = getattr(self.values_module, 'MOCK_WIFI_MACADDRESS', str())
            return self.__get_hook_code(
                return_capture='ret_val = String.$new("%s");' % mock_val
            )
        else:
            return self.__get_hook_code()

    def _get_hook_code_for_android_app_SharedPreferencesImpl(self):
        used_classes = 'const file_cls = Java.use("java.io.File");'

        _hook_handler = \
            """
            var file_instance = Java.cast(this.mFile.value, file_cls);
            hookData["Target file"] = file_instance.getAbsolutePath();
            """
        return self.__get_hook_code(_hook_handler, used_classes)

    def _get_hook_code_for_android_app_SharedPreferencesImpl_EditorImpl(self):
        used_classes = \
            """
            const pref_cls = Java.use("android.app.SharedPreferencesImpl");
            const file_cls = Java.use("java.io.File");
            """

        _hook_handler = \
            """
            var pref_instance = Java.cast(this.this$0.value, pref_cls);
            var file_instance = Java.cast(pref_instance.mFile.value, file_cls);
            
            hookData["Target file"] = file_instance.getAbsolutePath();
            """
        return self.__get_hook_code(_hook_handler, used_classes)

    def _get_hook_code_for_android_content_ContentResolver(self):
        if self.method_name.startswith('insert'):
            _hook_handler = \
                """
                var keys = param1.keySet();
                hookData["Content values"] = []
                
                for(i = 0; i < keys.size(); i++){
                    var aKey = keys.iterator().next();
                    
                    hookData["Content values"].push({
                        "Key": aKey.toString(),
                        "Value": param1.get(aKey).toString()
                    });
                }
                """
            return self.__get_hook_code(_hook_handler)

        else:
            return self.__get_hook_code()

    def _get_hook_code_for_android_database_sqlite_SQLiteDatabase(self):
        _hook_handler = 'hookData["Target file"] = this.getPath();'

        if self.method_name.startswith('insert'):
            _hook_handler += \
                """
                var keys = param2.keySet();
                hookData["Entries"] = []
    
                for(i = 0; i < keys.size(); i++){
                    var aKey = keys.iterator().next();
    
                    hookData["Content values"].push({
                        "Column": aKey.toString(), 
                        "Value": param2.get(aKey).toString()
                    });
                }
                """
        return self.__get_hook_code(_hook_handler)

    def _get_hook_code_for_android_content_Context(self):
        if self.method_name == 'registerReceiver':
            _hook_handler = 'hookData["Action"] = param1.getAction();'
            return self.__get_hook_code(_hook_handler)

        else:
            return self.__get_hook_code()

    def _get_hook_code_for_java_lang_ProcessBuilder(self):
        if self.method_name == 'start':
            _hook_handler = \
                """
                hookData["Command"] = '';
                for(cmd in this.command)
                    hookData["Command"] += cmd + ' ';
                """
            return self.__get_hook_code(_hook_handler)

        else:
            return self.__get_hook_code()

    @staticmethod
    def wrap_hook_code(hook_code):
        return \
            """
            // This script is generated from XenDroid `https://www.github.com/muhzii/XenDroid`

            // Attach to the vm
            Java.perform(function() {
                const Arrays = Java.use("java.util.Arrays");
                const String = Java.use("java.lang.String");
                %s
            });
            """ % hook_code

    def get_script(self, wrap=True):
        gen_name = "_get_hook_code_for_{}".format(re.sub('[.$]', '_', self.cls_name))
        gen_func = getattr(self, gen_name, None)

        if gen_func is None:
            script = self.__get_hook_code()
        else:
            script = gen_func()

        if wrap:
            return self.wrap_hook_code(script)
        else:
            return script


class APIMonitor(MonitoringModule):

    def __init__(self, analysis_path, frida_connection):

        MonitoringModule.__init__(self, analysis_path, 'API Monitoring')

        self.logger = logging.getLogger(self.__class__.__name__)
        self.frida_connection = frida_connection

        self.logs_path = os.path.join(
            self.analysis_path, 'logs', 'frida_logs.log'
        )
        self.err_logs_path = os.path.join(
            self.analysis_path, 'logs', 'frida_errors_logs.log'
        )
        self.hooks_file = os.path.join(
            ROOT_DIR, 'utils', 'hooking', 'hooks_def.json'
        )

        self.logs_dumper = None
        self.errors_dumper = None
        self._init_dumping()

    def _init_dumping(self):
        # initialize the logging to dump logs to a file that will contain the hooking logs

        self.logs_dumper = logging.getLogger('FRIDA_MESSAGE')
        self.errors_dumper = logging.getLogger('FRIDA_ERROR')

        self.errors_dumper.setLevel(logging.DEBUG)
        self.logs_dumper.setLevel(logging.DEBUG)

        logs_fh = logging.FileHandler(self.logs_path)
        logs_fh.setLevel(logging.INFO)

        errors_fh = logging.FileHandler(self.err_logs_path)
        errors_fh.setLevel(logging.INFO)

        self.logs_dumper.addHandler(logs_fh)
        self.errors_dumper.addHandler(errors_fh)

        self.logs_dumper.propagate = False
        self.errors_dumper.propagate = False

    def __log_script_messages(self, message, payload):
        if message['type'] == 'send':
            if 'payload' in message:
                self.logs_dumper.info(payload)
        elif message['type'] == 'error':
            self.errors_dumper.info(message)

    def start(self):
        """
        start monitoring android api calls
        :return:
        """
        super(APIMonitor, self).start()

        # load the file that contains the scripts definitions
        hooks_def = json.load(open(self.hooks_file, 'r'))

        hook_script_jvm = str()
        # loop through all the hooks in the json file
        for hook in hooks_def:
            script_gen = ScriptFactory(hook)
            hook_script_jvm += script_gen.get_script(wrap=False)

        hook_script_jvm = ScriptFactory.wrap_hook_code(hook_script_jvm)

        self.frida_connection.set_msg_handler(self.__log_script_messages)
        try:
            # attach to the process
            self.frida_connection.start_session()
            # load the script into the device
            self.frida_connection.load_script(hook_script_jvm)
        except XenDroidFridaError as e:
            self.logger.error(e.message)
            raise XenDroidModuleError()

        self.pid = self.frida_connection.pid
        self.logger.debug(
            'successfully started the API monitoring module...'
        )

    def stop(self):
        """
        stop the monitoring process
        :return:
        """
        super(APIMonitor, self).stop()

        self.frida_connection.terminate_session()
        self.logger.debug(
            'API monitoring module successfully terminated!'
        )
