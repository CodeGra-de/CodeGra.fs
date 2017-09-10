import os
import shutil

join = os.path.join


def rm(*args):
    return os.unlink(join(*args))


def rmdir(*args):
    return os.rmdir(join(*args))


def rm_rf(*args):
    return shutil.rmtree(join(*args))


def isfile(*args):
    is_file = os.path.isfile(join(*args))
    is_dir = os.path.isdir(join(*args))
    if is_file and is_dir:
        print(join(*args), 'is both a file and a dir')
    return is_file and not is_dir


def isdir(*args):
    return os.path.isdir(join(*args))


def mkdir(*args):
    return os.mkdir(join(*args))


def ls(*args):
    return os.listdir(join(*args))


def symlink(src, dst):
    return os.symlink(join(*src), join(*dst))


def rename(src, dst):
    return os.rename(join(*src), join(*dst))


def chown(path, uid, gid):
    return os.chown(join(*path), uid, gid)


def chmod(path, mode):
    return os.chmod(join(*path), mode)
