# APIs consumidas — WorldCup (modelo de apostas Copa 2026)

Documento de referência: **quais APIs o sistema usa, o que cada uma fornece e como consumir**
(endpoint, autenticação, parâmetros, limites). Tudo é chamado via `requests`/SDK em `scrapers/`.

> Convenção: chaves vêm de variáveis de ambiente (`.env` local) ou `st.secrets` (Streamlit Cloud).
> No Windmill, vêm de `wmill.get_variable("u/felipefelix/...")`.

---

## Resumo rápido

| API | Pra quê | Chave? | Limite | Custo |
|-----|---------|--------|--------|-------|
| **The Odds API** | Odds Pinnacle (sharp) + placares | `ODDS_API_KEY` | 500 req/mês | grátis (tier free) |
| **ESPN** | Odds DraftKings (1X2) + placares + escalação | não | — | grátis |
| **API-Football** | Escalação oficial (fallback) | `API_FOOTBALL_KEY` | 100 req/dia | grátis (tier free) |
| **TheSportsDB** | Escalação oficial | key pública `3` | branda | grátis |
| **Sofascore** | Escalação (fallback, não-oficial) | não | bloqueia (Cloudflare) | grátis |
| **Open-Meteo** | Clima (temp/umidade/vento) | não | branda | grátis |
| **eloratings.net** | Rating ELO das seleções | não | — | grátis (scrape) |
| **martj42/results** | Histórico de jogos (treino do modelo) | não | — | grátis (GitHub raw) |
| **Wikipedia** | Tabela de jogos da Copa 2026 | não | rate-limit 0.5s | grátis (scrape) |
| **Transfermarkt** | Valor de elenco | não | rate-limit 1.2s | grátis (scrape) |
| **worldreferee / worldfootball** | Árbitros | não | — | grátis (scrape) |
| **Anthropic (Claude)** | Validador LLM com web search (opcional) | `ANTHROPIC_API_KEY` | — | ~US$0.035/call |
| **GitHub API** | Dispara o workflow de precompute | `GITHUB_PAT` | — | grátis |
| **S3 (OVH)** | Armazenamento (calibração/snapshots/bets) | `S3_*` | — | conta OVH |

---

## 1. The Odds API — odds sharp (Pinnacle) + placares
- **Pra quê:** benchmark sharp (Pinnacle no-vig) pra O/U; e placares finais pra liquidar/aprender.
- **Base:** `https://api.the-odds-api.com/v4`
- **Auth:** query `apiKey=ODDS_API_KEY`. Cadastro: https://the-odds-api.com
- **Endpoints:**
  - Odds: `GET /sports/soccer_fifa_world_cup/odds?apiKey=...&regions=eu&markets=h2h,totals&bookmakers=pinnacle&oddsFormat=decimal&dateFormat=iso`
  - Placares: `GET /sports/soccer_fifa_world_cup/scores?apiKey=...&daysFrom=3`
- **Limite:** **500 requisições/mês** (free). Custo = 1 req × nº de markets (h2h,totals = 2 créditos/chamada).
- **Cuidados:** placar só até **3 dias** (`daysFrom<=3`); BTTS e placar exato **não** são cobertos por esse endpoint. O sistema só chama Pinnacle perto do kickoff pra economizar quota.
- **Código:** `scrapers/odds_api.py`, `scrapers/scores_api.py`

## 2. ESPN — odds DraftKings (1X2) + placares + escalação
- **Pra quê:** benchmark 1X2 grátis (DraftKings, preserva quota Pinnacle); placares fallback; escalação.
- **Base:** `http://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world`
- **Auth:** **nenhuma** (pública).
- **Endpoints:**
  - `GET /scoreboard?dates=YYYYMMDD` → jogos do dia (odds DraftKings em `competitions[].odds`, placares, status).
  - `GET /summary?event=EVENT_ID` → rosters/escalação.
- **Limite:** sem chave; uso comedido. **Limitação:** só publica moneyline 1X2 (sem O/U pra soccer).
- **Código:** `scrapers/espn_odds.py`, `scrapers/scores_api.py`, `scrapers/lineup_fallback.py`

## 3. API-Football (api-sports.io) — escalação oficial (fallback)
- **Pra quê:** XI oficial quando ESPN/TheSportsDB falham.
- **Base:** `https://v3.football.api-sports.io`
- **Auth:** header `x-apisports-key: API_FOOTBALL_KEY`. Cadastro grátis: https://dashboard.api-football.com
- **Endpoints:** `GET /fixtures?date=YYYY-MM-DD&timezone=UTC` → acha o fixture; `GET /fixtures/lineups?fixture=FIXTURE_ID` → escalação.
- **Limite:** **100 req/dia** (free).
- **Código:** `scrapers/lineup_fallback.py`

## 4. TheSportsDB — escalação oficial
- **Pra quê:** escalação (fonte primária de lineup).
- **Base:** `https://www.thesportsdb.com/api/v1/json/3` (a key `3` é a pública gratuita).
- **Auth:** key pública `3` embutida na URL.
- **Limite:** brando; instável às vezes.
- **Código:** `scrapers/sportsdb.py`

