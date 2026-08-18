import { test } from "node:test";
import assert from "node:assert";
import { percentile, costPerSuccessfulTask, classifyFailure } from "./metrics.mjs";

test("percentile interpolates", () => { assert.strictEqual(percentile([1,2,3,4], 50), 2.5); });
test("cost per success counts failed spend", () => {
  const r = costPerSuccessfulTask([{cost_usd:0.10,success:true},{cost_usd:0.05,success:false},{cost_usd:0.10,success:true}]);
  assert.strictEqual(r.cost_per_success, 0.125);
});
test("no success is null not zero", () => {
  assert.strictEqual(costPerSuccessfulTask([{cost_usd:0.2,success:false}]).cost_per_success, null);
});
test("failure classification", () => {
  assert.strictEqual(classifyFailure({timed_out:true}), "budget_exhaustion");
  assert.strictEqual(classifyFailure({success:false}), "verifier_failure");
});
