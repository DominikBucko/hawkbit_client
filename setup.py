from setuptools import setup, find_packages


required = [
  "setuptools~=53.0.0",
  "PyYAML~=5.4.1",
  "requests~=2.25.1",
  "sh~=1.14.1",
]

setup(
  name='hawkbit-client',
  author='Dominik Bucko',
  version='0.1.0',
  description='Update client working with Hawkbit DDI API.',
  install_requires=required,
  packages=find_packages(),
  entry_points={
    'console_scripts': [
      'hawkbit-client = hawkbit.main:main'
    ]
  },
)
