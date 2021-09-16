FROM python:3.7
WORKDIR /RoboFin
COPY ./RoboFin /RoboFin
# ENV PYTHONUNBUFFERED=1
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
CMD python manage.py migrate \
  && python manage.py loaddata ./fixtures/data.json \
  && python manage.py runserver 0.0.0.0:8000