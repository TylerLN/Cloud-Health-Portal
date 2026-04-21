# Health Portal - Cloud Security Application

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

- AWS account with credentials configured
- Terraform installed on computer

#### 1. Clone Repository

Github personal access token required to clone private repository.
Github -> Settings -> Developer Settings -> Personal Access Token -> Generate new token (Classic) -> Select "repo" scope -> Copy token

```bash
git clone -b appointments https://<replace-with-github-token>@github.com/454-Project-Group/Backend
```

Note: requirements.txt and backend & frontend installations/configurations are done automatically in EC2.tf file.

#### 2. Create terraform/terraform.tfvars (cloud deployment)

Use Example files and fill with own values

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

#### 3. Deploy terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Type 'yes' during deployment process.
After sucessful creation, wait 5-10 minutes for EC2 instances to finish checks and target groups healthy, then load the
alb_dns_name from Terraform output.

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
