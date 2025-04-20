import os.path
import shutil


def call(command):
    print(f'Calling `{command}`')
    os.system(command)


HEADER_BEFORE = '# -*- mode: python ; coding: utf-8 -*-'
HEADER_WITH_IMPORTS = '''\
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
COLLECT = lambda *args, **kwargs: None
'''


def main():
    if os.path.isdir('dist'):
        shutil.rmtree('dist')
    for exe in ['run_app.py', 'run_server.py']:
        command = " ".join(["pyi-makespec",
                            exe,
                            '--exclude-module', 'numpy',
                            '--exclude-module', 'tensorflow',
                            '--exclude-module', 'matplotlib',
                            '--exclude-module', 'zmq',
                            '--exclude-module', 'IPython',
                            '--exclude-module', 'babel',
                            '--exclude-module', 'pandas',
                            '--exclude-module', 'sqlalchemy',
                            '--exclude-module', 'sqlite3',
                            '--exclude-module', 'scipy',
                            '--hidden-import', 'bottle_websocket',
                            ])
        call(command)
        if os.path.isfile(exe.replace('.py', '_spec') + '.py'):
            os.remove(exe.replace('.py', '_spec') + '.py')
        os.rename(exe.replace('.py', '.spec'), exe.replace('.py', '_spec') + '.py')
        with open(exe.replace('.py', '_spec') + '.py') as py_file:
            contents = py_file.read()
        assert HEADER_BEFORE in contents
        contents_with_imports = contents.replace(HEADER_BEFORE, HEADER_WITH_IMPORTS)
        assert contents_with_imports.startswith(HEADER_WITH_IMPORTS)
        with open(exe.replace('.py', '_spec') + '.py', 'w') as py_file:
            py_file.write(contents_with_imports)

    command = " ".join(["pyinstaller",
                        'compile_both.spec', ])
    call(command)
    if os.path.isfile('dist/time_zone.zip'):
        os.remove('dist/time_zone.zip')
    shutil.make_archive(base_name='dist/time_zone', format='zip', root_dir='dist/time_zone',)


if __name__ == '__main__':
    main()
