// n8n Function node: run SmartLLMCost via the Node core (metrics only) or shell out to the CLI.
// Minimal: shell out to the installed `smartllmcost` CLI and parse the JSON report.
const { execSync } = require("child_process");
function run(taskpack, preset = "openai", model = "gpt-4o") {
  const out = execSync(`smartllmcost run ${taskpack} --preset ${preset} --model ${model} --format json`,
                       { encoding: "utf8" });
  return JSON.parse(out);
}
module.exports = { run };
