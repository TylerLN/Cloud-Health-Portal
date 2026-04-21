// IAM Configuration for EC2

resource "aws_iam_role" "ec2_role" {
  name = "ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

// enable cloudwatch for Ec2
resource "aws_iam_role_policy_attachment" "cloudwatch_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# IAM policy to allow EC2 instances to access the S3 bucket
resource "aws_iam_policy" "s3_access_policy" {
  name        = "s3-access-policy"
  description = "Allow EC2 backend to securely access S3 bucket"

  // list buck lists files in uploads/ nothing else
  // object acecss only for uploaded files in upload folder
  // extra deny condition to prevent deletion
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ListBucket" 
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.file_transfers.arn 
        Condition = {
          StringLike = {
            "s3:prefix" = ["uploads/*"]
          }
        }
      },
      {
        Sid    = "ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.file_transfers.arn}/uploads/*"
      },
      {
        Sid    = "DenyDelete"
        Effect = "Deny"
        Action = [
          "s3:DeleteObject",
          "s3:DeleteBucket"
        ]
        Resource = [
          aws_s3_bucket.file_transfers.arn,
          "${aws_s3_bucket.file_transfers.arn}/*"
        ]
      }
    ]
  })
}

// Attach the S3 access policy to the EC2 role
resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

// Create an instance profile for the EC2 role
resource "aws_iam_instance_profile" "app_instance_profile" {
  name = "app-ec2-profile"
  role = aws_iam_role.ec2_role.name
}