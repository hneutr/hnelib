import hnelib.tex.command
import hnelib.tex.table

def bold(string):
    return f"\\bf{{{string}}}"

def italic(string):
    return f"\\it{{{string}}}"

def indent(string):
    return f"\\quad {string}"
