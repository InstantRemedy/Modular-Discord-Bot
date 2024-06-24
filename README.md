# Modular discord bot

---

## Description

Bot for managing discord server ss13(Rockhill)

## Functions

### AI

- [mind]: queries llm and sends a response.
- [ai_new_thread]: (privileged) runs a new thread.
- [ai_help]: (privileged) shows help.
- [ai_switch_on]: (privileged) switch on ai.
- [ai_switch_off]: (privileged) switch off ai.
- [ai_max_requests]: (privileged) set max requests. Default is 10.
- [ai_reset_requests]: (privileged) reset requests counter.

### Byond settings

- [setup_host]: (privileged) sets host.
- [setup_port]: (privileged) sets port.

### Status module

- [modstatus]: (privileged) show status of modules.

## Installation

Clone the repository:

```bash
git clone https://github.com/InstantRemedy/Modular-Discord-Bot.git
```

### Docker

```bash
cd Modular-Discord-Bot
```

```bash
docker build -t modular-discord-bot .
```

```bash
docker run -d --name modular-discord-bot modular-discord-bot --volume /path/to/config:/app/config --volume /path/to/logs:/app/logs
```

#### Docker-compose

```bash
cd Modular-Discord-Bot
```

```yaml
version: '3.0'

services:
  rockhill_discord_bot:
    build:
      context: .
      dockerfile: Dockerfile
    image: modular-discord-bot
    container_name: modular-discord-bot
    restart: always
    volumes:
      - ./settings:/app/settings
      - ./logs:/app/logs
```

```bash
docker-compose up -d
```

### Python virtual environment

```bash
cd Modular-Discord-Bot
```

```bash
python3 -m venv .venv
```
