class InvalidTransition(Exception):
    pass

class JobStateMachine:
    VALID_TRANSITIONS = {
        'pending': {'running'},
        'running': {'done', 'failed', 'cancelled'},
        'failed': {'pending'},  # retry
        'done': set(),          # terminal
        'cancelled': set(),     # terminal
    }

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def can_transition(self, from_status: str, to_status: str) -> bool:
        allowed = self.VALID_TRANSITIONS.get(from_status, set())
        return to_status in allowed

    def transition(self, from_status: str, to_status: str) -> str:
        if not self.can_transition(from_status, to_status):
            raise InvalidTransition(
                f"Cannot transition from '{from_status}' to '{to_status}'"
            )
        return to_status

    def can_retry(self, retry_count: int) -> bool:
        return retry_count < self.max_retries
