AWS deployment pipeline setup (GitHub Actions -> ECR -> EC2)

Files added:
- .github/workflows/aws-deploy.yml
- .github/workflows/aws-infra-bootstrap.yml
- .github/workflows/aws-infra-init.yml
- backend/Dockerfile
- frontend/Dockerfile
- deploy/docker-compose.aws.yml
- deploy/ec2-deploy.sh

GitHub repository variables (Settings -> Secrets and variables -> Actions -> Variables):
- AWS_REGION: your region (example: ap-south-1)
- ECR_REPOSITORY_BACKEND: applydf-backend
- ECR_REPOSITORY_FRONTEND: applydf-frontend

GitHub repository secrets (Settings -> Secrets and variables -> Actions -> Secrets):
- AWS_ROLE_TO_ASSUME (IAM Role ARN for GitHub OIDC)
- EC2_HOST (public IP or DNS)
- EC2_USER (example: ubuntu or ec2-user)
- EC2_SSH_PRIVATE_KEY (private key text for EC2 SSH)

Optional one-time bootstrap secrets (only for AWS Infra Init workflow):
- AWS_BOOTSTRAP_ACCESS_KEY_ID
- AWS_BOOTSTRAP_SECRET_ACCESS_KEY

OIDC setup (recommended, no static AWS keys in GitHub):
1. Create an IAM OIDC provider for token.actions.githubusercontent.com (if not already created).
2. Create IAM role and store its ARN in secret AWS_ROLE_TO_ASSUME.
   The role trust policy must allow your GitHub repo/branch to assume it via OIDC.
3. Attach ECR permissions listed below to this role.

Automated alternative:
1. Run workflow `AWS Infra Init (One-Time)`.
2. It can create OIDC provider, IAM role, and ECR repositories automatically.
3. Copy the output values from workflow summary into GitHub Variables.
4. Put role ARN into secret AWS_ROLE_TO_ASSUME.
5. Remove bootstrap secrets after first successful run.

AWS IAM permissions needed for OIDC role used in workflow:
- ecr:GetAuthorizationToken
- ecr:BatchCheckLayerAvailability
- ecr:CompleteLayerUpload
- ecr:UploadLayerPart
- ecr:InitiateLayerUpload
- ecr:PutImage
- ecr:DescribeRepositories
- ecr:CreateRepository

EC2 one-time setup:
1. Install Docker and Docker Compose plugin.
2. Install AWS CLI.
3. Attach an IAM role to EC2 with ECR read permissions:
   - ecr:GetAuthorizationToken
   - ecr:BatchGetImage
   - ecr:GetDownloadUrlForLayer
4. Open inbound security group ports:
   - 8501 for Streamlit UI
   - 8000 for backend API (optional; can keep private)
5. Ensure /opt/applydf is writable by your deploy user.

How deployment works:
1. Push to main branch.
2. GitHub Actions builds backend and frontend Docker images.
3. Images are pushed to ECR using commit SHA tags.
4. Workflow copies deploy files to EC2 and runs deploy/ec2-deploy.sh.
5. EC2 pulls fresh images and restarts services with Docker Compose.

Infra bootstrap workflow:
1. Run workflow `AWS Infra Bootstrap` once from GitHub Actions.
2. It validates variables and creates ECR repositories if missing.
3. Then use `AWS Deploy ApplyDF` for regular deployments.

Access after deploy:
- Frontend: http://<EC2_HOST>:8501
- Backend: http://<EC2_HOST>:8000

Notes:
- Frontend container uses API_BASE_URL=http://backend:8000 inside Docker network.
- In frontend code, API base URL is now environment-driven with localhost fallback.
