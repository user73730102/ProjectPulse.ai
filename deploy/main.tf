provider "aws" {
  region = "us-east-1"
}

# 1. Create a Default VPC Security Group for ProjectPulse
resource "aws_security_group" "pulse_sg" {
  name        = "projectpulse-sg"
  description = "Allow inbound traffic for Frontend, Backend, and SSH"

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Next.js Frontend
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI Backend
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic (so EC2 can pull Docker images & use Groq API)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Find the latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# 3. Create the EC2 Instance
resource "aws_instance" "pulse_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "m7i-flex.large"
  
  vpc_security_group_ids = [aws_security_group.pulse_sg.id]

  # Inject the startup script (Cloud-Init) to install Docker and run the app automatically
  user_data = file("setup.sh")

  tags = {
    Name = "ProjectPulse-Live-Demo"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }
}

# Output the IP Address so we know where to connect!
output "frontend_url" {
  value       = "http://${aws_instance.pulse_server.public_ip}:3000"
  description = "The public URL for the Next.js Frontend."
}

output "backend_url" {
  value       = "http://${aws_instance.pulse_server.public_ip}:8000"
  description = "The public URL for the FastAPI Backend."
}
