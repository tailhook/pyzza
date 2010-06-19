with open('colorshemes.py', 'wt', encoding='utf-8') as output:
    output.write('@package("graph")\n')
    output.write('class Colors:\n')
    output.write('    def __init__(self):\n')
    output.write('        pass\n')
    output.write('    x11 = {\n')
    with open('/usr/share/X11/rgb.txt') as input:
        for line in input:
            r, g, b, name = line.split(None,3)
            output.write('        "{name}": 0x{:06x},\n'.format(
                (int(r) << 16) + (int(g) << 8) + int(b),
                name=name.strip().lower()))
    output.write('    }\n')
