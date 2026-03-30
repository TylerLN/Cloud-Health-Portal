// S3 bucket for file transfers

resource "aws_s3_bucket" "file_transfers" {
  bucket = "file-transfers-bucket-cpsc-454"

  tags = {
    Name = "File Transfers Bucket"
  }
}

// Block public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "file_transfers" {
  bucket = aws_s3_bucket.file_transfers.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Enable versioning for the S3 bucket
resource "aws_s3_bucket_versioning" "file_transfers" {
  bucket = aws_s3_bucket.file_transfers.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Enable server-side encryption for the S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "file_transfers" {
  bucket = aws_s3_bucket.file_transfers.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

