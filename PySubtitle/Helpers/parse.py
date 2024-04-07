import regex

def ParseNames(name_list):
    if isinstance(name_list, str):
        name_list = regex.split("[\n,]", name_list)

    if isinstance(name_list, list):
        return [ name.strip() for name in name_list ]

    return []