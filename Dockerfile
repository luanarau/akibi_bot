
FROM python:3.8

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install -r requirements2.txt

COPY . .

CMD python bot.py