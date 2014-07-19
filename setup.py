from distutils.core import setup


setup(
    name="agora",
    version="0.1.dev16",
    author="Eldarion",
    author_email="development@eldarion.com",
    description="an extensible forum app for Django and Pinax",
    long_description=open("README.rst").read(),
    license="BSD",
    url="http://github.com/eldarion/agora",
    packages=[
        "agora",
        "agora.templatetags"
    ],
    install_requires=[
        "django-appconf==0.6"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)
