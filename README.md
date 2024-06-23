# Modular discord bot

---

## Description

Bot for managing discord server ss13(Rockhill)

## Functions

### AI module

- [mind]: queries llm and sends a response.
- [ai_new_thread]: (privileged) runs a new thread.
- [ai_help]: (privileged) shows help.
- [ai_switch_on]: (privileged) switch on ai.
- [ai_switch_off]: (privileged) switch off ai.
- [ai_max_requests]: (privileged) set max requests. Default is 10.
- [ai_reset_requests]: (privileged) reset requests counter.

### Byond settings module

- [setup_host]: (privileged) sets host.
- [setup_port]: (privileged) sets port.

### Status module1254111603985485887

- [modstatus]: (privileged) show status of modules.

## Installation

before you start, you need to install the following software:

### Python 3.12

#### Windows/Ubuntu 24.04

- [Python 3.12](https://www.python.org/downloads/release/python-3120/) preferably
- [Docker](https://docs.docker.com/get-docker/) **if you want to run the bot in a container**

#### Ubuntu 24.04 cmd

```bash
apt install -y python3 python3-pip
```

> before check version of python3 `python3 --version`
> if version is not 3.12, you need to install it manually. Here is a guide for ubuntu 20.04, but it should work on other versions as well. [Install python 3.12](https://wiki.crowncloud.net/?How_to_Install_Python_3_12_on_Ubuntu_20_04)

### Python virtual environment

### Требования

- [Указать требования, например, Python, Node.js, Docker и т. д.]
- [Указать версии библиотек и фреймворков, например, discord.py, discord.js]

### Шаги установки

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/ваш_пользователь/ваш_репозиторий.git
