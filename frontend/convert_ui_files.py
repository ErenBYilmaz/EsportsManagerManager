import os

from lib.util import call_tool


base_dir = os.path.dirname(__file__)
for filename in os.listdir(f'{base_dir}/resources'):
    assert filename.endswith('.ui')
    in_path = os.path.abspath(os.path.join(f'{base_dir}/resources', filename))
    out_path = os.path.abspath(os.path.join(f'{base_dir}/generated', filename[:-len('.ui')] + '.py'))
    call_tool(['pyuic5', '-x', in_path, '-o', out_path])
