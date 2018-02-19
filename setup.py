from setuptools import setup, find_packages

setup(
    name='simple-proxy',
    version='0.1.0',
    description='Simple URL-Rewriting Reverse Proxy',
    url='https://github.com/terminal-labs/simple-proxy',
    author='Terminal Labs, Joseph Nix',
    author_email='solutions@terminallabs.com',
    license=license,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'beautifulsoup4',
        'click',
        'cssutils',
        'lxml',
        'requests',
        'tornado',
        'uritools',
    ],
    classifiers = [
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    entry_points='''
    [console_scripts]
    simple-proxy=simple_proxy.cli:main
    '''

)
