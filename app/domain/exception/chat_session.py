class ChatSessionException(Exception):
    def __init__(self, *, code: str, session_id: str, public_message: str) -> None:
        self.code = code
        self.session_id = session_id
        self.public_message = public_message
        super().__init__(self.public_message)


class ChatSessionAlreadyFinalizedException(ChatSessionException):
    def __init__(self, session_id: str) -> None:
        super().__init__(
            session_id=session_id,
            code="chat_session_already_finalized",
            public_message=(
                "The session is already finalized. You must start a new one."
            ),
        )


class ChatSessionNotFoundException(ChatSessionException):
    def __init__(self, session_id: str) -> None:
        super().__init__(
            session_id=session_id,
            code="chat_session_not_found",
            public_message="This session does not exist",
        )


class ChatSessionWriteConflictException(ChatSessionException):
    def __init__(self, session_id: str) -> None:
        super().__init__(
            session_id=session_id,
            code="chat_session_write_conflict",
            public_message=(
                "The session was altered by another operation. Try again later."
            ),
        )
