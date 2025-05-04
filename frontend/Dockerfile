# Step 1: Build React app using Yarn
FROM node:18 as builder

WORKDIR /app

# Install dependencies using yarn
COPY package.json yarn.lock ./
RUN yarn install

# Copy all source files and build
COPY . .
RUN yarn build

# Step 2: Serve with nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
