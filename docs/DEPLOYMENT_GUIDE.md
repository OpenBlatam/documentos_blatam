# 🚀 Guía de Despliegue - SaaS de IA para Marketing

## 📋 Prerrequisitos

### Requisitos del Sistema
- **Node.js**: 18.x o superior
- **Docker**: 20.x o superior
- **Kubernetes**: 1.24+ (opcional)
- **Base de datos**: PostgreSQL 14+
- **Cache**: Redis 6+

### Cuentas Requeridas
- **OpenAI**: Para GPT-4/GPT-3.5
- **Anthropic**: Para Claude
- **AWS/GCP**: Para infraestructura cloud
- **Stripe**: Para pagos (opcional)

## 🏗️ Arquitectura de Despliegue

### Opción 1: Despliegue Local (Desarrollo)
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ia-marketing-saas.git
cd ia-marketing-saas

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar servicios
docker-compose up -d

# Ejecutar migraciones
npm run migrate

# Iniciar aplicación
npm run dev
```

### Opción 2: Despliegue en Cloud (Producción)
```bash
# Configurar Kubernetes
kubectl apply -f k8s/

# Desplegar servicios
kubectl apply -f k8s/services/

# Configurar ingress
kubectl apply -f k8s/ingress/
```

## 🔧 Configuración de Variables de Entorno

### Archivo .env
```bash
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/ia_marketing
REDIS_URL=redis://localhost:6379

# APIs de IA
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Autenticación
JWT_SECRET=tu_jwt_secret_super_seguro
JWT_REFRESH_SECRET=tu_refresh_secret_super_seguro

# Servicios externos
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Configuración de la aplicación
NODE_ENV=production
PORT=3000
API_BASE_URL=https://api.ia-marketing.com

# Monitoreo
SENTRY_DSN=https://...
PROMETHEUS_PORT=9090

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_password_app
```

## 🐳 Despliegue con Docker

### Dockerfile Principal
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm ci --only=production

# Copiar código
COPY . .

# Compilar TypeScript
RUN npm run build

# Crear usuario no-root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Cambiar ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Exponer puerto
EXPOSE 3000

# Comando de inicio
CMD ["npm", "start"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/ia_marketing
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=ia_marketing
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

## ☸️ Despliegue con Kubernetes

### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ia-marketing
```

### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ia-marketing-config
  namespace: ia-marketing
data:
  NODE_ENV: "production"
  PORT: "3000"
  API_BASE_URL: "https://api.ia-marketing.com"
```

### Secrets
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ia-marketing-secrets
  namespace: ia-marketing
type: Opaque
data:
  DATABASE_URL: <base64_encoded>
  OPENAI_API_KEY: <base64_encoded>
  ANTHROPIC_API_KEY: <base64_encoded>
  JWT_SECRET: <base64_encoded>
```

### Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ia-marketing-app
  namespace: ia-marketing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ia-marketing-app
  template:
    metadata:
      labels:
        app: ia-marketing-app
    spec:
      containers:
      - name: app
        image: ia-marketing:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ia-marketing-secrets
              key: DATABASE_URL
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ia-marketing-secrets
              key: OPENAI_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ia-marketing-service
  namespace: ia-marketing
spec:
  selector:
    app: ia-marketing-app
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ia-marketing-ingress
  namespace: ia-marketing
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.ia-marketing.com
    secretName: ia-marketing-tls
  rules:
  - host: api.ia-marketing.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ia-marketing-service
            port:
              number: 80
```

## 🗄️ Configuración de Base de Datos

### PostgreSQL
```sql
-- Crear base de datos
CREATE DATABASE ia_marketing;

-- Crear usuario
CREATE USER ia_marketing_user WITH PASSWORD 'secure_password';

-- Asignar permisos
GRANT ALL PRIVILEGES ON DATABASE ia_marketing TO ia_marketing_user;

-- Crear extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Migraciones
```bash
# Ejecutar migraciones
npm run migrate

# Revertir migración
npm run migrate:rollback

# Ver estado de migraciones
npm run migrate:status
```

### Backup
```bash
# Crear backup
pg_dump -h localhost -U ia_marketing_user -d ia_marketing > backup.sql

# Restaurar backup
psql -h localhost -U ia_marketing_user -d ia_marketing < backup.sql
```

## 🔒 Configuración de Seguridad

### SSL/TLS
```bash
# Generar certificado con Let's Encrypt
certbot certonly --standalone -d api.ia-marketing.com

# Configurar renovación automática
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Firewall
```bash
# Configurar UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Nginx
```nginx
# nginx.conf
server {
    listen 80;
    server_name api.ia-marketing.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.ia-marketing.com;

    ssl_certificate /etc/letsencrypt/live/api.ia-marketing.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ia-marketing.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📊 Monitoreo y Logging

### Prometheus
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ia-marketing'
    static_configs:
      - targets: ['localhost:3000']
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "IA Marketing Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Logging
```javascript
// config/logging.js
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

module.exports = logger;
```

## 🚀 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test
    - name: Run linting
      run: npm run lint

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: docker build -t ia-marketing:${{ github.sha }} .
    - name: Push to registry
      run: docker push ia-marketing:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/ia-marketing-app \
          app=ia-marketing:${{ github.sha }}
        kubectl rollout status deployment/ia-marketing-app
```

## 🔧 Scripts de Utilidad

### Script de Despliegue
```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Iniciando despliegue..."

# Ejecutar tests
echo "🧪 Ejecutando tests..."
npm test

# Construir imagen Docker
echo "🐳 Construyendo imagen Docker..."
docker build -t ia-marketing:latest .

# Desplegar en Kubernetes
echo "☸️ Desplegando en Kubernetes..."
kubectl apply -f k8s/

# Esperar a que esté listo
echo "⏳ Esperando a que esté listo..."
kubectl rollout status deployment/ia-marketing-app

echo "✅ Despliegue completado!"
```

### Script de Backup
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump -h localhost -U ia_marketing_user -d ia_marketing > $BACKUP_DIR/db_$DATE.sql

# Backup de archivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /app/uploads

# Limpiar backups antiguos (más de 30 días)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "✅ Backup completado: $DATE"
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar conexión
psql -h localhost -U ia_marketing_user -d ia_marketing

# Verificar logs
kubectl logs deployment/ia-marketing-app
```

#### 2. Error de API Keys
```bash
# Verificar variables de entorno
kubectl get secret ia-marketing-secrets -o yaml

# Actualizar secret
kubectl create secret generic ia-marketing-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### 3. Problemas de Memoria
```bash
# Verificar uso de recursos
kubectl top pods

# Escalar horizontalmente
kubectl scale deployment ia-marketing-app --replicas=5
```

### Comandos Útiles

```bash
# Ver logs en tiempo real
kubectl logs -f deployment/ia-marketing-app

# Entrar al pod
kubectl exec -it deployment/ia-marketing-app -- /bin/bash

# Reiniciar deployment
kubectl rollout restart deployment/ia-marketing-app

# Ver estado de servicios
kubectl get all -n ia-marketing
```

## 📞 Soporte

### Contacto Técnico
- **Email**: devops@ia-marketing.com
- **Slack**: #devops-support
- **Documentación**: https://docs.ia-marketing.com

### Recursos Adicionales
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

*"Un despliegue exitoso es la base de un SaaS confiable y escalable."* 🚀✨
