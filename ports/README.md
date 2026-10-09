# Ports

The measurement core (percentiles, cost-per-successful-task, failure classification) is
reimplemented per language so results are identical everywhere. **Python is the reference.**

Canonical cross-language check (every port):
`cost_per_successful_task([{0.10,pass},{0.05,fail},{0.10,pass}]) = 0.125`
and `percentile([1,2,3,4], 50) = 2.5`.

| Port | Status | How to test |
|------|--------|-------------|
| Python (`src/sf_smartllmcost`) | ✅ reference, verified | `pytest` |
| Node (`ports/node`) | ✅ verified here | `node --test` |
| C (`ports/c`) | ✅ compiled + run here | `make test` (gcc) |
| C++ (`ports/cpp`) | ✅ compiled + run here | `make test` (g++ -std=c++17) |
| Go (`ports/go`) | ⏳ written to `go test` standard, unrun | `go test ./...` |
| Java (`ports/java`) | ⏳ written, unrun (no javac here) | `javac SmartLLMCost.java && java SmartLLMCost` |
| Ruby (`ports/ruby`) | ⏳ written, unrun | `ruby test_smartllmcost.rb` |
| Rust (`ports/rust`) | ⏳ written to `cargo test` standard, unrun | `cargo test` (add a Cargo.toml) |
| PHP (`ports/php`) | ⏳ written, unrun | include + call |
| C# (`ports/csharp`) | ⏳ written, unrun | `dotnet test` (add a project) |

✅ = compiled and its tests passed in this environment. ⏳ = written to the language's
standard test framework but not executed here (toolchain unavailable); verify on your box.
