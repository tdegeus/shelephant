import subprocess

def exec_cmd(cmd, verbose=False):
    r'''
Run command, optionally verbose command and its output, and return output.

:type cmd: str
:param cmd: The command to run.

:type verbose: bool
:param verbose: Print command and its output.
    '''

    if verbose:
        print(cmd)

    ret = subprocess.check_output(cmd, shell=True).decode('utf-8')

    if verbose:
        print(ret)

    return ret
