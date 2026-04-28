// variables.tf for RDS instance so we dontt hardcode sensitive info in rds.tf
// get password from terraform.tfvars
variable "rds_password" {
  description = "The password for the RDS instance."
  type        = string
  sensitive   = true
}

variable "rds_username" {
  description = "The username for the RDS instance."
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "secret key for PASETO token"
  type        = string
  sensitive   = true
}

// this is for the url to clone repo in user_data (in ec2.tf), based on the user that cloned it
variable "repo_url" {
  description = "GitHub repository URL for the application code."
  type        = string
}