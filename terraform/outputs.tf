// outputs terraform for s3 bucket, rds endpoint (for backend rds connection) and alb endpoint (for frontend)

output "s3_bucket_name" {
  value = aws_s3_bucket.file_transfers.id
}

output "rds_endpoint" {
  value = aws_db_instance.app_db.endpoint
}

output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}