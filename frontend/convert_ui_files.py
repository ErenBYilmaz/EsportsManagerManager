import os

from lib.util import call_tool

for filename in os.listdir('frontend/resources'):
    assert filename.endswith('.ui')
    in_path = os.path.abspath(os.path.join('frontend/resources', filename))
    out_path = os.path.abspath(os.path.join('frontend/generated', filename[:-len('.ui')] + '.py'))
    call_tool(['pyuic5', '-x', in_path, '-o', out_path])
