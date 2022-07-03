FROM mcr.microsoft.com/playwright/python:v1.21.0-focal

RUN pip3 install discord.py

WORKDIR /app

COPY src .

CMD ["python3", "discord_snapshot_bot.py"]
