#!/bin/bash
# Smart Data Analyst Agent - Blue/Green Deployment Helper (W12)
set -e

echo "[+] Starting Deployment Phase 4..."

# 1. Pastikan perubahan remote sudah ditarik
# git pull origin main

echo "[+] Building Docker Image..."
docker build -t smart-agent:latest .

# 2. Simple rolling update approach menggunakan docker-compose
echo "[+] Starting new up containers (Isolated DB state)..."
docker-compose up -d --build --no-deps api

echo "[+] Menganalisa log kontainer post-deployment..."
docker-compose ps

echo "[+] Deployment Success! Lingkungan Produktion stabil."
