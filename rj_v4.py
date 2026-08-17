#!/usr/bin/env python3
"""Re-judge BioMniBench results with Gemini. Correct parsing + negative levels."""
import json, os, time, re, httpx
from pathlib import Path
from openai import OpenAI, RateLimitError, APIError

GEMINI_MODEL = "Vendor2/Gemini-3.1-pro"
API_KEY = "00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
BASE_URL = "https://api.gpugeek.com/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL,
    http_client=httpx.Client(timeout=httpx.Timeout(300.0, connect=60.0)))

def parse_rubric_levels(rubric_text):
    out = {}
    parts = re.split(r"^Criterion\s+(\d+)\s*:", rubric_text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        n = parts[i].strip()
        body = parts[i+1] if i+1 < len(parts) else ""
        levels = {}
        for m in re.finditer(r"([A-Z])\s*=\s*(-?\d+)", body):
            levels[m.group(1).upper()] = int(m.group(2))
        if not levels:
            for m in re.finditer(r"\[([A-Z])\]\s*\(\s*(-?\d+)\s*points?\s*\)", body):
                levels[m.group(1).upper()] = int(m.group(2))
        if levels:
            out[f"criterion_{n}"] = levels
    return out

def find_rubric_file(summary_path):
    parent = os.path.dirname(os.path.dirname(summary_path))
    task_name = os.path.basename(parent)
    for base in [parent, os.path.dirname(parent)]:
        for jp in [
            os.path.join(base, ".judge_private", task_name, "evaluation", "rubric.txt"),
            os.path.join(base, ".judge_private", "evaluation", "rubric.txt"),
        ]:
            if os.path.exists(jp):
                return jp
    return None

def rejudge_one(summary_path):
    data = json.load(open(summary_path))
    run_dir = os.path.dirname(os.path.dirname(summary_path))
    trace_file = os.path.join(run_dir, "outputs", "trace.md")
    answer_file = os.path.join(run_dir, "outputs", "answer.txt")
    rubric_file = find_rubric_file(summary_path)
    if not os.path.exists(trace_file) and not os.path.exists(answer_file):
        return None, "no trace/answer"
    if not rubric_file:
        return None, "no rubric"
    run_name = os.path.basename(run_dir)
    task_id = run_name.split("_")[0]
    arm = "base" if "baseline" in run_name else "skill"
    rubric = Path(rubric_file).read_text()
    trace_content = Path(trace_file).read_text() if Path(trace_file).exists() else ""
    answer_content = Path(answer_file).read_text() if Path(answer_file).exists() else ""
    if len(trace_content) > 30000:
        trace_content = trace_content[:30000] + "\n...[truncated]"
    prompt = f"""You are an expert evaluator for a data analysis task.

Evaluate the agent's work using the following rubric:

{rubric}

Here is the agent's analysis trace:

<trace>
{trace_content if trace_content else "[No trace file provided]"}
</trace>

Here is the agent's final answer:

<answer>
{answer_content if answer_content else "[No answer file provided]"}
</answer>

For each criterion in the rubric, choose ONE level: A, B, or C. Only output JSON with the format:
{{
  "criteria": {{
    "criterion_1": {{"level": "A", "reasoning": "..."}},
    "criterion_2": {{"level": "B", "reasoning": "..."}}
  }},
  "overall_reasoning": "..."
}}"""
    for attempt in range(15):
        try:
            response = client.chat.completions.create(
                model=GEMINI_MODEL, max_tokens=8192, temperature=0.3,
                messages=[{"role": "user", "content": prompt}])
            response_text = response.choices[0].message.content
            break
        except (RateLimitError, APIError) as e:
            wait = min(10 * (2 ** attempt), 180)
            print(f"  RL a{attempt+1} w{wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:
            if attempt < 14:
                wait = 20 * (attempt + 1)
                print(f"  ERR a{attempt+1} {str(e)[:60]}", flush=True)
                time.sleep(wait)
            else:
                raise
    start_idx = response_text.find("{")
    if start_idx >= 0:
        bc, ei = 0, start_idx
        for i, c in enumerate(response_text[start_idx:], start_idx):
            if c == "{": bc += 1
            elif c == "}": bc -= 1
            if bc == 0: ei = i + 1; break
        result = json.loads(response_text[start_idx:ei])
    else:
        result = json.loads(response_text)
    criteria = result.get("criteria", {})
    criterion_levels = parse_rubric_levels(rubric)
    total_score = 0
    for ck, cd in criteria.items():
        if not isinstance(cd, dict): continue
        lv = cd.get("level", "C").upper()
        if ck in criterion_levels and lv in criterion_levels[ck]:
            total_score += criterion_levels[ck][lv]
    reward = total_score / 100.0
    data["final_result"] = {
        "total_score": total_score, "max_score": 100,
        "criteria": criteria, "model": GEMINI_MODEL,
        "overall_reasoning": result.get("overall_reasoning", ""),
    }
    data["reward"] = reward
    json.dump(data, open(summary_path, "w"), indent=2, ensure_ascii=False)
    print(f"  [{arm}] {task_id}: r={reward:.3f} ({total_score}/100)", flush=True)
    return True, None

def main():
    dirs = ["baseline", "with-skill"]
    all_s = []
    for d in dirs:
        if os.path.isdir(d):
            for root, dirs2, files in os.walk(d):
                if "run_summary.json" in files:
                    all_s.append(os.path.join(root, "run_summary.json"))
    all_s.sort(key=lambda p: os.path.basename(os.path.dirname(os.path.dirname(p))))
    print(f"FOUND {len(all_s)} run_summary.json files", flush=True)
    ok = err = 0
    for i, sp in enumerate(all_s):
        print(f"[{i+1}/{len(all_s)}] ", end="", flush=True)
        try:
            success, reason = rejudge_one(sp)
            if success: ok += 1
            else:
                print(f"  SKIP ({reason})", flush=True)
                err += 1
        except Exception as e:
            print(f"  FATAL: {e}", flush=True)
            err += 1
        time.sleep(3.0)
    print(f"\nDONE: {ok} OK, {err} skipped/failed", flush=True)

if __name__ == "__main__":
    main()