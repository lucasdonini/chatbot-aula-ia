def make_message_human(content: str) -> dict:
    return {"role": "human", "content": content}


def make_message_assistant(content: str) -> dict:
    return {"role": "assistant", "content": content}
