// Setting Security Groups for traffic control

// Security Group for ALB (public subnet)
resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Allow HTTP traffic from internetto ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  // outbound traffoc allowed to anywhere
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "alb-sg"
  }
}

// Security Group for EC2 app servers (private subnet)
// set ingress to only allow traffic from alb
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Allow traffic from ALB to app servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "ec2-sg"
  }
}

// Security Group for RDS database (private subnet)
// set ingress to only allow traffic from app servers
resource "aws_security_group" "db_sg" {
  name        = "db-sg"
  description = "Allow traffic from app servers to RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    // Postgres default port, change if using diff db port
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "db-sg"
  }
}