import asyncio
import logging
import uuid

from langchain_core.messages import HumanMessage

from .agents import execute_agent_flux
from .infrastructure.console_utils import clear_console
from .infrastructure.logger import set_session_context, setup_logger
from .infrastructure.md_console import print
from .infrastructure.mongo_connection import MongoManager
from .services.chat_session_service import ChatSessionService
from .services.session_summary_service import SessionSummaryService


async def main() -> None:
    session_id = str(uuid.uuid4())
    set_session_context(session_id)
    summary_service = SessionSummaryService()
    session_service = ChatSessionService(summary_service)
    try:
        mongo_manager = MongoManager()
        await mongo_manager.init_database()
        await session_service.init_session(session_id)
        await _execute_interaction_loop(session_id=session_id, service=session_service)

    except Exception as e:
        logger.exception(
            "Unhandled error",
            extra={"details": {"session": session_id[:8]}},
        )
        await session_service.save_error(session_id, e)
        print("**Unknow error ocurred! Try again later.**")

    finally:
        await session_service.finalize_session(session_id)


async def _execute_interaction_loop(
    service: ChatSessionService, session_id: str
) -> None:
    clear_console()
    print("\n# Bem vindo! Converse hoje mesmo com o Assessor.IA!!\n")

    while True:
        user_input = input(">>> ")
        if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
            print("Encerrando a conversa")
            break

        question = HumanMessage(id=str(uuid.uuid4()), content=user_input)
        await service.save_message(session_id=session_id, message=question)
        response = await execute_agent_flux(question, session_id)
        await service.save_message(session_id=session_id, message=response)
        print(f"\n{response.content}\n\n---\n\n")


if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("App started", extra={"details": {"state": "booting"}})
    asyncio.run(main())
    logger.info("App closed", extra={"details": {"state": "shutdown"}})
