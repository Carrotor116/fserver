from fserver import conf
from fserver.path_util import is_child
from fserver.path_util import normalize_path
from fserver.path_util import url_path_to_local_abspath


def path_permission_deny(path):
    """
    note that prior of black list is high than one of white list,
    that is, even path is sub of white list, path will be denied if path is in black or black' sub path
    :param path:
    :return:
    """
    DENY = True
    ALLOW = not DENY
    if path == '' or path == '/' or path == 'favicon.ico':
        return ALLOW

    local_abspath = url_path_to_local_abspath(path)
    if not is_child(local_abspath, conf.ROOT) and local_abspath != conf.ROOT:
        return DENY

    if len(conf.BLACK_LIST) == 0 and len(conf.WHITE_LIST) == 0:  # disable white or black list function
        return ALLOW

    np = normalize_path(path)
    if len(conf.WHITE_LIST) > 0:  # white mode
        if np in conf.WHITE_LIST_PARENTS or np in conf.WHITE_LIST:  # path is white or parent of white
            return ALLOW

        for w in conf.WHITE_LIST:
            if is_child(np, w):
                for b in conf.BLACK_LIST:
                    if is_child(np, b) or np == b:
                        return DENY
                return ALLOW  # path is child of white and not child of black
        return DENY  # define white_list while path not satisfy white_list

    if len(conf.BLACK_LIST) > 0:  # black mode
        for b in conf.BLACK_LIST:
            if is_child(np, b) or np == b:
                return DENY  # path is in black list.
        return ALLOW
    return DENY
