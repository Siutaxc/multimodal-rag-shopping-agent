FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN --mount=type=cache,target=/root/.npm npm config set fetch-retries 10 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && (npm ci --prefer-offline \
        || npm ci --prefer-offline \
        || npm ci --prefer-offline)

FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS builder
WORKDIR /workspace
ARG NEXT_PUBLIC_SHOPLENS_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_SHOPLENS_SITE_URL=http://localhost:3000
ENV NEXT_PUBLIC_SHOPLENS_API_BASE_URL=$NEXT_PUBLIC_SHOPLENS_API_BASE_URL
ENV NEXT_PUBLIC_SHOPLENS_SITE_URL=$NEXT_PUBLIC_SHOPLENS_SITE_URL
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web ./apps/web
RUN npm run build --workspace @shoplens/web

FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS runner
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs --ingroup nodejs
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/web/public ./apps/web/public
USER nextjs
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
