var base_addr = Module.findExportByName('libc.so', 'read');
Interceptor.attach(base_addr, {

        onEnter: function (args) {

        },

        onLeave: function (retval) {

        }
    }
);