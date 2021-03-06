import json
import sys

import guild.cmd_support
# Avoid expensive imports here

def add_parser(subparsers):
    p = guild.cmd_support.add_parser(
        subparsers,
        "project", "print project information",
        """With no arguments, prints a project.

        By default, projects are printed in YAML format. You may
        alternatively print them in JSON format by specifying the
        --json option.

        To print a fully resolved project (useful for debugging Guild
        View issues) use the --resolve option.
        """)
    p.add_argument(
        "types",
        nargs="*",
        metavar="TYPE",
        help=("print the specified type (e.g. models, profiles, "
              "resources, etc.)"))
    guild.cmd_support.add_project_arguments(p)
    p.add_argument(
        "--json",
        help="print project in JSON format (default format is YAML)",
        action="store_true")
    p.add_argument(
        "--resolve",
        help="fully resolve extends references and includes",
        action="store_true")
    p.set_defaults(func=main)

def main(args):
    project = guild.cmd_support.project_for_args(args, use_plugins=True)
    if args.resolve:
        _print_resolved_project(project, args)
    else:
        _print_project(project, args)

def _print_resolved_project(project, args):
    import guild.view

    view = guild.view.ProjectView(project, {})
    resolved = view.resolved_project()
    _print_project(resolved, args)

def _print_project(project, args):
    if args.types:
        project = _filter_project_by_types(project, args.types)
    if args.json:
        _print_project_json(project)
    else:
        _print_project_yaml(project)

def _filter_project_by_types(project, types):
    filtered_data = {
        key: val
        for key, val in project.data.items()
        if key in types
    }
    return guild.project.copy_with_new_data(project, filtered_data)

def _print_project_json(project):
    sys.stdout.write(
        json.dumps(
            project.data,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')))

def _print_project_yaml(project):
    import yaml
    sys.stdout.write(
        yaml.dump(
            project.data,
            default_flow_style=False,
            indent=2))
