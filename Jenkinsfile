// Jenkinsfile
pipeline {
    // 假设 Jenkins agent 上已安装 Docker 和 AWS CLI
    agent any 

    // 环境变量将从 Jenkins Job 配置中自动注入
    environment {
        // ECR_REPO_URL, APP_RUNNER_SERVICE_ARN, AWS_REGION 
        // 必须在 Jenkins Job 中配置!
    }

    stages {
        stage('Checkout') {
            steps {
                echo "1. Checking out code..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "2. Building Docker image..."
                    // 使用 Git Commit 的前 7 位作为唯一的镜像标签
                    env.IMAGE_TAG = env.GIT_COMMIT.substring(0, 7)
                    sh "docker build -t ${ECR_REPO_URL}:${env.IMAGE_TAG} ."
                }
            }
        }

        stage('Push to ECR') {
            steps {
                echo "3. Logging in to ECR and pushing image..."
                // 假设 Jenkins 实例 Role 已有 ECR 权限
                sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URL}"
                sh "docker push ${ECR_REPO_URL}:${env.IMAGE_TAG}"
            }
        }

        stage('Deploy to App Runner') {
            steps {
                echo "4. Updating App Runner service..."
                // 更新 App Runner 服务，使其指向新的镜像 Tag
                sh """
                aws apprunner update-service \
                    --region ${AWS_REGION} \
                    --service-arn ${APP_RUNNER_SERVICE_ARN} \
                    --source-configuration '{"imageRepository": {"imageIdentifier": "${ECR_REPO_URL}:${env.IMAGE_TAG}"}}'
                """
                echo "✅ Deployment triggered!"
            }
        }
    }
}