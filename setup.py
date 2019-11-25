from setuptools import setup
try: # pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # pip <= 9.0.3
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
requirements = [str(requirement.req) for requirement in install_reqs]

setup(
    name='emis-lunch-expenses-scanner',
    version='0.0.1',
    author='Sandervm',
    website='https://github.com/sandervm',
    packages=['src'],
    include_package_data=False,
    description='Simple CLI command to scan expenses images for the price and date and submit them to EMIS',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=requirements,
    python_requires='>=3, <4',
    entry_points={
        'console_scripts': [
            'emis-expenses=src.main:main',
            'eles=src.main:main'
        ]
    }
)
