import os
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildExecutable(build_py):
    def run(self):
        """Run PyInstaller to build the executable before the actual build process"""
        args = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--windowed",
            "--noconfirm",
            "--onedir",
            "--clean",
            "--splash=icons/logo.png",
            "--add-data=icons:icons",
            "--name=geomech",
            "--hidden-import=jedi",
            "--hidden-import=wx._xml",
            "--hidden-import=pony.orm.dbproviders",
            "--hidden-import=pony.orm.dbproviders.postgres",
            "--hidden-import=pony.orm.dbproviders.sqlite",
            "--hidden-import=psycopg2",
            "--hidden-import=transliterate",
            "--collect-all=transliterate",
            "--optimize=2",
        ]
        if sys.platform != "win32":
            args.append("--strip")
            args.append("--icon=icons/logo.png")
        else:
            args.append("--icon=icons/logo.ico")
        args.append("__main__.py")
        os.environ["PYTHONOPTIMIZE"] = "1"
        subprocess.run(
            args, check=True, env=os.environ
        )  # Create a single executable file  # Name of the output file  # Your main script
        super().run()


setup(name="geomech", cmdclass={"build_py": BuildExecutable})  # Replace with actual package name
