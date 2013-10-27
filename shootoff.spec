# -*- mode: python -*-
a = Analysis(['shootoff.py'],
             pathex=[''],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='shootoff.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )


# Include the training_protocols directory in the final build
dict_tree = Tree('training_protocols', prefix = 'training_protocols')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               dict_tree,
               strip=None,
               upx=True,
               name='shootoff')
