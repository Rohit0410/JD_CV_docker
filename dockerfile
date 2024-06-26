FROM python:3.9-slim-buster
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5005
ENV FLASK_APP=app.py
CMD ["FLASK_APP", "run", "--host", "0.0.0.0"]