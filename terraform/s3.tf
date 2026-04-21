// S3 bucket for file transfers

resource "aws_s3_bucket" "file_transfers" {
  bucket = "files-transfers-bucket-cpsc-454"

  tags = {
    Name = "File Transfers Bucket"
  }
}

// Block public access to the S3 bucket at bucket level
resource "aws_s3_bucket_public_access_block" "block_public_acls" {
  bucket = aws_s3_bucket.file_transfers.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Block public access to the S3 bucket at account level
resource "aws_s3_account_public_access_block" "account_block_public_acls" {
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

// Commented out since ALB accepts http traffic but should be enabled for compliance
// Certificate Manager for ALB https listerer requires domain but that costs money, so sticking with http
/*
// enable https only access to the S3 bucket
resource "aws_s3_bucket_policy" "https_only" {
  bucket = aws_s3_bucket.file_transfers.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceHTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [
          "${aws_s3_bucket.file_transfers.arn}/*",
        ],
        // if the request is not using HTTPS, deny access to the bucket
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
*/
