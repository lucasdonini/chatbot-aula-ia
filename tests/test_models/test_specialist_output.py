from src.model.specialist_output import AgendaOutput, FinancialOutput, SpecialistOutput


class TestSpecialistOutput:
    def test_create_minimal(self):
        output = SpecialistOutput(
            dominio="agenda",
            intencao="consultar",
            resposta="Você tem 2 compromissos hoje.",
        )
        assert output.dominio == "agenda"
        assert output.intencao == "consultar"
        assert output.resposta == "Você tem 2 compromissos hoje."
        assert output.recomendacao == ""
        assert output.esclarecer is None
        assert output.janela_tempo is None

    def test_create_full(self):
        output = SpecialistOutput(
            dominio="financeiro",
            intencao="inserir",
            resposta="Transação registrada.",
            recomendacao="Confirma?",
            esclarecer="Qual o valor?",
            janela_tempo={"de": "2026-06-01", "ate": "2026-06-30", "rotulo": "mês"},
        )
        assert output.esclarecer == "Qual o valor?"
        assert output.janela_tempo["rotulo"] == "mês"

    def test_model_dump_roundtrip(self):
        original = SpecialistOutput(
            dominio="agenda",
            intencao="criar",
            resposta="Evento criado.",
            recomendacao="Verifique a agenda.",
        )
        data = original.model_dump()
        restored = SpecialistOutput.model_validate(data)
        assert restored.dominio == original.dominio
        assert restored.intencao == original.intencao
        assert restored.resposta == original.resposta


class TestFinancialOutput:
    def test_default_dominio(self):
        output = FinancialOutput(
            intencao="consultar",
            resposta="Saldo de R$ 5.000,00.",
        )
        assert output.dominio == "financeiro"

    def test_with_escrita(self):
        output = FinancialOutput(
            intencao="inserir",
            resposta="Transação adicionada.",
            escrita=[{"operacao": "adicionar", "id": 1}],
        )
        assert output.escrita == [{"operacao": "adicionar", "id": 1}]

    def test_with_indicadores(self):
        output = FinancialOutput(
            intencao="consultar",
            resposta="Saldo consultado.",
            indicadores={"saldo": 7600.0, "receitas": 8000.0},
        )
        assert output.indicadores["saldo"] == 7600.0

    def test_escrita_optional(self):
        output = FinancialOutput(
            intencao="consultar",
            resposta="Saldo positivo.",
        )
        assert output.escrita is None

    def test_indicadores_optional(self):
        output = FinancialOutput(
            intencao="consultar",
            resposta="Saldo positivo.",
        )
        assert output.indicadores is None

    def test_inherits_specialist_fields(self):
        output = FinancialOutput(
            intencao="deletar",
            resposta="Transação deletada.",
            recomendacao="Nada mais.",
            esclarecer="Tem certeza?",
        )
        assert output.recomendacao == "Nada mais."
        assert output.esclarecer == "Tem certeza?"

    def test_model_dump_roundtrip(self):
        original = FinancialOutput(
            intencao="consultar",
            resposta="Saldo de R$ 1.000,00.",
            escrita=[{"operacao": "adicionar", "id": 99}],
        )
        data = original.model_dump()
        restored = FinancialOutput.model_validate(data)
        assert restored.dominio == "financeiro"
        assert restored.escrita == [{"operacao": "adicionar", "id": 99}]


class TestAgendaOutput:
    def test_default_dominio(self):
        output = AgendaOutput(
            intencao="criar",
            resposta="Compromisso criado.",
        )
        assert output.dominio == "agenda"

    def test_with_acompanhamento(self):
        output = AgendaOutput(
            intencao="criar",
            resposta="Evento agendado.",
            acompanhamento="Deseja adicionar lembrete?",
        )
        assert output.acompanhamento == "Deseja adicionar lembrete?"

    def test_with_evento(self):
        output = AgendaOutput(
            intencao="criar",
            resposta="Evento criado.",
            evento={
                "titulo": "Reunião",
                "data": "2026-07-01",
                "inicio": "10:00",
                "fim": "11:00",
            },
        )
        assert output.evento["titulo"] == "Reunião"

    def test_acompanhamento_optional(self):
        output = AgendaOutput(
            intencao="consultar",
            resposta="Nenhum evento.",
        )
        assert output.acompanhamento is None

    def test_evento_optional(self):
        output = AgendaOutput(
            intencao="consultar",
            resposta="Agenda vazia.",
        )
        assert output.evento is None

    def test_inherits_specialist_fields(self):
        output = AgendaOutput(
            intencao="disponibilidade",
            resposta="Você está livre.",
            recomendacao="Quer agendar algo?",
            janela_tempo={"de": "2026-07-01T10:00", "ate": "2026-07-01T11:00"},
        )
        assert output.janela_tempo["de"] == "2026-07-01T10:00"

    def test_model_dump_roundtrip(self):
        original = AgendaOutput(
            intencao="cancelar",
            resposta="Evento cancelado.",
            acompanhamento="Reagende?",
        )
        data = original.model_dump()
        restored = AgendaOutput.model_validate(data)
        assert restored.dominio == "agenda"
        assert restored.acompanhamento == "Reagende?"
