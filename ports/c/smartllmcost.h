#ifndef SMARTLLMCOST_H
#define SMARTLLMCOST_H
typedef struct { double cost_usd; int success; int timed_out; int hit_token_cap; int error; } Attempt;
typedef struct { double cost_per_success; int has_success; double total_cost; int passed; int attempts; } CostResult;
int percentile(const double *values, int n, double p, double *out);
CostResult cost_per_successful_task(const Attempt *a, int n);
const char *classify_failure(const Attempt *a);
#endif
