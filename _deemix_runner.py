"""
Thin entry point for PyInstaller to bundle deemix as a second executable.
When called, this behaves exactly like running `deemix` from the command line.
"""
import runpy
import sys

runpy.run_module("deemix", run_name="__main__", alter_sys=True)
