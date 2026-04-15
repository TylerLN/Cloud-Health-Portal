// outputs terraform for s3 bucket, rds endpoint (for backend rds connection) and alb endpoint (for frontend)

output "s3_bucket_name" {
  value = aws_s3_bucket.bucket.id
}

output "rds_endpoint" {
  value = aws_db_instance.db.endpoint
}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}