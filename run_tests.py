import subprocess
import sys
import os

HERE = os.path.dirname(__file__)
EXAMPLES = os.path.join(HERE, 'examples')

def run_one(path):
    print('--- Running', os.path.basename(path))
    proc = subprocess.run([sys.executable, os.path.join(HERE, 'run.py'), path], capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print('STDERR:')
        print(proc.stderr)
    print('Exit code:', proc.returncode)
    print()

def main():
    files = [f for f in os.listdir(EXAMPLES) if f.endswith('.cpp')]
    files.sort()
    for f in files:
        run_one(os.path.join(EXAMPLES, f))

if __name__ == '__main__':
    main()
