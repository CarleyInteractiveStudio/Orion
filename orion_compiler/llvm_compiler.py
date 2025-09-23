from llvmlite import binding
from .lexer import Lexer
from .parser import Parser
from .llvm_backend import LLVMBackend

def compile_to_llvm_ir(source: str):
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    backend = LLVMBackend()
    backend.generate(statements)
    return backend.module

def compile_orion_to_object_file(source: str, output_filename: str):
    """
    Compiles Orion source code to an object file.
    """
    llvm_ir = compile_to_llvm_ir(source)

    print("--- LLVM IR ---")
    print(llvm_ir)

    # Initialize the target machine
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()

    # Compile the module to an object file
    parsed_module = binding.parse_assembly(str(llvm_ir))
    obj_code = target_machine.emit_object(parsed_module)
    with open(output_filename, "wb") as f:
        f.write(obj_code)

    print(f"\n--- Object file '{output_filename}' generated ---")
