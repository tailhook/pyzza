
To disassemble swf call ``swf`` module::

    python3 -m pyzza.swf file.swf

It will print module disassembly and also write more compact ``file.swf.swf``,
without metadata.

To compile python-like language (pyzza) file::

    python3 -m pyzza.compile -l library.swf file.py

This produces ``file.swf``. ``library.swf`` is usually file from flex SDK,
it's contained in ``playerglobal.swc`` which you use to compile actionscript
when using ``mxmlc``. You can also add your own library.

For description of pyzza language see ``pyzza.txt``.
