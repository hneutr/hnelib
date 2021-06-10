def empty_directory(directory, recursive=True, delete=True):
    for f in directory.glob('*'):
        if f.is_file():
            f.unlink()
        elif recursive:
            empty_directory(f)
            f.rmdir()

    if delete and not len(list(directory.glob('*'))):
        directory.rmdir()
