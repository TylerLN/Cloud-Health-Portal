// EC2 instance configuration for app servers

resource "aws_instance" "app_server" {
  count                       = 2
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.private_app.id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.app_instance_profile.name
  user_data_replace_on_change = true

  root_block_device {
    encrypted = true
  }

  // Install and configure CloudWatch agent on EC2 instances to monitor memory, disk, and logs
  // also run the uvicorn python by clonign our repository and running it automattically within ec2
  user_data = <<-EOF
              #!/bin/bash
              set -eux

              apt-get update -y

              wget https://amazoncloudwatch-agent.s3.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
              dpkg -i -E ./amazon-cloudwatch-agent.deb

              cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'CWCONFIG'
              {
                "agent": {
                  "metrics_collection_interval": 60,
                  "run_as_user": "root"
                },
                "metrics": {
                  "metrics_collected": {
                    "mem": {
                      "measurement": ["mem_used_percent"]
                    },
                    "disk": {
                      "measurement": ["used_percent"],
                      "resources": ["*"]
                    }
                  }
                },
                "logs": {
                  "logs_collected": {
                    "files": {
                      "collect_list": [
                        {
                          "file_path": "/var/log/syslog",
                          "log_group_name": "health-portal-syslog",
                          "log_stream_name": "{instance_id}"
                        },
                        {
                          "file_path": "/var/log/auth.log",
                          "log_group_name": "health-portal-authlog",
                          "log_stream_name": "{instance_id}"
                        }
                      ]
                    }
                  }
                }
              }
              CWCONFIG

              /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
                -a fetch-config \
                -m ec2 \
                -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
                -s

              apt-get install -y python3 python3-pip git nginx

              git clone -b appointments https://${var.github_token}@github.com/454-Project-Group/Backend /app

              pip3 install -r /app/requirements.txt
              
              chmod -R 755 /app 
              chown -R www-data:www-data /app

              cat > /app/src/.env <<ENVFILE
              DB_HOST=${aws_db_instance.app_db.address}
              DB_PORT=5432
              DB_USER=${var.rds_username}
              DB_PASSWORD=${var.rds_password}
              SECRET_KEY=${var.secret_key}
              ENVFILE

              cat > /etc/nginx/sites-available/default <<'NGINXCONFIG'
              server {
                listen 80;

                root /app/src/templates;
                index login.html;

                location /api/ {
                  proxy_pass http://127.0.0.1:8000;
                  proxy_set_header Host $host;
                  proxy_set_header X-Real-IP $remote_addr;
                }

                location /static/ {
                  alias /app/src/static/;
                }

                location / {
                  try_files $uri $uri/ /login.html;
                }
              }
              NGINXCONFIG

              nginx -t && systemctl restart nginx


              cd /app
              nohup uvicorn src.app:app --host 127.0.0.1 --port 8000 &

              EOF


  tags = {
    Name = "app-server"
  }

}

// AMI lookup since AMI IDs can change across regions and over time. This will get the latest Ubuntu 20.04 LTS image.
data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}