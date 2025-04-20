# -*- mode: python ; coding: utf-8 -*-

import run_app_spec
import run_server_spec

block_cipher = None
coll = COLLECT(run_app_spec.exe,
               run_server_spec.exe,
               run_app_spec.a.binaries,
               run_app_spec.a.zipfiles,
               run_app_spec.a.datas,
               run_server_spec.a.binaries,
               run_server_spec.a.zipfiles,
               run_server_spec.a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='time_zone')
