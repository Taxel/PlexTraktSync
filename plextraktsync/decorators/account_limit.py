from __future__ import annotations

from decorator import decorator
from trakt.errors import AccountLimitExceeded

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)

bypassed_lists = set()


# https://forums.trakt.tv/t/freemium-experience-more-features-for-all-with-usage-limits/41641
@decorator
def account_limit(fn, *args, **kwargs):
    list_name = fn.__name__.replace("add_to_", "")
    if list_name in bypassed_lists:
        return None

    try:
        return fn(*args, **kwargs)
    except AccountLimitExceeded as e:
        logger.error(f"Trakt Error: {e}")
        logger.warning(
            f"Account Limit Exceeded for Trakt {list_name}: {e.account_limit} items. "
            f"Consider disabling {list_name} sync or upgrading your Trakt account."
        )
        logger.debug(e.details)

        if list_name:
            bypassed_lists.add(list_name)
        return None
