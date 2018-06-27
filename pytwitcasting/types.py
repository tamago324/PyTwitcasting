from typing import (
    Dict,
    Union,
    Optional
)

from pytwitcasting.api import API
from pytwitcasting.auth import (
    TwitcastingApplicationBasis,
    TwitcastingImplicit,
    TwitcastingOauth
)
from pytwitcasting.models import (
    App,
    Category,
    Comment,
    Credentials,
    Movie,
    SubCategory,
    User,
    WebHook
)

Basis = TwitcastingApplicationBasis
Implicit = TwitcastingImplicit
Oauth = TwitcastingOauth

Header = Dict[str, str]
