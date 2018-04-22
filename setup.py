from setuptools import setup
# Rende la nostra app un package python, installabile tramite pip
setup(
    name='demo_completa',
    packages=['demo_completa'],
    include_package_data=True,
    install_requires=[  # Indica i moduli richiesti dall'app
        'flask',
    ],
)

