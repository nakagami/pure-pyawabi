from setuptools import setup

setup(
    name="pure-pyawabi",
    version="0.2.0",
    description='A morphological analyzer awabi clone',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/nakagami/pure-pyawabi/',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Operating System :: POSIX",
    ],
    keywords=['MeCab'],
    license="MIT",
    author='Hajime Nakagami',
    author_email='nakagami@gmail.com',
    test_suite="tests",
    packages=['pyawabi'],
    scripts=['bin/pyawabi'],
)
