#include "smartllmcost.hpp"
#include <cmath>
#include <iostream>
using namespace smartllmcost;
int main() {
    int fails = 0;
    auto r = cost_per_successful_task({{0.10,true},{0.05,false},{0.10,true}});
    if (!r.cost_per_success || std::abs(*r.cost_per_success - 0.125) > 1e-9) { std::cout << "FAIL cps\n"; fails++; }
    auto none = cost_per_successful_task({{0.2,false}});
    if (none.cost_per_success.has_value()) { std::cout << "FAIL no-success\n"; fails++; }
    auto p = percentile({1,2,3,4}, 50);
    if (!p || std::abs(*p - 2.5) > 1e-9) { std::cout << "FAIL pctile\n"; fails++; }
    if (classify_failure({0,false,true}) != "budget_exhaustion") { std::cout << "FAIL classify\n"; fails++; }
    if (!fails) std::cout << "C++ port: all tests passed\n";
    return fails;
}
