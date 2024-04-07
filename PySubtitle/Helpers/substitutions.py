import logging
import regex

def ParseSubstitutions(sub_list, separator="::"):
    """
    :param sub_list: is assumed to be a list of (before,after) pairs
    separated by the separator ("::" by default).

    :return: a dictionary of (before,after) pairs
    :rtype dict:
    """
    if not sub_list:
        return {}

    if isinstance(sub_list, dict):
        return sub_list

    if isinstance(sub_list, str):
        sub_list = regex.split("[\n,]", sub_list)

    if isinstance(sub_list, list):
        substitutions = {}
        for sub in sub_list:
            if "::" in sub:
                before, after = sub.split(separator)
                substitutions[before] = after
            elif sub.strip():
                try:
                    with open(sub, "r", encoding="utf-8", newline='') as f:
                        for line in [line.strip() for line in f if line.strip()]:
                            if "::" in line:
                                before, after = line.split("::")
                                substitutions[before] = after
                            else:
                                raise ValueError(f"Invalid substitution format in {sub}: {line}")

                except FileNotFoundError:
                    logging.warning(f"Substitution file not found: {sub}")
                except ValueError:
                    raise

        return substitutions

    return {}

def PerformSubstitutions(substitutions : dict, input, match_partial_words : bool = False):
    """
    :param input: If input is string-like, attempt to substitute all (before,after) pairs
    in substitutions. If input is a list, iterate over all elements performing substitutions.

    :return: If input is string-like, return a string with the substitutions.
    If input is a list, return a list of strings along with a dictionary of (before,after) pairs
    for each elements that had one or more substitutions.
    """
    substitutions = substitutions if substitutions else {}

    if isinstance(input, list):
        new_list = [ PerformSubstitutions(substitutions, line, match_partial_words) for line in input ]
        replacements = { line: new_line for line, new_line in zip(input, new_list) if new_line != str(line) }
        return new_list, replacements

    result = str(input)
    for before, after in substitutions.items():
        pattern = fr"\b{regex.escape(before)}\b" if not match_partial_words else regex.escape(before)
        result = regex.sub(pattern, after, result, flags=regex.UNICODE)

    return result