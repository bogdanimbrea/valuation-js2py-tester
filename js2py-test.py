import js2py

input_params = "#MIN=51&MAX=52"
_input_params = {}
if input_params:
    _input_params = dict(item.split("=") for item in input_params[1:].split("&"))
for item in _input_params:
    _input_params[item] = float(_input_params[item])

js_string = """
function _SetEstimatedValue(value, ccy){console.log("_SetEstimatedValue logged"); return;}
function _StopIfWatch(value, ccy){console.log("_StopIfWatch logged"); return true;}
function print(str, label='', type=''){console.log(value);return;}
function Input(original){if(_input_params){for(key in _input_params){original[key] = _input_params[key];}}return original;}


var INPUT = Input({MIN: 5,
                   MAX: 10});

function _when_done(){
    value = Math.random() * (INPUT.MAX - INPUT.MIN) + INPUT.MIN;
    print(value);
    // If we are calculating the value per share for a watch, we can stop right here.
    if(_StopIfWatch(value, 'USD')){
      return;
    }
    _SetEstimatedValue(value, 'USD');
}
_when_done();
"""
context = js2py.EvalJs({'_input_params': _input_params})
context.execute(js_string)
