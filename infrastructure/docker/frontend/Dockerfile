FROM node:22-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json frontend/pnpm-lock.yaml* ./frontend/
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    corepack enable && pnpm install --frozen-lockfile 2>/dev/null || pnpm install

COPY frontend /app/frontend

WORKDIR /app/frontend

EXPOSE 3000

CMD ["pnpm", "dev"]
