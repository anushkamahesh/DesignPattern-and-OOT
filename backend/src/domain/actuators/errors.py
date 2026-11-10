class PolicyViolationError(Exception):
    """A decorator refused to apply a command. Carries the policy's name so the
    logging decorator can record which policy blocked the attempt."""

    def __init__(self, policy: str, message: str) -> None:
        super().__init__(message)
        self.policy = policy
        self.message = message