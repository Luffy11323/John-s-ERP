from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="kodessy_app",
    version="0.0.1",
    description="Kodessy Custom ERPNext Extensions and Business Workflows",
    author="Kodessy",
    author_email="info@kodessy.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
