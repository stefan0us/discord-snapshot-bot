FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

ADD requirements.txt .
RUN pip3 install -r requirements.txt

ADD https://raw.githubusercontent.com/berstend/puppeteer-extra/stealth-js/stealth.min.js .

COPY src .

CMD ["python3", "discord_snapshot_bot.py"]
