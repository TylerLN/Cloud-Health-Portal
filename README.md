# Health Portal - Cloud Security Application

## Link to Github Repository

https://github.com/TylerLN/Cloud-Health-Portal

## Description

The health portal is a cloud-based medical health portal that allows doctors and patients to manage appointments and securely transfer files. The backend is built with Python (Falcon), PostgreSQL, and deployed on AWS through Infrastructure as Code (IAC through Terraform)

The project applies the following key concepts:

- Network Segmentation (VPC and subnets)
- Identity and Access Managment (IAM roles, RBAC)
- Infrastructure as Code (Terraform)
- Compliance Checks and Remediation (NIST SP 800-53 and HIPAA)

## Implementation

- **Backend:** Python, Falcon (async), uvicorn
- **Database:** PostgreSQL (local deployment), AWS RDS (cloud deployment)
- **Frontend:** HTML, CSS, JavaScript
- **Cloud Infrastructure:** AWS Services (EC2, ALB, RDS, S3, CloudWatch, WAF), Terraform (Automation)
- **Authentication:** PASETO tokens (bearer token authentication)

## Cloud Deployment Installation Steps (Ubuntu/Linux)

### Installation Prerequisites

- AWS account with credentials configured. Steps include:
  - Install aws configure: sudo apt install awscli
  - Configure: aws configure
  - Create access key ID and Secret Access Key
    - AWS console -> IAM -> Users -> Create user (adminaccess) -> security tab -> create access key (CLI) -> copy access key ID and secret access key
  - Default region: us-west-2,
  - Output: json
  - Verify: Run aws sts get-caller-identity in command line

- Install Terraform

#### 1. Clone Repository

```bash
git clone https://github.com/TylerLN/Cloud-Health-Portal
cd Cloud-Health-Portal
```

Note: requirements.txt and backend & frontend installations/configurations are done automatically in EC2.tf file, so tester only needs to set up terraform cloud environment. The repo_url in terraform.tfvars is the github repository link.

#### 2. Create terraform/terraform.tfvars (cloud deployment)

Use Example files and fill with own values

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

Note: If user wants to do local development/testing, please read test_steps.txt file provided.

#### 3. Deploy terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Type 'yes' during deployment process.
After sucessful creation, wait 5-10 minutes for EC2 instances to finish checks and target groups healthy, then copy the
alb_dns_name link from Terraform output and paste into internet search bar.

#### 4. Application Use:

Register with white list logins (doctor first, then patient). Follow password requirements on register page and remember for future log in.

- `doctor1@hospital.com` - role: `doctor`
- `patient1@hospital.com` - role: `patient`
- `patient2@hospital.com` - role: `patient`
- `patient3@hospital.com` - role: `patient`

Test features on application

#### 5. When finished, destroy aws services

Check if uploads/ folder is empty on AWS console

```bash
terraform destroy
```

Confirm resources are terminated on AWS console to avoid charges.

## Disclaimer:

This is a demo application for educational purposes only. It does not store or transmit any real medical data and should not be used in a real medical setting.
