import os
import sys
from orion_compiler.compiler import compile

def run_tests():
    # Find all .orion files in the root and tests/ directories
    test_files = [f for f in os.listdir('.') if f.endswith('.orion')]
    if os.path.isdir('tests'):
        test_files.extend([os.path.join('tests', f) for f in os.listdir('tests') if f.endswith('.orion')])

    all_passed = True
    failed_tests = []

    for test_file in test_files:
        print(f"--- Running {test_file} ---")
        with open(test_file, 'r') as f:
            source = f.read()

        expects_error = "COMPILE_ERROR" in source
        result = compile(source)

        test_passed = False
        if expects_error:
            if result is None:
                print(f"+++ PASSED (expected failure): {test_file} +++")
                test_passed = True
            else:
                print(f"!!! FAILED (expected failure but passed): {test_file} !!!")
        else:
            if result is None:
                print(f"!!! FAILED (expected success but failed): {test_file} !!!")
            else:
                print(f"+++ PASSED: {test_file} +++")
                test_passed = True

        if not test_passed:
            all_passed = False
            failed_tests.append(test_file)

    if all_passed:
        print("\n\nAll tests passed!")
        sys.exit(0)
    else:
        print(f"\n\nSome tests failed: {', '.join(failed_tests)}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
