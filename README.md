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

```bash
# linux
source .venv/bin/activate
```

```powershell
# windows
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
cd app && python3 main.py
```

## Configuration

The config_example.yaml file exists in the app/settings directory. Copy it to the same directory or rename it to config.yaml

```yaml
# config_example.yaml

byond:
  host:  # format "0.0.0.0"
  port: 
discord:
  bot_prefix: '!'
  case_insensitive: true
  token: # Your Discord bot token
openai:
  api_key: sk-...
  assistant_id: asst_...
  org_id: org-...
  project_id: proj_...
  thread_id: thread_... # Optional. If you don't have a thread ID, bot will create a new one and save it to this file.
```
