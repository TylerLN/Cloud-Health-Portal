// RDS Database

// Create DB Subnet Group for RDS instance
// Need to specify which subnets RDS can use, must be private subnets for security
resource "aws_db_subnet_group" "db_subnet_group" {
  name = "db-subnet-group"
  subnet_ids = [
    aws_subnet.private_db_a.id,
    aws_subnet.private_db_b.id
  ]

  tags = {
    Name = "db-subnet-group"
  }
}

// RDS Instance Configs
resource "aws_db_instance" "app_db" {
  identifier        = "app-db"
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "appdb"
  username = var.rds_username
  password = var.rds_password
  port     = 5432

  vpc_security_group_ids = [aws_security_group.db_sg.id]            // who can access
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name // where db is (private subnet)

  publicly_accessible = false // make RDS private, only accessible from app servers in private subnet

  skip_final_snapshot = true
  
  tags = {
    Name = "app-rds"
  }
}


