import time

# a command is a dictionary of:
# - value: function/value
# - comment: description of the stat
# - add_percent_sign: True/False, defaults to True for stats that start with a p
# - add_xspace: True/False, defaults to True. Adds an xspace
# - add_commas: True/False, defaults to True. Adds commas to numbers

# a command collection is a dictionary of commands:
# - keys are the command string (alphabetical only)
# - values are commands

def evaluate_collections(collections):
    print('evaluating command collections')

    results = {}
    n_commands = 0
    for name, collection in collections.items():
        start = time.time()
        results[name] = collection()
        end = time.time()

        n_collection_commands = len(results[name])
        n_commands += n_collection_commands
        
        print(f'\t{name}: {n_collection_commands} commands ({round(end - start)}s)')

    print(f"{n_commands} stats. yay!")

    return results


def get_header(string):
    lines = [
        80 * '%',
        f'% {string}',
        80 * '%',
    ]

    return "\n".join(lines)


def format_command(name, content):
    value = content['value']

    if content.get('add_commas', True):
        try:
            value = "{:,}".format(value)
        except:
            pass

    value = str(value)

    if content.get('add_percent_sign') != False and name.startswith('p'):
        value += '\\%'

    if content.get('add_xspace', True):
        value += '\\xspace'

    command = "\\newcommand{\\" + name + "}{" + value + "}"
    command = command.replace('&', '\&')

    return [
        f"% {content['comment']}",
        command,
        "",
    ]
    

def generate(collections):
    lines = []
    for collection_name, commands in evaluate_collections(collections).items():
        lines.append(get_header(collection_name))

        for name, content in commands.items():
            lines += format_command(name, content)

    return "\n".join(lines)


# what I want to do:
# 1. namespace all commands (probably with a suffix)
# 2. modify instances of the command in text
#
# how:
# 1. deal with the commands file
#   - read the commands
#   - make dict of {old_key: new_key}
#   - modify the commands
#   - save the file
# 2. update references
#   - for each file in the list of files to examine:
#       - change the old command to the new command
def add_namespace(
    namespace,
    command_paths=[],
    text_paths=[],
    write=False,
):
    command_to_namespaced_command = get_namespaced_commands(namespace, command_paths)

    for path in command_paths + text_paths:
        namespace_commands(path, command_to_namespaced_command, write=write)

def get_namespaced_commands(namespace, paths):
    command_to_namespaced_command = {}
    for path in paths:

        lines = []
        for line in path.read_text().split('\n'):
            if line.startswith('\\newcommand{\\'):
                prefix, _line = line.split("{", 1)
                command, suffix = _line.split("}", 1)
                namespaced_command = command + namespace

                command_to_namespaced_command[command] = namespaced_command

                line = prefix + "{" + namespaced_command + "}" + suffix

            lines.append(line)

    return command_to_namespaced_command

def namespace_commands(path, command_to_namespaced_command, write=False):
    text = path.read_text()

    for command in sorted(command_to_namespaced_command.keys(), key=lambda c: len(c), reverse=True):
        text = text.replace(command, str(hash(command)))

    for command, namespaced_command in command_to_namespaced_command.items():
        text = text.replace(str(hash(command)), namespaced_command)

    if write:
        path.write_text(text)
