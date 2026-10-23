# Statický web na Railway: Caddy servíruje soubory z /srv, TLS řeší Railway.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY . /srv
# Konfigurace a dokumentace nemají být veřejně ke stažení
RUN cd /srv && rm -rf Dockerfile Caddyfile .dockerignore railway.json README.md CNAME .nojekyll .gitignore tools
