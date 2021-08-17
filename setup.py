from setuptools import setup, find_packages


setup(
    name='cldfzenodo',
    version='0.1.1.dev0',
    author='Robert Forkel',
    author_email='dlce.rdm@eva.mpg.de',
    description='functionality to retrieve CLDF datasets deposited on Zenodo',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='',
    license='Apache 2.0',
    url='https://github.com/cldf/cldfzenodo',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    python_requires='>=3.6',
    entry_points={
        'cldfbench.commands': [
            'zenodo=cldfzenodo.commands',
        ],
    },
    install_requires=[
        'pycldf>=1.23.0',
        'html5lib',
        'nameparser',
        'attrs',
    ],
    extras_require={
        'cli': ['cldfbench'],
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'cldfbench',
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
