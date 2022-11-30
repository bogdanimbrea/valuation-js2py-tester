import js2py
import errno
import os
import signal
import functools

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


# Timeout after 5 seconds
@timeout(5)
def long_running_function2(js_string):
    js2py.eval_js(js_string)

x = 2

js_string = """
    /* A Very Simple Example */
    while(1){console.log('asdfasdfasdfas');}
"""

#context = js2py.EvalJs({'_input_params': _input_params})
# js2py.eval_js(js_string)
long_running_function2(js_string)
print(x)
