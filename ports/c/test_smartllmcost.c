#include "smartllmcost.h"
#include <stdio.h>
#include <math.h>
#include <string.h>
int main(void) {
    int fails = 0;
    Attempt a[] = {{0.10,1,0,0,0},{0.05,0,0,0,0},{0.10,1,0,0,0}};
    CostResult r = cost_per_successful_task(a, 3);
    if (fabs(r.cost_per_success - 0.125) > 1e-9) { printf("FAIL cost_per_success=%f\n", r.cost_per_success); fails++; }
    Attempt none[] = {{0.2,0,0,0,0}};
    if (cost_per_successful_task(none,1).has_success) { printf("FAIL no-success\n"); fails++; }
    double vals[] = {1,2,3,4}, out;
    percentile(vals,4,50,&out);
    if (fabs(out-2.5)>1e-9) { printf("FAIL percentile=%f\n",out); fails++; }
    Attempt t = {0,0,1,0,0};
    if (strcmp(classify_failure(&t),"budget_exhaustion")) { printf("FAIL classify\n"); fails++; }
    if (!fails) printf("C port: all tests passed\n");
    return fails;
}
