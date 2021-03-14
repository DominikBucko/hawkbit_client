from setuptools import setup, find_packages

setup(
  name='hawkbit-client',
  author='Dominik Bucko',
  version='0.1.0',
  description='Update client working with Hawkbit DDI API.',
  packages=find_packages(),
  entry_points={
    'console_scripts': [
      'hawkbit-client = hawkbit.main:main'
    ]
  },
)
