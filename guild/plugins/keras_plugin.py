import ast
import glob
import os

import guild.log

def try_project(args):
    if args.command == "train":
        return _try_project_for_train(args)
    elif args.command == "view":
        return _project_for_view(args)
    else:
        return None

def _try_project_for_train(args):
    script = _find_keras_script(args)
    if script:
        return _project_for_script(script)
    else:
        return None

def _find_keras_script(args):
    scripts = _keras_scripts(args)
    if args.model:
        for script in scripts:
            if _script_name(script) == args.model:
                return script
        _no_such_model_error(args.model, scripts)
    else:
        if len(scripts) == 1:
            return scripts[0]
        else:
            _model_required_error(scripts)

def _keras_scripts(args):
    keras_scripts = []
    for script in _python_scripts(args):
        debug_parts = ["testing script '%s':" % script]
        is_script = _is_keras_script(script, debug_parts)
        guild.log.debug(" ".join(debug_parts), source="keras-plugin")
        if is_script:
            keras_scripts.append(script)
    return keras_scripts

def _python_scripts(args):
    return glob.glob(os.path.join(args.project_dir, "*.py"))

def _is_keras_script(script, debug_parts):
    try:
        parsed = ast.parse(open(script, "r").read())
    except SyntaxError as e:
        debug_parts.append("%s, skipping" % e)
        return False
    else:
        return _is_keras_ast(parsed, debug_parts)

def _is_keras_ast(parsed, debug_parts):
    conditions = [
        (_imports_keras_condition, "imports-keras"),
        (_calls_fit_condition, "calls-fit")
    ]
    return _ast_meets_conditions(parsed, conditions, debug_parts)

def _ast_meets_conditions(parsed, conditions, debug_parts):
    working = list(conditions)
    for node in ast.walk(parsed):
        for condition in working:
            condition_fun, _name = condition
            condition_met = condition_fun(node)
            if condition_met:
                working.remove(condition)
        if len(working) == 0:
            debug_parts.append("appears to be a Keras script")
            return True
    assert len(working) > 0
    debug_parts.append(
        "does not appear to be a Keras script (failed conditions: %s)"
        % ", ".join([name for _, name in working]))
    return False

def _imports_keras_condition(node):
    if (isinstance(node, ast.ImportFrom)
        and _is_keras_module_name(node.module)):
        return True
    elif isinstance(node, ast.Import):
        for name in node.names:
            if (isinstance(name, ast.alias)
                and _is_keras_module_name(name.name)):
                return True
    return False

def _is_keras_module_name(name):
    return name == "keras" or name.startswith("keras.")

def _calls_fit_condition(node):
    if (isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "fit"):
        return True
    return False

def _script_name(script):
    name, _ext = os.path.splitext(os.path.basename(script))
    return name

def _no_such_model_error(model, scripts):
    script_names = [_script_name(script) for script in scripts]
    guild.cli.error(
        "cannot find a script for model '%s'\n"
        "Try 'guild train MODEL' where MODEL is one of: %s"
        % (model, ", ".join(script_names)))

def _model_required_error(scripts):
    script_names = [_script_name(script) for script in scripts]
    guild.cli.error(
        "more than one Keras script found\n"
        "Use 'guild train MODEL' where MODEL is one of: %s"
        % ", ".join(script_names))

def _project_for_script(script):
    script_name = _script_name(script)
    train_spec = _train_spec(script)
    data = {
        "models": {
            script_name: {
                "train": train_spec
            }
        }
    }
    return guild.project.Project(
        data,
        source=None,
        dir=os.path.dirname(script),
        annotation="auto-generated for train by keras plugin")

def _train_spec(script):
    return " ".join([_keras_run_path(), script])

def _keras_run_path():
    this_dir = os.path.dirname(__file__)
    return os.path.join(this_dir, "keras_run.py")

def _project_for_view(args):
    data = {
    }
    return guild.project.Project(
        data,
        source=None,
        dir=args.project_dir,
        annotation="auto-generated for view by keras plugin")
