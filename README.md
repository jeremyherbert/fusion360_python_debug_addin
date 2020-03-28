# fusion360_python_debug_addin

This addin starts a HTTP server on `localhost:8181` which can launch and debug (using [PyDev.Debugger](https://github.com/fabioz/PyDev.Debugger)) python scripts inside Fusion 360. It currently only supports Mac OS but if someone compiles pydevd for Windows, it should be easy to add support for that too.

It is primarily intended for use with PyCharm and other Jetbrains IDEs.

After installing the addin, you need to tick the "Run on Startup" in the "Scripts and Add-Ins" window in Fusion 360.

To trigger a script to be run, you can simply make a HTTP POST request to the server with the correctly filled out JSON arguments. Here is an example using `curl`:

```
curl --data '{"script": "/Users/jeremy/fusion_test_script/script.py", "detach": false, "debug_port":7681}' http://localhost:8181
```

These fields are as follows:

- `script` - The absolute path to the script which will be run
- `detach` - if true, force the debugger to detach after the script has run
- `debug_port` - the port of your python debug server

## Use with PyCharm

To use this with PyCharm, create a new Run/Debug Configuration and choose the type "Remote Python Debug". Start your debug server and you should see the following in the Debug console in PyCharm:

```
Starting debug server at port 7681
Use the following code to connect to the debugger:
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=7681, stdoutToServer=True, stderrToServer=True)
Waiting for process connection...
```

Set a breakpoint in your script. Then, simply use the port listed in the Run/Debug Configuration window (also shown the Debug console output) in your HTTP request and PyCharm should break at the breakpoint in your script. 