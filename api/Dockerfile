# Backend service
FROM node:18-alpine AS backend

WORKDIR /app/backend

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]

# Database service
FROM postgres:15-alpine AS db

ENV POSTGRES_DB=api_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

EXPOSE 5432

VOLUME ["/var/lib/postgresql/data"]

CMD ["postgres"]