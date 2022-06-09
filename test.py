valuation = """
function replace_with_ltm(report, ltm){
  $.each(ltm, function(key, value) {
    if ( $.isNumeric(value) ){
      report[0][key] = ltm[key]
    }
  });
  return report;
}
$.when(
  get_cash_flow_statement(),
  get_quote()).done(
  function(flows, quote){
    var context = [];
    for(var i=0; i<income.length; i++){
      linRevenue[i] = (income[income.length - i -1]['revenue'] - linRevenue[i])*INPUT._REVENUE_TRACKING_RATIO + linRevenue[i];
      if(linRevenue[i] < 0){linRevenue[i] = 0;}
    }
  }
  );
"""
index_start = valuation.find(start := '$.when(')
index_end = index_start + len(start) + valuation[index_start:].find('{') - 1
# remove the ) from function done()
brackets = 1
for i in range(index_end, len(valuation)):
    print(valuation[i])
    if valuation[i] == '{':
        brackets += 1
    if valuation[i] == '}':
        brackets -= 1
    if valuation[i] == ')' and brackets == 0:
        # now find ; and delete it as well
        for j in range(i, len(valuation)):
            if valuation[j] == ';':
                valuation = valuation[:i] + valuation[j+1:]
                break
        break
print(index_start)
print(index_end)

if len(valuation) > index_end and index_start <= index_end - 1:
    valuation = valuation[0:index_start] + 'function _when_done(){' + valuation[index_end - 1:]

print(valuation)
