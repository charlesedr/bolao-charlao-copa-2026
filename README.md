# 🏆 Bolão Charlão Copa 2026

Plataforma web gratuita para um bolão de palpites da **Copa do Mundo FIFA 2026**
(48 seleções, 12 grupos, 104 jogos). Os participantes se cadastram, são aprovados
pelo administrador e palpitam nos jogos; o sistema calcula a pontuação e mantém o
ranking ao vivo. Projeto recreativo, **100% Python**, sem fins comerciais.

## ✨ Funcionalidades

- **Cadastro e login** (por apelido ou e-mail), com aprovação do administrador
- **Palpites** nos jogos, com trava automática **5 minutos antes** de cada partida
- **Pontuação automática**: fase de grupos (até 5 pts), mata-mata (até 6 pts) e
  aposta de classificação final (até 4 pts)
- **Ranking** com critérios de desempate (placares exatos → resultados → gols)
- **Minha Copa**: simulação dos grupos pelos seus palpites + prévia/chave do mata-mata
- **Avanço automático do mata-mata** e preenchimento das 32avas via tabela oficial
  da FIFA (Anexo C — 495 combinações dos 3º colocados)
- **Tela da Partida** (palpites de todos, visíveis após o início), **Comparar** e **Perfil**
- Painel **administrativo**: aprovar/bloquear usuários, lançar placares, recalcular
- Tela **"Como Funciona"** com as regras explicadas

## 🧰 Stack

- **Python 3.12** + **Streamlit** (UI multipage)
- **PostgreSQL** (Neon) com **SQLModel** + **Alembic** (migrações)
- Autenticação própria: **bcrypt** + **JWT** em cookie
- **pytest** (regras de pontuação/classificação) + **ruff** (lint/format)
- Deploy gratuito: **Streamlit Community Cloud** + **Neon**

## 🚀 Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell)
pip install -r requirements-dev.txt

copy .env.example .env            # preencha DATABASE_URL, SECRET_KEY, ADMIN_*

alembic upgrade head              # cria o schema
python scripts/seed_selecoes_grupos.py
python scripts/seed_partidas.py
python scripts/criar_admin.py

streamlit run streamlit_app.py
```

## ⚙️ Variáveis de ambiente (`.env`)

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | Conexão Postgres (`postgresql+psycopg://...`) |
| `SECRET_KEY` | Chave para assinar o cookie de sessão (JWT) |
| `TZ_DISPLAY` | Fuso de exibição (`America/Sao_Paulo`) |
| `ADMIN_*` | Dados do admin para o `criar_admin.py` |

> O arquivo `.env` **não é versionado**. Em produção, os segredos ficam nos
> *Secrets* do Streamlit Community Cloud.

## 🏅 Regras de pontuação (resumo)

- **Grupos (máx 5):** +1 gols mandante · +1 gols visitante · +2 resultado · +1 placar exato
- **Mata-mata (máx 6):** base dos grupos (placar dos **90 min**) · +1 por acertar quem avança
- **Aposta final (máx 4):** +1 por acerto em campeão, vice, 3º e 4º

## 🧪 Testes e qualidade

```bash
pytest          # testes de pontuação, classificação, trava e chaveamento
ruff check .    # lint/format
```

## 📁 Estrutura

```
streamlit_app.py        # entry point + navegação por perfil
app/core/               # config, db, segurança, fuso, tema
app/domain/             # models (SQLModel) e enums
app/repositories/       # acesso a dados
app/services/           # regras de negócio (pontuação, simulação, chaveamento...)
app/ui/                 # tema, sessão e telas (views)
data/                   # CSVs oficiais (seleções, jogos, Anexo C)
scripts/                # seeds e utilitários
tests/                  # testes automatizados
alembic/                # migrações
```
