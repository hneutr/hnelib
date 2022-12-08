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

        n_collection_commands = len(results[key])
        n_commands += n_collection_commands
        
        print(f'\t{key}: {n_collection_commands} commands ({round(end - start)}s)')

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
