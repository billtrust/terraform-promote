# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import argparse
from . import promote_tool


def create_parser():
    parser = argparse.ArgumentParser(add_help=False) # since we are specifically handing --help
    parser.add_argument('--help', action='store_true', required=False)
    parser.add_argument('--from', dest='from_path', required=False)
    parser.add_argument('--to', dest='to_path', required=False)
    parser.add_argument('--auto-approve', action='store_true', default=False)
    parser.add_argument('--ignore-missing', action='store_true', default=False)

    mutually_exclusive_group = parser.add_mutually_exclusive_group(required=False)
    mutually_exclusive_group.add_argument('--difftool', required=False)
    mutually_exclusive_group.add_argument('--printdiff', action='store_true')

    return parser


def get_to_from_environments(args):
    if not args.from_path and not args.to_path:
        # full auto, no paths given (figure out both paths automatically)

        # in full auto mode, the current dir needs to be an env dir
        to_path = os.getcwd()
        to_env = os.path.basename(os.path.normpath(to_path))
        if not promote_tool.is_env_path_valid(to_env):
            raise Exception(('In --auto paths mode, current directory must be an ',
                   'environment in TFPROMOTE_ENVS.'))

        # the from dir will be the lower environment
        base_path = os.path.split(os.path.abspath(os.getcwd()))[0]
        from_env = promote_tool.get_lower_environment(to_env)
        from_path = os.path.join(base_path, from_env)
    elif args.from_path and not args.to_path:
        # only from path given (to path is current path)
        from_path = os.path.abspath(args.from_path)
        to_path = os.getcwd()
    elif args.to_path and not args.from_path:
        # only to path given (from path is current path)
        from_path = os.getcwd()
        to_path = os.path.abspath(args.to_path)
    elif args.from_path and args.to_path:
        # both from and to explicitly given
        from_path = os.path.abspath(args.from_path)
        to_path   = os.path.abspath(args.to_path)
    else:
        raise Exception('Unexpected to/from argument situation, should never occur.')

    # assumes the last folder in the directory structure is the name of the environment
    from_env = os.path.basename(os.path.normpath(from_path))
    from_env = from_env.split('-')[0] # '/dev/' or 'dev-us-east-1' -> 'dev'
    to_env   = os.path.basename(os.path.normpath(to_path))
    to_env = to_env.split('-')[0] # '/dev/' or 'dev-us-east-1' -> 'dev'


    # validate env names
    if not promote_tool.is_env_path_valid(from_env):
        raise Exception("From env ({}) is not part of TFPROMOTE_ENVS ({})".format(
            from_env, promote_tool.get_env_names()))
    if not promote_tool.is_env_path_valid(to_env):
        raise Exception("To env ({}) is not part of TFPROMOTE_ENVS ({})".format(
            to_env, promote_tool.get_env_names()))

    # validate to and from paths exist
    if not os.path.exists(from_path):
        raise Exception("From path does not exist: {}".format(
            from_path))
    if not os.path.exists(to_path):
        raise Exception("To path does not exist: {}".format(
            to_path))
    return {
        'from_path': from_path,
        'from_env': from_env,
        'to_path': to_path,
        'to_env': to_env
    }


