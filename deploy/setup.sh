#!/bin/bash
# Log all output to a file for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting EC2 Cloud-Init setup for ProjectPulse AI..."

# 1. Update system packages
apt-get update -y

# 2. Install Docker
apt-get install -y docker.io
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# 3. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 4. Clone the repository
cd /home/ubuntu
git clone https://github.com/user73730102/ProjectPulse.ai.git
cd ProjectPulse.ai

# 5. Make sure the ubuntu user owns the files
chown -R ubuntu:ubuntu /home/ubuntu/ProjectPulse.ai

# 6. We will pause the script here.
# We do NOT run `docker-compose up` yet because you need to SSH into the machine 
# and paste your GROQ_API_KEY into backend/.env first!

echo "Setup complete! Docker and the repository are ready."
