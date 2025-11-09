import pytest
import os
from orion_compiler.compiler import compile, TypeAnalyzer
from orion_compiler.vm import VM

def run_orion_file(filepath):
    with open(filepath, 'r') as f:
        source = f.read()

    vm = VM()
    native_module_specs = {name: {field: "function" for field in mod.keys()} for name, mod in vm.native_modules.items()}
    type_analyzer = TypeAnalyzer(native_module_specs)

    result = compile(source, type_analyzer)

    # This is the crucial part for the typing test
    if "typing_test.orion" in filepath:
        assert result is None, f"Typing test should fail compilation, but it passed for {filepath}"
    else:
        assert result is not None, f"Compilation failed for {filepath}"

# Discover all .orion files in the tests directory
orion_test_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk('tests') for f in filenames if f.endswith('.orion')]

@pytest.mark.parametrize("filepath", orion_test_files)
def test_orion_file(filepath):
    run_orion_file(filepath)
