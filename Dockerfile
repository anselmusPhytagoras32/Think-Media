FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    APP_FRONTEND_DIST=/app/frontend/dist
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY presentation/fictional-resume.pdf /app/presentation/fictional-resume.pdf
COPY --from=frontend /build/dist /app/frontend/dist
RUN useradd --create-home --uid 10001 thinkmedia
USER thinkmedia
EXPOSE 10000
CMD ["python", "-m", "ops.hosted"]
