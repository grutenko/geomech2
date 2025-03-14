import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildExecutable(build_py):
    def run(self):
        """Run PyInstaller to build the executable before the actual build process"""
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--windowed",
                "--noconfirm",
                "--onefile",
                "--clean",
                "--strip",
                "--splash=icons/logo.png",
                "--add-data=icons:icons",
                "--icon=icons/logo.png",
                "--name=geomech",
                "--hidden-import=wx._xml",
                "--hidden-import=pony.orm.dbproviders",
                "--hidden-import=pony.orm.dbproviders.postgres",
                "--hidden-import=psycopg2",
                "--hidden-import=transliterate",
                "--hidden-import=transliterate.contrib.languages",
                "--optimize=2",
                "__main__.py",
            ],  # Create a single executable file  # Name of the output file  # Your main script
            check=True,
        )
        super().run()


setup(name="geomech", cmdclass={"build_py": BuildExecutable})  # Replace with actual package name
