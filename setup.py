from setuptools import setup

setup(
    name='blotre',
    version='0.0.2',
    author="Matt Bierner",
    author_email="mattbierner@users.noreply.github.com",
    license="MIT",
    description="Thin Python Blot're client.",
    url="https://github.com/mattbierner/blotre-py",
    py_modules=['blotre'],
    install_requires=[
        'requests'],
    keywords = ['blotre', "blot're", 'REST', 'oauth2']
)
