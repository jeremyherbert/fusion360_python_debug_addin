# SPDX-License-Identifier: MIT

import adsk.core
import adsk.fusion
import importlib
import traceback
import os
import sys
import tempfile

import threading

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# add pydevd to path
this_script_dir = os.path.dirname(os.path.realpath(__file__))

if sys.platform == "darwin":
    # mac
    sys.path.append(os.path.join(this_script_dir, "pydevd_lib.macosx-10.9-x86_64-3.7"))
    sys.path.append(os.path.join(this_script_dir, "pydevd_lib.macosx-10.9-x86_64-3.7", "pydevd_attach_to_process"))
else:
    # windows
    pass

# run log path
script_run_log_path = os.path.join(tempfile.gettempdir(), "fusion360_python_debug_addin_log.txt")

# name of asynchronous even which will be used to launch a script inside fusion 360
custom_event_name = 'fusion360_python_debug_addin_run_script'


class ThreadEventHandler(adsk.core.CustomEventHandler):
    """
    An event handler which can run a python script in the main thread of fusion 360.
    """
    def notify(self, args):
        try:
            args = json.loads(args.additionalInfo)
            script_path = os.path.abspath(args['script'])
            detach = args['detach']
            if os.path.isfile(script_path):
                script_name = os.path.splitext(os.path.basename(script_path))[0]
                script_dir = os.path.dirname(script_path)

                sys.path.append(script_dir)
                try:
                    import attach_script
                    attach_script.attach(args['debug_port'], 'localhost')

                    module = importlib.import_module(script_name)
                    importlib.reload(module)
                    module.run({'isApplicationStartup': False})
                finally:
                    del sys.path[-1]
                    if detach:
                        try:
                            import pydevd
                            pydevd.stoptrace()
                        except:
                            pass
        except:
            with open(script_run_log_path, 'w') as f:
                f.write(traceback.format_exc())


class FusionInjectorHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    A HTTP request handler which queues an event in the main thread of fusion 360 (event is to run a script)
    """
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        try:
            request_data = json.loads(body.decode())

            assert "script" in request_data
            assert "detach" in request_data
            assert "debug_port" in request_data

            adsk.core.Application.get().fireCustomEvent(custom_event_name, json.dumps(request_data))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"done")
        except:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())


def run_server():
    server_address = ('localhost', 8181)
    httpd = HTTPServer(server_address, FusionInjectorHTTPRequestHandler)
    httpd.serve_forever()


handlers = []

def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        if sys.platform != "darwin":
            raise NotImplementedError("Windows support not implemented")

        try:
            app.unregisterCustomEvent(custom_event_name)
        except:
            pass

        # set up fusion 360 callback
        custom_event = app.registerCustomEvent(custom_event_name)
        event_handler = ThreadEventHandler()
        custom_event.add(event_handler)
        handlers.append(event_handler)  # prevent instance from being garbage collected

        http_server_thread = threading.Thread(target=run_server, daemon=True)
        http_server_thread.start()

        ui.messageBox('addin started')
    except:
        if ui:
            ui.messageBox(('AddIn Start Failed: {}').format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

    except:
        if ui:
            ui.messageBox(('AddIn Stop Failed: {}').format(traceback.format_exc()))