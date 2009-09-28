from . import parser, library

def get_options():
    import optparse
    op = optparse.OptionParser()
    op.add_option('-l', '--library', "SWFFILE"
        help="Use SWFFILE as library of external classes (repeatable).",
        dest="libraries", default=[], action="append", type="string")
    return op

def main():
    global options
    op = get_options()
    options, args = op.parse_args()
    if len(args) != 1:
        op.error("Exacly one argument expected")
    from . import parser, library
    ast = parser.parse_file(args[0])
    lib = library.Library()
    for i in options.libraries:
        lib.add_file(i)
    # TODO: do actual compilation

if __name__ == '__main__':
    from . import compile
    compile.main()
