# This module monitors the android APIs defined in the JSON file, which are called during the runtime of the application

from modules.definitions.abstract import RunTimeModule
from modules.definitions.constants import ROOT_DIR
import frida
import logging
import os
import json
import re


class ScriptFactory(object):

    """
    This class generates the scripts that frida injects for API instrumentation
    """

    def __init__(self, hook_def):

        self.cls_name = hook_def['class']
        self.method_name = hook_def['method']
        self.method_params_types = hook_def['params']
        self.hooked_params = hook_def['hooked_params']
        self.hook_category = hook_def['category']

        self.method_params = ','.join(['param{}'.format(x) for x in range(len(self.method_params_types))])

    def __get_hook_code(self, _hook_handler=str(), loaded_classes=str(), return_val=None):

        base_hook_code = \
            """
            // This script is generated from XenDroid `https://www.github.com/muhzii/XenDroid`
            
            // Load the hook into the JVM
            Java.perform(function() {
                const Arrays = Java.use("java.util.Arrays");
                const String = Java.use("java.lang.String");
                const hook_cls = Java.use("%s");
                %s
                hook_cls.%s.overload(%s).implementation = function (%s) {
                    var hookData = {
                        "Category" : "%s",
                        "Class" : "%s",
                        "Method" : "%s"
                    };
                    %s
                    send(JSON.stringify(hookData));
                    return %s;
                };
            });
            """

        overload_args = ','.join(['"{}"'.format(x) for x in self.method_params_types])

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

        if return_val is None:
            return_val = 'this.%s(%s)' % (self.method_name, self.method_params)

        return base_hook_code % (self.cls_name, loaded_classes, self.method_name, overload_args,
                                 self.method_params, self.hook_category, self.cls_name,
                                 self.method_name, _hook_handler, return_val)

    def __get_hook_code_for_android_telephony_TelephoneManager(self):

        if self.method_name.startswith('get'):
            return_val = 'this.%s(%s).split("").sort(function(){return 0.5-Math.random()}).join("")' % \
                         (self.method_name, self.method_params)
            return self.__get_hook_code(return_val=return_val)
        else:
            return self.__get_hook_code()

    def __get_hook_code_for_android_app_SharedPreferencesImpl(self):

        loaded_classes = 'const file_cls = Java.use(java.io.File");'

        _hook_handler = \
            """
            var file_instance = Java.cast(this.mFile.value, file_cls);
            hookData["Target file"] = file_instance.getAbsolutePath();
            """
        return self.__get_hook_code(_hook_handler, loaded_classes)

    def __get_hook_code_for_android_app_SharedPreferencesImpl_EditorImpl(self):

        loaded_classes = \
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
        return self.__get_hook_code(_hook_handler, loaded_classes)

    def __get_hook_code_for_android_content_ContentResolver(self):

        if self.method_name.startswith('insert'):
            _hook_handler = \
                """
                var keys = param1.keySet();
                hookData["Content values"] = []
                
                for(i = 0; i < keys.size(); i++){
                    var aKey = keys.iterator().next();
                    
                    hookData["Content values"].push(
                        {"Key": aKey.toString(), "Value": param1.get(aKey).toString()}
                    );
                }
                """
            return self.__get_hook_code(_hook_handler)

        else:
            return self.__get_hook_code()

    def __get_hook_code_for_android_database_sqlite_SQLiteDatabase(self):

        _hook_handler = 'hookData["Target file"] = this.getPath();'

        if self.method_name.startswith('insert'):
            _hook_handler += \
                """
                var keys = param2.keySet();
                hookData["Entries"] = []
    
                for(i = 0; i < keys.size(); i++){
                    var aKey = keys.iterator().next();
    
                    hookData["Content values"].push(
                        {"Column": aKey.toString(), "Value": param2.get(aKey).toString()}
                    );
                }
                """
        return self.__get_hook_code(_hook_handler)

    def __get_hook_code_for_android_content_Context(self):

        if self.method_name == 'registerReceiver':
            _hook_handler = 'hookData["Action"] = param1.getAction();'
            return self.__get_hook_code(_hook_handler)

        else:
            return self.__get_hook_code()

    def __get_hook_code_for_java_lang_ProcessBuilder(self):

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

    def get_script(self):

        gen_name = "__get_hook_code_for_{}".format(re.sub('[.$]', '_', self.cls_name))
        gen_func = getattr(self, gen_name, None)

        if gen_func is None:
            return self.__get_hook_code()
        else:
            return gen_func()


class ProcessMonitor(RunTimeModule):

    def __init__(self, package_name, device_serial, analysis_path):

        RunTimeModule.__init__(self)

        self.logger = logging.getLogger(self.__class__.__name__)

        self.package_name = package_name
        self.device_serial = device_serial
        self.analysis_path = analysis_path

        self.logs_file_path = os.path.join(analysis_path, 'logs', 'frida_logs.log')
        self.errors_file_path = os.path.join(analysis_path, 'logs', 'frida_errors_logs.log')

        self.hook_file_path = os.path.join(ROOT_DIR, 'utils', 'hooking', 'hooks_def.json')

        self.logs_dumper = None
        self.errors_dumper = None
        self.init_dumping()

    def init_dumping(self):

        # initialize the logging to dump logs to a file that will contain the hooking logs
        self.logs_dumper = logging.getLogger()
        self.errors_dumper = logging.getLogger()

        self.errors_dumper.setLevel(logging.DEBUG)
        self.logs_dumper.setLevel(logging.DEBUG)

        logs_fh = logging.FileHandler(self.logs_file_path)
        logs_fh.setLevel(logging.DEBUG)

        errors_fh = logging.FileHandler(self.errors_file_path)
        errors_fh.setLevel(logging.DEBUG)

        self.logs_dumper.addHandler(logs_fh)
        self.errors_dumper.addHandler(errors_fh)

    def __log_script_messages(self, message, data):

        if message['type'] == 'send':
            self.logs_dumper.debug(message['payload'])
        elif message['type'] == 'error':
            self.errors_dumper.debug(message)

    def run(self):

        # first: attach to the process
        session = frida.get_device_manager().get_device(self.device_serial).attach(self.package_name)

        # load the file that contains the scripts definitions
        hooks_def = json.load(open(self.hook_file_path, 'r'))

        # loop through all the hooks in the json file
        for hook in hooks_def:

            script_gen = ScriptFactory(hook)

            # load the script into the device
            script = session.create_script(script_gen.get_script())
            script.on('message', self.__log_script_messages)
            script.load()

        self.logger.debug('successfully started the process monitoring module ...')
