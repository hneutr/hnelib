def empty_directory(directory, recursive=True, delete=True):
    for f in directory.glob('*'):
        if f.is_file():
            f.unlink()
        elif recursive:
            empty_directory(f)
            f.rmdir()

    if delete and not len(list(directory.glob('*'))):
        directory.rmdir()

def fraction_to_percent(fraction, round_to=0):
    percent = 100 * fraction
    if round_to != None:
        percent = round(percent, round_to)

        if round_to == 0:
            percent = int(percent)

    return percent
