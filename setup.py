from setuptools import setup

setup(
    name='blotre',
    version='0.0.0',
    author="Matt Bierner",
    license="MIT",
    description="Thin Python Blot're client.",
    url="https://github.com/mattbierner/blotre-py",
    py_modules=['blotre'],
    install_requires=[
        'requests']
)
