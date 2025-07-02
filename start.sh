\#!/usr/bin/env bash

# Script pour exécuter python clone.py et commit/push les résultats

# Usage: bash deploy\_clone.sh \<repo\_dir> <owner> <repo>

echo "🔄 Exécution du script snifftraffic.py..."
python3 snifftraffic.py merce-fra PELCA

# Ajout au staging
git add .

# Commit avec message 'Update Traffic <date>'
COMMIT_MSG="Update traffic $(date +'%Y-%m-%d %H:%M:%S')"
echo "📝 Commit avec message : $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# Push vers le remote
echo "⬆️ Pushing to remote..."
git push origin main

echo "✅ Déploiement terminé."