## 5. Sofascore — escalação (fallback não-oficial)
- **Pra quê:** última tentativa de escalação.
- **Base:** `https://api.sofascore.com/api/v1`
- **Auth:** nenhuma, mas exige `User-Agent` de browser. **Cloudflare bloqueia com frequência (403)** — é best-effort.
- **Código:** `scrapers/lineup_fallback.py`

## 6. Open-Meteo — clima
- **Pra quê:** temperatura/umidade/vento (ajuste de contexto — calor extremo reduz gols).
- **Base:** previsão `https://api.open-meteo.com/v1/forecast` · histórico (>7 dias) `https://archive-api.open-meteo.com/v1/archive`
- **Auth:** **nenhuma** (grátis pra uso não-comercial).
- **Params:** `latitude, longitude, hourly=<vars>, start_date, end_date, timezone=auto, wind_speed_unit=kmh`
- **Código:** `scrapers/weather.py`

## 7. eloratings.net — rating ELO
- **Pra quê:** força relativa das seleções (entra no modelo).
- **Endpoint:** `GET https://www.eloratings.net/World.tsv` (TSV; precisa `User-Agent`).
- **Auth:** nenhuma. **Código:** `scrapers/elo.py`

## 8. martj42/international_results — histórico de jogos
- **Pra quê:** dataset histórico que **treina** o modelo Poisson/Dixon-Coles.
- **Endpoint:** `GET https://raw.githubusercontent.com/martj42/international_results/master/results.csv`
- **Auth:** nenhuma. Cache local 24h. **Código:** `data_loader.py`

## 9. Wikipedia — tabela de jogos da Copa 2026
- **Pra quê:** fixtures (jogos, datas, grupos).
- **Endpoint:** `GET https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_{A..L}` (scrape HTML).
- **Auth:** nenhuma; `User-Agent` + rate-limit 0.5s. **Código:** `scrapers/worldcup_fixtures.py`

## 10. Transfermarkt — valor de elenco
- **Pra quê:** valor de mercado do plantel (contexto do modelo).
- **Base:** `https://www.transfermarkt.com` (scrape; IDs das seleções no `config.py`).
- **Auth:** nenhuma; `User-Agent` + rate-limit 1.2s entre requests. **Código:** `config.py`, scraper de squads.

## 11. worldreferee.com / worldfootball.net — árbitros
- **Pra quê:** dados de árbitro (cartões/perfil).
- **Endpoints:** `https://worldreferee.com/referee/{slug}`, `https://www.worldfootball.net` (scrape).
- **Auth:** nenhuma. **Código:** `scrapers/referees.py`

## 12. Anthropic (Claude) — validador LLM (opcional)
- **Pra quê:** camada opcional que busca notícias (lesão/escalação/clima) via web search e dá verdict GO/CAUTION/NO_GO.
- **Auth:** SDK `anthropic` com `ANTHROPIC_API_KEY` (https://console.anthropic.com). `pip install anthropic`.
- **Config:** modelo `claude-sonnet-4-6`, `max_tokens=1024`, `web_search` (máx 3 buscas, domínios confiáveis), prompt cache no system.
- **Custo:** ~US$0.035/call (~US$60/mês a 50 bets/dia). **Desligado** se a key não existir.
- **Código:** `llm_validator.py`

## 13. GitHub API — dispara o precompute
- **Pra quê:** acionar o workflow `worldcup-precompute.yml` sob demanda.
- **Endpoints:** `POST https://api.github.com/repos/felipedxon/GERAL/actions/workflows/{file}/dispatches` (body `{"ref":"main"}`); `GET .../runs?per_page=1` (status).
- **Auth:** header `Authorization: Bearer GITHUB_PAT` (PAT com permissão de Actions). **Código:** `github_dispatcher.py`

## 14. S3 (OVH) — armazenamento
- **Pra quê:** persistir calibração (`model_calibration.json`), snapshots (`odds_history/`), apostas (`bets.jsonl`), previsões (`precomputed/`).
- **Auth:** `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_PREFIX`, `S3_REGION` (boto3).
- **Endpoint atual:** OVH `s3.us-west-or.io.cloud.ovh.us`, bucket `dxon-playground`, prefixo `felipefelix/world_cup`.
- **Código:** `clv_logger.py`, `odds_history.py`, `model_calibration.py`

---

## Variáveis de ambiente / secrets (resumo)
| Variável | Obrigatória? | Usada por |
|----------|--------------|-----------|
| `ODDS_API_KEY` | recomendada | Pinnacle odds + placares |
| `API_FOOTBALL_KEY` | opcional | escalação fallback |
| `ANTHROPIC_API_KEY` | opcional | validador LLM |
| `GITHUB_PAT` | opcional | disparar precompute |
| `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/`S3_SECRET_KEY`/`S3_BUCKET`/`S3_PREFIX`/`S3_REGION` | recomendada | armazenamento |
| `BANKROLL` | sim | gestão (Kelly) |

Sem nenhuma chave o app ainda roda: usa ESPN (1X2 grátis), Open-Meteo, ELO e a própria odd digitada — só perde o benchmark Pinnacle, a escalação por API e o validador LLM.
