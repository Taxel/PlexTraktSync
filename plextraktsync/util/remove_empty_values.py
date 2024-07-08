from __future__ import annotations


def remove_empty_values(result):
    """
    Update result to remove empty changes.
    This makes diagnostic printing cleaner if we don't print "changed: 0"
    """
    for change_type in ["added", "existing", "updated"]:
        if change_type not in result:
            continue
        for media_type, value in result[change_type].copy().items():
            if value == 0:
                del result[change_type][media_type]
        if len(result[change_type]) == 0:
            del result[change_type]

    for media_type, items in result["not_found"].copy().items():
        if len(items) == 0:
            del result["not_found"][media_type]

    if len(result["not_found"]) == 0:
        del result["not_found"]

    if len(result) == 0:
        return None

    return result
