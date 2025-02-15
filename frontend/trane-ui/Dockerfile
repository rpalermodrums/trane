# Use Node.js LTS version as base image
FROM node:20

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# RUN ls -la && pwd && cat pnpm-lock.yaml

# Copy package files
# COPY package.json pnpm-lock.yaml ./

# # Install dependencies
# RUN pnpm install --frozen-lockfile
# RUN pnpm install

# # Copy source code
# COPY . .

# # Build the application
# RUN pnpm build

# # Install serve to run the built app
# RUN pnpm install -g serve

# # Expose port 3000
# EXPOSE 3000

# # Start the application
# CMD ["serve", "-s", "dist", "-l", "3000"]
