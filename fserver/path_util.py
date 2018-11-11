import os
import posixpath
import re

try:
    from urllib.parse import unquote
except:
    from urllib import unquote


def translate_path(path):
    """Translate a /-separated PATH to the local filename syntax.

    Components that mean special things to the local file system
    (e.g. drive or directory names) are ignored.  (XXX They should
    probably be diagnosed.)

    """
    # abandon query parameters
    path = path.split('?', 1)[0]
    path = path.split('#', 1)[0]
    # Don't forget explicit trailing slash when normalizing. Issue17324
    trailing_slash = path.rstrip().endswith('/')
    try:
        path = unquote(path, errors='surrogatepass')
    except Exception as e:
        path = unquote(path)
    path = posixpath.normpath(path)
    words = path.split('/')
    words = filter(None, words)
    path = os.getcwd()
    for word in words:
        if os.path.dirname(word) or word in (os.curdir, os.pardir):
            # Ignore components that are not a simple file/directory name
            continue
        path = os.path.join(path, word)
    if trailing_slash:
        path += '/'
    return path


def to_local_path(path):
    path = to_local_abspath(path)
    here = to_local_abspath('')

    min_len = len(path) if len(path) < len(here) else len(here)
    sep = os.path.sep

    if os.name == 'nt' and path[0] != here[0]:
        return path
    else:
        sep_ind = 0
        same_ind = 0
        for i in range(min_len):
            if here[i] != path[i]:
                break
            same_ind = i
            if here[i] == sep:
                sep_ind = i
        if same_ind == min_len - 1:
            if len(path) == len(here):
                res = ''
            elif len(path) > len(here):
                res = path[same_ind + 2:]
            else:
                here = here[same_ind:]
                res = '../' * count(here, sep)
        else:
            res = '../' * (count(here[sep_ind:], sep)) + path[sep_ind + 1:]
    res = normalize_path(res)
    res = res + '/' if res.endswith('..') else res
    res = './' if res == '' else res
    return res


def count(string, pattern):
    res = 0
    while True:
        if pattern in string:
            string = string[string.index(pattern) + len(pattern):]
            res += 1
        else:
            break
    return res


def to_local_abspath(path):
    path = normalize_path(path)
    return os.path.abspath(path)


def normalize_path(path):
    p = path.replace('\\', '/').replace('/./', '/')
    p = p[:len(p) - 1] if p.endswith('/') else p
    p = p[2:] if p.startswith('./') else p
    p = re.compile('/+').sub('/', p)
    p = re.compile('/[^./]*?/\.\.').sub('', p)
    return p


def parents_path(path):
    """
    :param path:
    :return: return parents_path which does not contain the end '/', that is remove the end '/'
    """
    res = set()
    path = normalize_path(path)
    while '/' in path:
        sep_ind = path.rindex('/')
        res.add(path[:sep_ind])
        path = path[:sep_ind]
    if path.startswith('./') or not path.startswith('.'):
        res.add('.')
    return res


def parent_path(path):
    """
    :param path:
    :return: return path which does not contain the end '/'
    """
    np = normalize_path(path)
    if '/' not in np:
        return '.'
    else:
        sep_ind = np.rindex('/')
        return np[:sep_ind]


def is_dir(local_path):
    return os.path.isdir(local_path)


def is_file(local_path):
    return os.path.isfile(local_path)


def get_filename(path):
    if os.path.sep in path:
        sep_ind = path.rindex(os.path.sep)
        return path[sep_ind + 1:]
    else:
        return path


def get_suffix(path):
    if '.' in path:
        return path[path.rindex('.') + 1:]
    else:
        return ''


def is_child(child_path, parent_path):
    nc = normalize_path(child_path)
    np = normalize_path(parent_path)
    if len(nc) >= len(np):
        if nc == np:
            return True
        if nc.startswith(np) and nc[len(np)] == os.sep:
            return True
    return False


def path_exists(path):
    res = set()
    np = normalize_path(path)
    if os.path.exists(np):
        res.add(np)
        return res

    start_ind = -1 if '*' not in np else np.index('*')
    start_rind = -1 if '*' not in np else np.rindex('*')
    sep_rind = -1 if '/' not in np else np.rindex('/')

    if start_ind != -1 and start_ind == start_rind:
        if start_ind == 0:
            filename_prefix = ''
            filename_suffix = np[1:] if len(np) > 1 else ''
        else:
            filename_prefix = np[sep_rind + 1:start_ind]
            filename_suffix = np[start_ind + 1:]
        npp = parent_path(np)
        for li in os.listdir(npp):
            if li.startswith(filename_prefix) and li.endswith(filename_suffix):
                res.add(npp + '/' + li)
    return res


if __name__ == '__main__':
    # print(to_local_path('test1/test2/test3/test4'))
    print(normalize_path('test1////ds*/test2///test3/../test4'))
    print(parents_path('test1////dsdas/test2///test3/../test4'))
    print(to_local_path('t'))
    print(parents_path('./t'))
    print(parents_path('../t'))
    print(path_exists('p1/p*'))
    print(path_exists('util*'))
    print(path_exists('*'))
    print(path_exists('*.pyc'))
