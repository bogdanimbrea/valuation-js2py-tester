import re
import os
f = open("code.txt", "r")
raw_js = f.read()


def get_when_functions(valuation):
    functions = valuation[valuation.find(start:='$.when(')+len(start):valuation.find(').done')].replace('\n', ' ').replace(' ', '')
    return functions.split(',')


def get_done_parameters(valuation):
    params = valuation[valuation.find(start:=').done(')+len(start):valuation.find('){')].replace('\n', ' ').replace('function(', '').replace(' ', '')
    return params.split(',')


def format_raw_valuation(raw_valuation):
    # formatted_valuation = re.sub(r'Input\((.*?)\);', '_input;', raw_valuation, flags=re.DOTALL)
    formatted_valuation = re.sub(r"\$\.when\((.*?)\.done\(\n\s+function", "function _when_done", raw_valuation, flags=re.DOTALL)
    return formatted_valuation


functions = get_when_functions(raw_js)
parameters = get_done_parameters(raw_js)
urls = []
for item in functions:
    if item == 'get_cash_flow_statement()':
        urls.append("https://financialmodelingprep.com/api/v3/income-statement/INTC/?apikey=" + os.environ.get('FMP_KEY'))
    elif item == 'get_quote()':
        urls.append("https://financialmodelingprep.com/api/v3/quote/INTC?apikey=" + os.environ.get('FMP_KEY'))
responses = ['response1', 'response2']
context = {}
if len(responses) == len(parameters):
    for i in range(len(parameters)):
        context[parameters[i]] = responses[i]
print(context)






