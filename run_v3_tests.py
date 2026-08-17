"""Run v3 tests - check and execute"""
import subprocess, json, sys, os

SERVER = "server1"
REMOTE = "/tmp/run_remote.py"

def ssh(cmd, timeout=7200):
    full = ['ssh', SERVER, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode

def check():
    pycode = """
import json, glob
base = '/data/yjh/skill-transfer-eval/generalized'
idx = json.load(open('/data/yjh/skill-transfer-eval/results_index.json'))
bl = {t: v['gemini']/100.0 for t,v in idx.get('baselines',{}).items()}
v3 = {'da-19-6':'da-19-1','da-8-3':'da-8-2','da-17-5':'da-17-1','da-14-8':'da-14-3','da-17-3':'da-17-1','da-20-4':'da-20-1'}
v2 = {'da-19-6':'da-19-1','da-8-3':'da-8-2','da-17-5':'da-13-5','da-14-8':'da-14-3','da-17-3':'da-17-1','da-20-4':'da-6-2'}
need_run = []
for tgt, src in v3.items():
    if src == v2.get(tgt):
        pat = f'{base}/{tgt}_batch_v2*/logs/run_summary.json'
        ms = sorted(glob.glob(pat))
        if ms:
            s = json.load(open(ms[0]))
            r = s.get('reward', 0)
            d = r - bl.get(tgt, 0)
            v = 'HELP' if d > 0.05 else ('HARM' if d < -0.05 else 'NEUT')
            print(f'EXISTS: {src}->{tgt} reward={r:.3f} bl={bl.get(tgt,0):.3f} delta={d:+.3f} {v}')
        else:
            print(f'MISSING: {src}->{tgt} (same as v2 but no result)')
            need_run.append(tgt)
    else:
        print(f'NEW: {src}->{tgt} (v2 had {v2.get(tgt)})')
        need_run.append(tgt)
print('NEED_RUN:' + json.dumps(need_run))
"""
    out, err, rc = ssh(f'python3 -c {json.dumps(pycode)}')
    return out, err, rc

def run_eval(target, timeout=3600):
    cmd = f'cd /tmp && python3 {REMOTE} --target {target} --smart --feedback --timeout {timeout}'
    print(f'Starting: {target} (timeout={timeout}s)')
    out, err, rc = ssh(cmd, timeout=timeout+300)
    return out, err, rc

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        target = sys.argv[2]
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
        print(f'=== Running {target} ===')
        out, err, rc = run_eval(target, timeout)
        print(f'RC={rc}')
        print(f'STDOUT(last 3000):\n{out[-3000:]}')
        if err:
            print(f'STDERR(last 500):\n{err[-500:]}')
    else:
        print('=== Checking v3 test status ===')
        out, err, rc = check()
        print(f'STDOUT:\n{out}')
        if err:
            print(f'STDERR:\n{err[-500:]}')
        print(f'RC={rc}')