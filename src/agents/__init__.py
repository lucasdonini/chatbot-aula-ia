from .router import router_app
from .financial import financial_app
from .agenda import agenda_app
from .orquestrator import orquestrator_app
from .faq_reader import faq_reader_app

SPECIALISTS = {"financeiro": financial_app, "agenda": agenda_app, "faq": faq_reader_app}
