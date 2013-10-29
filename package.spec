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
          console=False,
          icon='images/windows_icon.ico'	
	 )


# Include the directories in the final build
dict_tree1 = Tree('training_protocols', prefix = 'training_protocols')
dict_tree2 = Tree('images', prefix = 'images')
dict_tree3 = Tree('targets', prefix = 'targets')


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               dict_tree1,
               dict_tree2,
               dict_tree3,
               strip=None,
               upx=True,
               name='shootoff')
