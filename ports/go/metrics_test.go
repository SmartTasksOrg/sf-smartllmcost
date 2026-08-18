package smartllmcost

import "testing"

func TestCostPerSuccessCountsFailedSpend(t *testing.T) {
	r := CostPerSuccessfulTask([]Attempt{{CostUSD: 0.10, Success: true}, {CostUSD: 0.05, Success: false}, {CostUSD: 0.10, Success: true}})
	if r.CostPerSuccess != 0.125 {
		t.Fatalf("want 0.125, got %v", r.CostPerSuccess)
	}
}
func TestNoSuccess(t *testing.T) {
	r := CostPerSuccessfulTask([]Attempt{{CostUSD: 0.2, Success: false}})
	if r.HasSuccess {
		t.Fatal("expected no success")
	}
}
func TestClassify(t *testing.T) {
	if ClassifyFailure(Attempt{TimedOut: true}) != "budget_exhaustion" {
		t.Fatal("timeout should be budget_exhaustion")
	}
}
