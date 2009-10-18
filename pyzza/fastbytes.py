from . import bytecode

def optimize(tag):
    for meth in tag.real_body.method_body_info:
        optimize_method(meth)

def optimize_method(meth):
    meth.bytecode = list(clean_nops(meth.bytecode))

def clean_nops(bytecodes):
    cleanbc = (
        bytecode.debug,
        bytecode.debugline,
        bytecode.debugfile,
        bytecode.nop,
        )
    for code in bytecodes:
        if not isinstance(code, cleanbc):
            yield code
