// SmartLLMCost measurement core — Java port. Mirrors python smartllmcost/metrics.py.
import java.util.*;

public class SmartLLMCost {
    public static class Attempt {
        public double costUsd; public boolean success, timedOut, hitTokenCap, error;
        public Attempt(double c, boolean s) { costUsd = c; success = s; }
    }
    public static class CostResult {
        public Double costPerSuccess; public double totalCost; public int passed, attempts;
    }

    public static Double percentile(double[] values, double p) {
        if (values.length == 0) return null;
        double[] xs = values.clone(); Arrays.sort(xs);
        if (xs.length == 1) return xs[0];
        double rank = (p / 100.0) * (xs.length - 1);
        int lo = (int) rank, hi = Math.min(lo + 1, xs.length - 1);
        return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo);
    }

    public static CostResult costPerSuccessfulTask(List<Attempt> a) {
        CostResult r = new CostResult(); r.attempts = a.size();
        double total = 0; int passed = 0;
        for (Attempt x : a) { total += x.costUsd; if (x.success) passed++; }
        r.totalCost = total; r.passed = passed;
        if (passed > 0) r.costPerSuccess = total / passed;
        return r;
    }

    public static String classifyFailure(Attempt a) {
        if (a.success) return "success";
        if (a.timedOut || a.hitTokenCap) return "budget_exhaustion";
        if (a.error) return "harness_error";
        return "verifier_failure";
    }

    // Simple self-test (run with `java SmartLLMCost` once compiled with a JDK).
    public static void main(String[] args) {
        List<Attempt> a = Arrays.asList(new Attempt(0.10, true), new Attempt(0.05, false), new Attempt(0.10, true));
        CostResult r = costPerSuccessfulTask(a);
        assert Math.abs(r.costPerSuccess - 0.125) < 1e-9;
        assert costPerSuccessfulTask(Arrays.asList(new Attempt(0.2, false))).costPerSuccess == null;
        assert Math.abs(percentile(new double[]{1,2,3,4}, 50) - 2.5) < 1e-9;
        System.out.println("Java port: all tests passed");
    }
}
