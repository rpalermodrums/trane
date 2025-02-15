# Build stage
FROM node:20-slim AS installer
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN npm install -g npm@latest
RUN npm install -g corepack@latest
RUN corepack enable

# Copy package files and install dependencies
COPY package.json pnpm-lock.yaml /app/
WORKDIR /app
RUN pnpm install --frozen-lockfile


FROM node:20-slim AS builder
COPY --from=installer /app/node_modules /app/node_modules
# Copy source code and build the application
COPY . /app
WORKDIR /app
RUN pnpm build


# Production stage
FROM nginx:alpine
# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
# Start nginx in non-daemon mode on port 80
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
