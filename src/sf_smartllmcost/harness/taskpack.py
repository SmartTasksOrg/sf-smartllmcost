"""Native SmartBench task-pack — the format that matters most (a company's OWN jobs).

A task-pack is JSON: {"name","version","tasks":[{"id","prompt","check"}]}. `check` is a
simple, transparent acceptance test so success is reproducible:
  {"type":"contains","value":"..."} | {"type":"equals","value":"..."}
  {"type":"regex","value":"..."} | {"type":"json_path","path":"a.b","value":...}
External harnesses (lm-eval-harness, HELM, SWE-bench) plug in via adapters/ that convert
their tasks into this shape, so the cost/timing math is identical across all of them.
"""
from __future__ import annotations
import json
import re


class TaskPack:
    def __init__(self, name, version, tasks):
        self.name = name
        self.version = version
        self.tasks = tasks

    def __len__(self):
        return len(self.tasks)


def load_taskpack(path_or_obj):
    d = path_or_obj if isinstance(path_or_obj, dict) else json.load(open(path_or_obj, encoding="utf-8"))
    tasks = d.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("task-pack 'tasks' must be a list")
    return TaskPack(d.get("name", "unnamed"), d.get("version", "0"), tasks)


def validate_taskpack(path_or_obj):
    """Return a list of problems (empty = valid). Used by the `validate` CLI command."""
    tp = load_taskpack(path_or_obj)
    problems = []
    if not tp.tasks:
        problems.append("no tasks")
    ids = set()
    for i, t in enumerate(tp.tasks):
        if not isinstance(t, dict):
            problems.append(f"task {i}: not an object"); continue
        if not t.get("prompt"):
            problems.append(f"task {t.get('id', i)}: missing 'prompt'")
        chk = t.get("check")
        if chk and chk.get("type") not in ("contains", "equals", "regex", "json_path", None):
            problems.append(f"task {t.get('id', i)}: unknown check type {chk.get('type')}")
        tid = t.get("id", i)
        if tid in ids:
            problems.append(f"duplicate task id: {tid}")
        ids.add(tid)
    return problems


def check_output(text, check):
    """Transparent acceptance check → bool. This IS the verifier; success is auditable."""
    if not check:
        return True
    t = check.get("type", "contains")
    v = check.get("value")
    text = text or ""
    if t == "contains":
        return str(v).lower() in text.lower()
    if t == "equals":
        return text.strip() == str(v).strip()
    if t == "regex":
        return re.search(v, text) is not None
    if t == "json_path":
        try:
            obj = json.loads(text)
            for k in check.get("path", "").split("."):
                obj = obj[k] if k else obj
            return obj == v
        except Exception:
            return False
    return False
