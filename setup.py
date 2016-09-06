"""Setup for fun_videofront_xblock XBlock."""

import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='fun-videofront-xblock',
    version='0.1',
    description='XBlock for interaction with Videofront from FUN',
    packages=[
        'fun_videofront_xblock',
    ],
    install_requires=[
        'XBlock', 'xblock-utils',
    ],
    entry_points={
        'xblock.v1': [
            'fun_videofront_xblock = fun_videofront_xblock:FunVideofrontXBlock',
        ]
    },
    package_data=package_data("fun_videofront_xblock", ["static", "public"]),
)
