FROM python:3

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENV FLASK_APP main.py
ENV FLASK_ENV development

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000", "--reload", "--debugger", "--eager-loading", "--with-threads"]