"""Subscription class for TeamTalk."""

from .implementation.TeamTalkPy import TeamTalk5 as sdk


class _SubscriptionMeta(type):
    def __getattr__(cls, name: str) -> sdk.UserRight:
        name = f"SUBSCRIBE_{name}"
        return getattr(sdk.Subscription, name, None)


class Subscription(metaclass=_SubscriptionMeta):
    """A class representing subscriptions in TeamTalk."""
