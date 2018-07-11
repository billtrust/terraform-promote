import os
import sys
import logging
import difflib
import shutil

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
logger = logging.getLogger(__name__)


def get_nonenv_tf_files_in_directory(directory):
    env_name = os.path.basename(os.path.normpath(directory))
    filenames = []
    for file in os.listdir(directory):
        if file.endswith(".tf"):
            envprefix = "{}-".format(env_name)
            if not file.startswith(envprefix):
                filenames.append(file)
    logger.info("Found {} non-env .tf files in {}".format(len(filenames), directory))
    return filenames


def get_env_tf_files_in_directory(directory):
    '''Finds all .tf files named in format env-whatever.tf and returns the list of files
    with the env- part removed.  Key assumption - that the last folder in the directory
    structure is also the name of the environment.'''
    env_name = os.path.basename(os.path.normpath(directory))
    filenames = []
    for file in os.listdir(directory):
        if file.endswith(".tf"):
            envprefix = "{}-".format(env_name)
            if file.startswith(envprefix):
                filenames.append(file.replace(envprefix, ''))
    logger.info("Found {} non-env .tf files in {}".format(len(filenames), directory))
    return filenames
    


def validate_filenames(from_files, to_files):
    from_has_to_doesnt = [ f for f in from_files if f not in to_files ]
    to_has_from_doesnt = [ f for f in to_files if f not in from_files ]

    return from_has_to_doesnt, to_has_from_doesnt


def diff_files(file1_path, file2_path):
    with open(file1_path, 'r', encoding='utf-8') as file1:
        file1_lines = file1.readlines()
    with open(file2_path, 'r', encoding='utf-8') as file2:
        file2_lines = file2.readlines()

    difflines = difflib.unified_diff(
        file1_lines, file2_lines,
        fromfile=file1_path, tofile=file2_path, lineterm='')
    return difflines


def envprefix_from_directory(directory):
    envname = os.path.basename(os.path.normpath(directory))
    prefix = "{}-".format(envname)
    return prefix
    

def compare_filecontents(filenames, from_directory, to_directory, use_env_prefix, ignore_missing):
    if use_env_prefix:
        from_prefix = envprefix_from_directory(from_directory)
        to_prefix = envprefix_from_directory(to_directory)
    else:
        from_prefix = ''
        to_prefix = ''

    diffs = []
    for filename in filenames:
        from_filename = os.path.join(from_directory, from_prefix + filename)
        to_filename = os.path.join(to_directory, to_prefix + filename)
        logger.debug("Diff on FROM filename: {}".format(from_filename))
        logger.debug("Diff on TO filename: {}".format(to_filename))
        if not os.path.exists(from_filename) and ignore_missing:
            print('Ignoring missing file: {}'.format(from_filename))
            continue
        if not os.path.exists(to_filename) and ignore_missing:
            print('Ignoring missing file: {}'.format(to_filename))
            continue

        difflines = diff_files(from_filename, to_filename)
        # difflines is a generator
        difflines_list = list(filter(lambda a: a.strip() != '', difflines))
        logger.debug("{} lines different in {}".format(
            len(difflines_list), filename))
        if len(difflines_list) > 0:
            diffs.append( (filename, difflines_list) )
    
    return diffs  


def promote_files(filenames, from_path, to_path, continue_on_error = False):
    for filename in filenames:
        try:
            print("Promoting {}".format(filename))
            shutil.copyfile(
                os.path.join(from_path, filename),
                os.path.join(to_path, filename)
            )
        except Exception as e:
            print("Error promoting {}: {}".format(filename, e))
            if not continue_on_error:
                raise

def find_executable(executable):
    '''Similar to bash "which". Returns full path or None if no
    command is found.'''
    paths = os.environ['PATH'].split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        _, ext = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        _, ext = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None

