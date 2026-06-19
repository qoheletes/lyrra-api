class EmailAlreadyExists(Exception):  # noqa: N818 — domain name reads better without suffix
    def __init__(self, email: str) -> None:
        super().__init__(f"Email {email!r} is already registered")
        self.email = email


class InvalidCredentials(Exception):  # noqa: N818 — domain name reads better without suffix
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InvalidToken(Exception):  # noqa: N818 — domain name reads better without suffix
    def __init__(self) -> None:
        super().__init__("Could not validate credentials")
