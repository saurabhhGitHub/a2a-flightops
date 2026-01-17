#!/bin/bash
# Heroku Deployment Script for a2a-flightops

echo "🚀 Starting Heroku deployment..."

# 1. Login to Heroku
echo "📝 Logging into Heroku..."
heroku login

# 2. Create Heroku app (if not exists)
echo "📦 Creating Heroku app..."
heroku create a2a-flightops 2>/dev/null || echo "App already exists"

# 3. Add PostgreSQL addon (lowest tier - Essential)
echo "🗄️  Adding PostgreSQL addon (Essential tier)..."
heroku addons:create heroku-postgresql:essential-0 --app a2a-flightops 2>/dev/null || echo "PostgreSQL addon already exists"

# 4. Set environment variables
echo "🔐 Setting environment variables..."
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())') --app a2a-flightops
heroku config:set DEBUG=False --app a2a-flightops
heroku config:set GEMINI_API_KEY=AIzaSyCDlkQfCD8_K3ASXwjER_J93DJTHymsb_A --app a2a-flightops
heroku config:set ALLOWED_HOSTS=a2a-flightops.herokuapp.com,localhost,127.0.0.1 --app a2a-flightops

# 5. Add Heroku remote if not exists
echo "🔗 Adding Heroku remote..."
git remote add heroku https://git.heroku.com/a2a-flightops.git 2>/dev/null || echo "Heroku remote already exists"

# 6. Deploy to Heroku
echo "📤 Deploying to Heroku..."
git push heroku main

# 7. Run migrations
echo "🔄 Running database migrations..."
heroku run python manage.py migrate --app a2a-flightops

echo "✅ Deployment complete!"
echo "🌐 Your app is available at: https://a2a-flightops.herokuapp.com"
echo ""
echo "📋 Next steps:"
echo "   - Create superuser: heroku run python manage.py createsuperuser --app a2a-flightops"
echo "   - View logs: heroku logs --tail --app a2a-flightops"
echo "   - Open app: heroku open --app a2a-flightops"
