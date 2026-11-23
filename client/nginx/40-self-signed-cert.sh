#!/bin/sh
# Runs before nginx starts. For real deployments, mount your certificate and key at
# /etc/nginx/certs/tls.crt and /etc/nginx/certs/tls.key and this does nothing.
# Otherwise a self-signed development certificate is generated (browsers will warn).
set -e
CERT_DIR=/etc/nginx/certs
if [ -f "$CERT_DIR/tls.crt" ] && [ -f "$CERT_DIR/tls.key" ]; then
  echo "TLS: using the provided certificate"
  exit 0
fi
mkdir -p "$CERT_DIR"
openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
  -keyout "$CERT_DIR/tls.key" -out "$CERT_DIR/tls.crt" 2>/dev/null
echo "TLS: generated a self-signed development certificate"
