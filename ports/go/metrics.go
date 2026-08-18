// Package smartllmcost — measurement core, Go port. Mirrors python smartllmcost/metrics.py.
package smartllmcost

import "sort"

type Attempt struct {
	CostUSD    float64
	Success    bool
	TimedOut   bool
	HitTokenCap bool
	Error      string
}

func Percentile(values []float64, p float64) (float64, bool) {
	xs := append([]float64(nil), values...)
	sort.Float64s(xs)
	if len(xs) == 0 {
		return 0, false
	}
	if len(xs) == 1 {
		return xs[0], true
	}
	rank := (p / 100.0) * float64(len(xs)-1)
	lo := int(rank)
	hi := lo + 1
	if hi > len(xs)-1 {
		hi = len(xs) - 1
	}
	return xs[lo] + (xs[hi]-xs[lo])*(rank-float64(lo)), true
}

type CostResult struct {
	CostPerSuccess float64
	HasSuccess     bool
	TotalCost      float64
	Passed         int
	Attempts       int
}

func CostPerSuccessfulTask(attempts []Attempt) CostResult {
	total := 0.0
	passed := 0
	for _, a := range attempts {
		total += a.CostUSD
		if a.Success {
			passed++
		}
	}
	if passed == 0 {
		return CostResult{HasSuccess: false, TotalCost: total, Passed: 0, Attempts: len(attempts)}
	}
	return CostResult{CostPerSuccess: total / float64(passed), HasSuccess: true,
		TotalCost: total, Passed: passed, Attempts: len(attempts)}
}

func ClassifyFailure(a Attempt) string {
	if a.Success {
		return "success"
	}
	if a.TimedOut || a.HitTokenCap {
		return "budget_exhaustion"
	}
	if a.Error != "" {
		return "harness_error"
	}
	return "verifier_failure"
}
