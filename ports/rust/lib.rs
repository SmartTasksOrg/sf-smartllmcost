//! SmartLLMCost measurement core — Rust port. Mirrors python smartllmcost/metrics.py.
pub struct Attempt { pub cost_usd: f64, pub success: bool, pub timed_out: bool, pub hit_token_cap: bool, pub error: bool }
pub struct CostResult { pub cost_per_success: Option<f64>, pub total_cost: f64, pub passed: usize, pub attempts: usize }

pub fn percentile(values: &[f64], p: f64) -> Option<f64> {
    if values.is_empty() { return None; }
    let mut xs = values.to_vec();
    xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
    if xs.len() == 1 { return Some(xs[0]); }
    let rank = (p / 100.0) * (xs.len() - 1) as f64;
    let lo = rank as usize;
    let hi = (lo + 1).min(xs.len() - 1);
    Some(xs[lo] + (xs[hi] - xs[lo]) * (rank - lo as f64))
}

pub fn cost_per_successful_task(a: &[Attempt]) -> CostResult {
    let total: f64 = a.iter().map(|x| x.cost_usd).sum();
    let passed = a.iter().filter(|x| x.success).count();
    CostResult { cost_per_success: if passed > 0 { Some(total / passed as f64) } else { None },
                 total_cost: total, passed, attempts: a.len() }
}

pub fn classify_failure(a: &Attempt) -> &'static str {
    if a.success { "success" }
    else if a.timed_out || a.hit_token_cap { "budget_exhaustion" }
    else if a.error { "harness_error" }
    else { "verifier_failure" }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn cps() {
        let a = vec![Attempt{cost_usd:0.10,success:true,timed_out:false,hit_token_cap:false,error:false},
                     Attempt{cost_usd:0.05,success:false,timed_out:false,hit_token_cap:false,error:false},
                     Attempt{cost_usd:0.10,success:true,timed_out:false,hit_token_cap:false,error:false}];
        assert!((cost_per_successful_task(&a).cost_per_success.unwrap() - 0.125).abs() < 1e-9);
    }
    #[test] fn pctile() { assert!((percentile(&[1.0,2.0,3.0,4.0],50.0).unwrap()-2.5).abs()<1e-9); }
}
