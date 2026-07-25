#!/bin/bash
set -e
echo "== Health =="
curl -s http://localhost:8000/health
echo
echo "== Lista de libros (debe estar vacía) =="
curl -s http://localhost:8000/api/books
echo
echo "== Detalle de libro inexistente (debe ser 404) =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/books/1
