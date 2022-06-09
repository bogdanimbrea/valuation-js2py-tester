import re
import asyncio
import aiohttp
import json
import os
import js2py
import datetime


def get_when_functions(valuation):
    functions = valuation[valuation.find(start := '$.when') + len(start):valuation.find('.done')].replace('(', '').replace(')', '').replace('\n', '').replace(' ', '').replace('\r','')
    return functions.split(',')


def get_done_parameters(valuation):
    ix = valuation.find(start := '.done') + len(start)
    done_start = valuation[ix:].find('(') + ix + 1
    done_end = valuation[done_start:].find(')') + done_start
    params = valuation[done_start:done_end].replace('\n', '').replace('function', '').replace('(','').replace(' ', '').replace('\r','').strip(',')
    return params.split(',')


def format_raw_valuation(valuation):
    index_start = valuation.find(start := '$.when(')
    index_end = index_start + len(start) + valuation[index_start:].find('{') - 1
    # also remove the ');' from function .done()
    brackets = 1
    for i in range(index_end, len(valuation)):
        if valuation[i] == '{':
            brackets += 1
        if valuation[i] == '}':
            brackets -= 1
        if valuation[i] == ')' and brackets == 0:
            # now find ; and delete it as well
            for j in range(i, len(valuation)):
                if valuation[j] == ';':
                    valuation = valuation[:i] + valuation[j + 1:]
                    break
            break
    if len(valuation) > index_end and index_start <= index_end - 1:
        valuation = valuation[0:index_start] + 'function _when_done(){' + valuation[index_end - 1:]

    # remove Description () if it has it
    valuation = re.sub(r"`(.*?)`", "", valuation, flags=re.DOTALL)
    index_start = valuation.find(start := 'Description(') + len(start)
    if index_start:
        parenthesis = 1
        for i in range(index_start, len(valuation)):
            if valuation[i] == '(':
                parenthesis += 1
            elif valuation[i] == ')':
                parenthesis -= 1
            if valuation[i] == ')' and parenthesis == 0:
                valuation = valuation[0:index_start] + "''" + valuation[i:]
                break

    return valuation


async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def get_async(url, session):
    # use GET instead of POST
    async with session.get(url) as response:
        text = await response.text()
        return json.loads(text)


async def async_api_get(urls):
    conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    conc_req = len(urls)
    responses = await gather_with_concurrency(conc_req, *[get_async(url, session) for url in urls])
    await session.close()
    return responses


if __name__ == "__main__":
    # Open file
    f = open("code.txt", "r")
    raw_js = f.read()

    # Retrieve URLs and put them into context
    functions = get_when_functions(raw_js)
    parameters = get_done_parameters(raw_js)
    print(parameters)
    print(functions)
    urls = []
    ticker = 'AAPL'
    for item in functions:
        if item == 'get_cash_flow_statement':
            urls.append("https://financialmodelingprep.com/api/v3/cash-flow-statement/" + ticker.upper() + "/?apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_quote':
            urls.append("https://financialmodelingprep.com/api/v3/quote/" + ticker.upper() + "?apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_profile':
            urls.append("https://financialmodelingprep.com/api/v3/profile/" + ticker.upper() + "?apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_income_statement':
            urls.append("https://financialmodelingprep.com/api/v3/income-statement/" + ticker.upper() + "?apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_balance_sheet_statement':
            urls.append("https://financialmodelingprep.com/api/v3/balance-sheet-statement/" + ticker.upper() + "?apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_income_statement_quarterly':
            urls.append("https://financialmodelingprep.com/api/v3/income-statement/" + ticker.upper() + "?period=quarter&apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_balance_sheet_statement_quarterly':
            urls.append("https://financialmodelingprep.com/api/v3/balance-sheet-statement/" + ticker.upper() + "?period=quarter&apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_cash_flow_statement_quarterly':
            urls.append("https://financialmodelingprep.com/api/v3/cash-flow-statement/" + ticker.upper() + "?period=quarter&apikey=" + os.environ.get('FMP_KEY'))
        elif item == 'get_income_statement_ltm':
            urls.append("https://discountingcashflows.com/api/income-statement/ltm/" + ticker.upper() + "/")
        elif item == 'get_cash_flow_statement_ltm':
            urls.append("https://discountingcashflows.com/api/cash-flow-statement/ltm/" + ticker.upper() + "/")
        elif item == 'get_treasury':
            to_date = datetime.datetime.today().strftime('%Y-%m-%d')
            urls.append("https://financialmodelingprep.com/api/v4/treasury?to=" + to_date + "&apikey=" + os.environ.get('FMP_KEY'))

    responses = asyncio.get_event_loop().run_until_complete(async_api_get(urls))
    context = {}

    if len(responses) == len(parameters):
        for i in range(len(parameters)):
            # TODO: income[0] stuff (remove [])
            context[parameters[i]] = [responses[i]]

    _input_params = {}
    context['_input_params'] = _input_params
    # print(context)
    context = js2py.EvalJs(context)

    # After we have the context, we need to format the raw js valuation
    append_functions = """
    function monitor(context){return;}
    function Description(text){return '';}
    function _SetEstimatedValue(value, ccy){console.log("_SetEstimatedValue log: " + value + ccy); return;}
    function _StopIfWatch(value, ccy){console.log("_StopIfWatch log: " + value + ccy); return true;}
    function print(str, label, type){console.log(str);return;}
    function Input(original){if(_input_params){for(key in _input_params){original[key] = _input_params[key];}}for(key in original){if(key[0] == '_' && original[key] != '-' && typeof original[key] == 'number'){original[key] /= 100;}}return original;}
    """

    # LOOKOUT for replace_with... functions for reports and create DEEP COPIES of them
    # example:
    # function (income, flows){ income = replace_with_ltm(income) }
    # replace_with_ltm will alter the cached data of income report
    formatted_valuation = format_raw_valuation(raw_js)
    formatted_valuation = append_functions + formatted_valuation + '\n_when_done();'
    print(formatted_valuation)
    context.execute(formatted_valuation)

    print("Done")
