# -*- mode: python -*-

def Datafiles(*filenames, **kw):
    import os
    
    def datafile(path, strip_path=True):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'

    strip_path = kw.get('strip_path', True)
    return TOC(
        datafile(filename, strip_path=strip_path)
        for filename in filenames
        if os.path.isfile(filename))


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
dict_tree4 = Tree('sounds', prefix = 'sounds')
license = Datafiles('LICENSE')


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               dict_tree1,
               dict_tree2,
               dict_tree3,
               dict_tree4,
               license,
               strip=None,
               upx=True,
               name='shootoff')

