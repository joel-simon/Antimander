import os
from distutils.core import setup
from Cython.Build import cythonize
import numpy as np

def find_pyx(path='.'):
    pyx_files = []
    for root, dirs, filenames in os.walk(path):
        for fname in filenames:
            if fname.endswith('.pyx'):
                pyx_files.append(os.path.join(root, fname))
    return pyx_files

setup(
    name='Multi Objective District Optimization.',
    author = 'joelsimon.net',
    author_email='joelsimon6@gmail.com',
    install_requires = ['numpy', 'cython'],
    ext_modules=cythonize(find_pyx()),
    include_dirs=[np.get_include()]
)