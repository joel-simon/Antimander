from distutils.core import setup
from Cython.Build import cythonize
import numpy as np
setup(
    name='Multi Objective District Optimization.',
    ext_modules=cythonize("utils/articulation_points.pyx"),
    include_dirs=[np.get_include()]
)