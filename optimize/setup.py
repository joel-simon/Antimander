import os
from distutils.core import setup
from setuptools import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy as np

def find_pyx(path='.'):
    pyx_files = []
    for root, dirs, filenames in os.walk(path):
        for fname in filenames:
            if fname.endswith('.pyx'):
                pyx_files.append(
                    Extension(
                        root[2:].replace('/', '.') + '.' + fname.split('.')[0],
                        [ os.path.join(root, fname) ]
                    )
                )
    return pyx_files

setup(
    name='Multi Objective District Optimization.',
    author = 'joelsimon.net',
    author_email='joelsimon6@gmail.com',
    ext_modules=cythonize(
        find_pyx(),
        compiler_directives={ 'language_level' : '3' }
    ),
    cmdclass = {'build_ext': build_ext},
    include_dirs=[ np.get_include() ]
)