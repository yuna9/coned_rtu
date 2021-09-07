from setuptools import setup

setup(
    name="coned_rtu",
    version="0.1",
    description="Getting real-time usage reports from Con Edison",
    packages=["coned_rtu"],
    zip_safe=False,
    install_requires=[
        "configobj==5.0.6",
        "pre-commit==2.14.1",
        "pyotp==2.3.0",
        "python-dateutil==2.8.1",
        "python-dotenv==0.11.0",
        "selenium==3.141.0",
    ],
)
