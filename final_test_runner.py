import os
from orion_compiler.compiler import compile

test_files = [f for f in os.listdir('.') if f.endswith('.orion')]

all_passed = True
for test_file in test_files:
    print(f"--- Running {test_file} ---")
    with open(test_file, 'r') as f:
        source = f.read()

    expects_error = "COMPILE_ERROR" in source
    result = compile(source)

    if expects_error:
        if result is None:
            print(f"+++ PASSED (expected failure): {test_file} +++")
        else:
            print(f"!!! FAILED (expected failure but passed): {test_file} !!!")
            all_passed = False
    else:
        if result is None:
            print(f"!!! FAILED (expected success but failed): {test_file} !!!")
            all_passed = False
        else:
            print(f"+++ PASSED: {test_file} +++")

if all_passed:
    print("\n\nAll tests passed!")
else:
    print("\n\nSome tests failed.")