def main():
    here = os.path.abspath(os.path.dirname(__file__))
    about = {}
    with open(os.path.join(here, 'version.py'), 'r') as f:
        exec(f.read(), about)

    print('TFPromote version {}'.format(about['__version__']))

    parser = create_parser()
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        parser.exit()

    if args.difftool:
        difftool = args.difftool
    else:
        difftool = os.environ.get('TFPROMOTE_DIFFTOOL', None)

    try:
        tf_envs = get_to_from_environments(args)
    except Exception as e:
        print(e)
        sys.exit(1)

    print("From env {:<4}, path: {}".format(tf_envs['from_env'], tf_envs['from_path']))
    print("To   env {:<4}, path: {}".format(tf_envs['to_env'], tf_envs['to_path']))

    # if any portion of the to or from path was unspecified (and left to auto), seek
    # confirmation before proceeding, unless --auto-approve was specified.
    if (not args.to_path or not args.from_path) and not args.auto_approve:
        print("Continue? (CTRL+C to abort)")
        response = sys.stdin.readline()

    if difftool:
        if not promote_tool.find_executable(difftool):
            print("Could not find an executable for {}".format(difftool))
            sys.exit(1)

    from_filenames = \
        promote_tool.get_nonenv_tf_files_in_directory(tf_envs['from_path'])
    to_filenames = \
        promote_tool.get_nonenv_tf_files_in_directory(tf_envs['to_path'])

    from_env_filenames = \
        promote_tool.get_env_tf_files_in_directory(tf_envs['from_path'])
    to_env_filenames = \
        promote_tool.get_env_tf_files_in_directory(tf_envs['to_path'])

    from_has_to_doesnt, to_has_from_doesnt = \
        promote_tool.validate_filenames(from_filenames, to_filenames)
    from_env_has_to_env_doesnt, to_env_has_from_env_doesnt = \
        promote_tool.validate_filenames(from_env_filenames, to_env_filenames)

    # add environment prefixes to the lists
    from_env_has_to_env_doesnt = \
        ["{}-{}".format(tf_envs['from_env'], filename) for filename in from_env_has_to_env_doesnt]
    to_env_has_from_env_doesnt = \
        ["{}-{}".format(tf_envs['to_env'], filename) for filename in to_env_has_from_env_doesnt]

    if to_has_from_doesnt:
        print("Files present in {} not found in {}: {}".format(
            tf_envs['to_env'], tf_envs['from_env'], to_has_from_doesnt))
        if args.ignore_missing:
            print('Ignoring missing files...')
        else:
            print('Resolve diffs before tfpromote will proceed.')
            sys.exit(1)

    if to_env_has_from_env_doesnt:
        print("Files present in {} not found in {}: {}".format(
            tf_envs['to_env'], tf_envs['from_env'], to_env_has_from_env_doesnt))
        if args.ignore_missing:
            print('Ignoring missing files...')
        else:
            print('Resolve diffs before tfpromote will proceed.')
            sys.exit(1)

    if from_has_to_doesnt:
        print("Files present in {} not found in {}: {}".format(
            tf_envs['from_env'], tf_envs['to_env'], from_has_to_doesnt))
        proceed = False
        if args.auto_approve:
            proceed = True
        else:
            print("Promote new files (N/y)?")
            response = sys.stdin.readline()
            if response[0] == 'y':
                proceed = True
        if proceed:
            promote_tool.promote_files(from_has_to_doesnt, tf_envs['from_path'], tf_envs['to_path'])
        else:
            sys.exit(1)

    if from_env_has_to_env_doesnt:
        print("Files present in {} not found in {}: {}".format(
            tf_envs['from_env'], tf_envs['to_env'], from_env_has_to_env_doesnt))
        if args.ignore_missing:
            print('Ignoring missing files...')
        else:
            print('Resolve diffs before tfpromote will proceed.')
            sys.exit(1)

    # for clarity, these should be identical at this point
    filenames = from_filenames
    env_filenames = from_env_filenames

    print('Comparing environment specific files...')

    # just for comparing, these are expected to be different per environment
    env_diffs = promote_tool.compare_filecontents(
        env_filenames,
        tf_envs['from_path'],
        tf_envs['to_path'],
        use_env_prefix=True,
        ignore_missing=args.ignore_missing)

    for filename, difflines in env_diffs:
        from_filename = os.path.join(
            tf_envs['from_path'], promote_tool.envprefix_from_directory(tf_envs['from_path']) + filename)
        to_filename = os.path.join(
            tf_envs['to_path'], promote_tool.envprefix_from_directory(tf_envs['to_path']) + filename)
        print("Diff: \n{}\n{} - {} lines different".format(
            from_filename, to_filename, len(difflines)))
        if args.printdiff:
            for line in difflines:
                print(line)
        elif difftool:
            cmd = "{} {} {}".format(
                difftool,
                from_filename,
                to_filename)
            os.system(cmd)

    print('\nComparing non-environment specific files...')

    diffs = promote_tool.compare_filecontents(
        filenames,
        tf_envs['from_path'],
        tf_envs['to_path'],
        use_env_prefix=False,
        ignore_missing=args.ignore_missing)

    if not diffs:
        print('No non-environment specific differences, nothing to promote!')
        sys.exit(0)
    else:
        for filename, difflines in diffs:
            if args.printdiff:
                for line in difflines:
                    print(line)
            else:
                print("Diff: {} - {} lines different".format(
                    filename, len(difflines)))
                if difftool:
                    full_from_filename = os.path.join(tf_envs['from_path'], filename)
                    full_to_filename = os.path.join(tf_envs['to_path'], filename)
                    if not os.path.isfile(full_from_filename):
                        print("From filename does not exist: " + full_from_filename)
                    if not os.path.isfile(full_to_filename):
                        print("To filename does not exist: " + full_to_filename)
                    cmd = "{} {} {}".format(
                        difftool,
                        full_from_filename,
                        full_to_filename)
                    return_code = os.system(cmd)
                    if return_code != 0:
                        print("Error executing diff command: {}".format(cmd))
                        print("Continue (N/y)?")
                        response = sys.stdin.readline()
                        if response[0] != 'y':
                            sys.exit(1)
                else:
                    print('WARNING: No difftool specified for {}. Provide environment variable TFPROMOTE_DIFFTOOL or argument --difftool or --printdiff.'.format(filename))


    proceed = False
    if args.auto_approve:
        proceed = True
    else:
        print("Promote modified files (N/y)?")
        response = sys.stdin.readline()
        if response[0] == 'y':
            proceed = True
    if proceed:
        for filename, _ in diffs:
            promote_tool.promote_files([filename], tf_envs['from_path'], tf_envs['to_path'])
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
