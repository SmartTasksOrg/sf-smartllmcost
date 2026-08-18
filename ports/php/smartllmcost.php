<?php
// SmartLLMCost measurement core — PHP port. Mirrors python smartllmcost/metrics.py.
function percentile(array $values, float $p) {
    $xs = array_values(array_filter($values, fn($v) => $v !== null));
    sort($xs);
    $n = count($xs);
    if ($n === 0) return null;
    if ($n === 1) return $xs[0];
    $rank = ($p / 100.0) * ($n - 1);
    $lo = (int)$rank;
    $hi = min($lo + 1, $n - 1);
    return $xs[$lo] + ($xs[$hi] - $xs[$lo]) * ($rank - $lo);
}
function cost_per_successful_task(array $attempts): array {
    $total = array_sum(array_map(fn($a) => $a['cost_usd'] ?? 0.0, $attempts));
    $passed = count(array_filter($attempts, fn($a) => $a['success'] ?? false));
    if ($passed === 0) return ['cost_per_success' => null, 'total_cost' => $total, 'passed' => 0, 'attempts' => count($attempts)];
    return ['cost_per_success' => $total / $passed, 'total_cost' => $total,
            'passed' => $passed, 'attempts' => count($attempts), 'success_rate' => $passed / count($attempts)];
}
function classify_failure(array $a): string {
    if ($a['success'] ?? false) return 'success';
    if (($a['timed_out'] ?? false) || ($a['hit_token_cap'] ?? false)) return 'budget_exhaustion';
    if ($a['error'] ?? false) return 'harness_error';
    return 'verifier_failure';
}
