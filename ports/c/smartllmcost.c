/* SmartLLMCost measurement core — C port. Mirrors python smartllmcost/metrics.py.
   Canonical check: cost_per_successful_task([{0.10,pass},{0.05,fail},{0.10,pass}]) = 0.125 */
#include "smartllmcost.h"
#include <stdlib.h>

static int cmp_double(const void *a, const void *b) {
    double da = *(const double *)a, db = *(const double *)b;
    return (da > db) - (da < db);
}

int percentile(const double *values, int n, double p, double *out) {
    if (n <= 0) return 0;
    double *xs = (double *)malloc(sizeof(double) * n);
    for (int i = 0; i < n; i++) xs[i] = values[i];
    qsort(xs, n, sizeof(double), cmp_double);
    if (n == 1) { *out = xs[0]; free(xs); return 1; }
    double rank = (p / 100.0) * (n - 1);
    int lo = (int)rank;
    int hi = lo + 1; if (hi > n - 1) hi = n - 1;
    *out = xs[lo] + (xs[hi] - xs[lo]) * (rank - lo);
    free(xs);
    return 1;
}

CostResult cost_per_successful_task(const Attempt *a, int n) {
    CostResult r = {0.0, 0, 0.0, 0, n};
    double total = 0.0; int passed = 0;
    for (int i = 0; i < n; i++) { total += a[i].cost_usd; if (a[i].success) passed++; }
    r.total_cost = total; r.passed = passed;
    if (passed == 0) { r.has_success = 0; return r; }
    r.has_success = 1; r.cost_per_success = total / passed;
    return r;
}

const char *classify_failure(const Attempt *a) {
    if (a->success) return "success";
    if (a->timed_out || a->hit_token_cap) return "budget_exhaustion";
    if (a->error) return "harness_error";
    return "verifier_failure";
}
