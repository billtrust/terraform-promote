# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import argparse
from . import promote_tool


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from', dest='from_path', required=True)
    parser.add_argument('--to', dest='to_path', required=True)
    parser.add_argument('--auto-approve', action='store_true', default=False)
    parser.add_argument('--ignore-missing', action='store_true', default=False)

    mutually_exclusive_group = parser.add_mutually_exclusive_group(required=False)
    mutually_exclusive_group.add_argument('--difftool', required=False)
    mutually_exclusive_group.add_argument('--printdiff', action='store_true')

    args = parser.parse_args()
    return args


def main():
    here = os.path.abspath(os.path.dirname(__file__))
    about = {}
    with open(os.path.join(here, 'version.py'), 'r') as f:
        exec(f.read(), about)

    print('TFPromote version {}'.format(about['__version__']))

    args = parse_args()

    if args.difftool:
        difftool = args.difftool
    else:
        difftool = os.environ.get('TFPROMOTE_DIFFTOOL', None)

    from_path = os.path.abspath(args.from_path)
    to_path   = os.path.abspath(args.to_path)

    # assumes the last folder in the directory structure is the name of the environment
    from_env = os.path.basename(os.path.normpath(from_path))
    to_env   = os.path.basename(os.path.normpath(to_path))

    if difftool:
        if not promote_tool.find_executable(difftool):
            print("Could not find an executable for {}".format(difftool))
            sys.exit(1)

    from_filenames = \
        promote_tool.get_nonenv_tf_files_in_directory(from_path)
    to_filenames = \
        promote_tool.get_nonenv_tf_files_in_directory(to_path)

    from_env_filenames = \
        promote_tool.get_env_tf_files_in_directory(from_path)
    to_env_filenames = \
        promote_tool.get_env_tf_files_in_directory(to_path)

    from_has_to_doesnt, to_has_from_doesnt = \
        promote_tool.validate_filenames(from_filenames, to_filenames)
    from_env_has_to_env_doesnt, to_env_has_from_env_doesnt = \
        promote_tool.validate_filenames(from_env_filenames, to_env_filenames)
    # add environment prefixes to the lists
    from_env_has_to_env_doesnt = \
        ["{}-{}".format(from_env, filename) for filename in from_env_has_to_env_doesnt]
    to_env_has_from_env_doesnt = \
        ["{}-{}".format(to_env, filename) for filename in to_env_has_from_env_doesnt]

    if to_has_from_doesnt:
        print("Files present in {} not found in {}: {}".format(
            to_env, from_env, to_has_from_doesnt))
        if args.ignore_missing:
            print('Ignoring missing files...')
        else:
            print('Resolve diffs before tfpromote will proceed.')
            sys.exit(1)

    if to_env_has_from_env_doesnt:
        print("Files present in {} not found in {}: {}".format(
            to_env, from_env, to_env_has_from_env_doesnt))
        if args.ignore_missing:
            print('Ignoring missing files...')
        else:
            print('Resolve diffs before tfpromote will proceed.')
            sys.exit(1)

    if from_has_to_doesnt:
        print("Files present in {} not found in {}: {}".format(
            from_env, to_env, from_has_to_doesnt))
        proceed = False
        if args.auto_approve:
            proceed = True
        else:
            print("Promote new files (N/y)?")
            response = sys.stdin.readline()
            if response[0] == 'y':
                proceed = True
        if proceed:
            promote_tool.promote_files(from_has_to_doesnt, from_path, to_path)
        else:
            sys.exit(1)

    if from_env_has_to_env_doesnt:
        print("Files present in {} not found in {}: {}".format(
            from_env, to_env, from_env_has_to_env_doesnt))
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
        from_path,
        to_path,
        use_env_prefix=True,
        ignore_missing=args.ignore_missing)

    for filename, difflines in env_diffs:
        from_filename = os.path.join(
            from_path, promote_tool.envprefix_from_directory(from_path) + filename)
        to_filename = os.path.join(
            to_path, promote_tool.envprefix_from_directory(to_path) + filename)
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
        from_path,
        to_path,
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
                    cmd = "{} {} {}".format(
                        difftool,
                        os.path.join(from_path, filename),
                        os.path.join(to_path, filename))
                    os.system(cmd)
                else:
                    print('WARNING: No difftool specified for {}. Provide --difftool or --printdiff.'.format(filename))


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
            promote_tool.promote_files([filename], from_path, to_path)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
