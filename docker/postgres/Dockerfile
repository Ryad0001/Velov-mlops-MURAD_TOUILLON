# Image Postgres du projet : l'image officielle + le schéma de la table predictions.
# Tout fichier .sql dans /docker-entrypoint-initdb.d/ est joué au premier démarrage
# (volume vide). Un volume déjà initialisé n'est pas rejoué.
FROM postgres:17-alpine

COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
