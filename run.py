import sys
from src.parser import Parser
from src.semantic import SemanticAnalyzer


def main():
    if len(sys.argv) < 2:
        print('Usage: python run.py <source.cpp>')
        sys.exit(1)
    path = sys.argv[1]
    code = open(path, 'r', encoding='utf8').read()
    parser = Parser(code)
    try:
        prog = parser.parse()
    except Exception as e:
        print('Parse error:', e)
        sys.exit(1)
    print('Parsed AST:')
    print(prog)
    sem = SemanticAnalyzer(prog)
    sem.analyze()
    if sem.errors:
        print('\nSemantic errors:')
        for e in sem.errors:
            print('-', e)
    else:
        print('\nNo semantic errors detected.')


if __name__ == '__main__':
    main()
