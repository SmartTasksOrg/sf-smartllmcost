require_relative "smartllmcost"
r = SmartLLMCost.cost_per_successful_task([{cost_usd:0.10,success:true},{cost_usd:0.05,success:false},{cost_usd:0.10,success:true}])
raise "FAIL cps" unless (r[:cost_per_success] - 0.125).abs < 1e-9
raise "FAIL no-success" unless SmartLLMCost.cost_per_successful_task([{cost_usd:0.2,success:false}])[:cost_per_success].nil?
raise "FAIL pctile" unless (SmartLLMCost.percentile([1,2,3,4],50) - 2.5).abs < 1e-9
raise "FAIL classify" unless SmartLLMCost.classify_failure({timed_out:true}) == "budget_exhaustion"
puts "Ruby port: all tests passed"
