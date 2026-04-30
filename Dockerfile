FROM postgres:latest

LABEL maintainer="Lucas Kluska Donini"

COPY ./sql/init-db.sql /docker-entrypoint-initdb.d/
COPY ./.psqlrc /etc/postgresql-common/psqlrc

EXPOSE 5432
VOLUME [ "pgdata" ]

CMD [ "postgres" ]