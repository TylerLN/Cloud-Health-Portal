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