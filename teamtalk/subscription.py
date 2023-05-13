"""Subscription class for TeamTalk."""

from .implementation.TeamTalkPy import TeamTalk5 as sdk


class _SubscriptionMeta(type):
    def __getattr__(cls, name: str) -> sdk.UserRight:
        name = f"SUBSCRIBE_{name}"
        return getattr(sdk.Subscription, name, None)

    def __dir__(cls) -> list[str]:
        return [name[10:] for name in dir(sdk.Subscription) if name.startswith("SUBSCRIBE_")]


class Subscription(metaclass=_SubscriptionMeta):
    """A class representing subscriptions in TeamTalk."""
