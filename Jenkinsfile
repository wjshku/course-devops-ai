// Jenkinsfile
pipeline {
    // 假设 Jenkins agent 上已安装 Docker 和 AWS CLI
    agent any 

    // 通过参数与环境变量结合的方式，避免空 environment 导致编译错误
    parameters {
        string(name: 'ECR_REPO_URL', defaultValue: '', description: 'ECR 仓库完整地址，例如 531...amazonaws.com/bee-edu-rag-app')
        string(name: 'APP_RUNNER_SERVICE_ARN', defaultValue: '', description: 'App Runner 服务 ARN')
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS 区域')
        string(name: 'HTTP_PROXY', defaultValue: '', description: '可选：HTTP 代理，如 http://127.0.0.1:7890')
        string(name: 'HTTPS_PROXY', defaultValue: '', description: '可选：HTTPS 代理，如 http://127.0.0.1:7890')
        string(name: 'ALL_PROXY', defaultValue: '', description: '可选：SOCKS 代理，如 socks5://127.0.0.1:7890')
    }

    environment {
        // 从参数传递到环境，若 Jenkins Job 直接设置环境变量也会覆盖这里
        ECR_REPO_URL           = "${params.ECR_REPO_URL}"
        APP_RUNNER_SERVICE_ARN = "${params.APP_RUNNER_SERVICE_ARN}"
        AWS_REGION             = "${params.AWS_REGION}"
        // 扩展 PATH 以找到 docker（Homebrew 与 Docker Desktop 常见路径）
        PATH                  = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Applications/Docker.app/Contents/Resources/bin:${PATH}"
        // 代理（同时设置大小写，兼容不同工具）
        HTTP_PROXY  = "${params.HTTP_PROXY}"
        HTTPS_PROXY = "${params.HTTPS_PROXY}"
        ALL_PROXY   = "${params.ALL_PROXY}"
        http_proxy  = "${params.HTTP_PROXY}"
        https_proxy = "${params.HTTPS_PROXY}"
        all_proxy   = "${params.ALL_PROXY}"
    }

    stages {
        stage('Validate Env') {
            steps {
                script {
                    def missing = []
                    if (!env.ECR_REPO_URL?.trim()) missing << 'ECR_REPO_URL'
                    if (!env.APP_RUNNER_SERVICE_ARN?.trim()) missing << 'APP_RUNNER_SERVICE_ARN'
                    if (!env.AWS_REGION?.trim()) missing << 'AWS_REGION'
                    if (missing) {
                        error "缺少必要的环境变量: ${missing.join(', ')}。请在 Jenkins Job 参数或环境中配置。"
                    }
                }
            }
        }

        stage('Preflight Docker') {
            steps {
                sh '''
                  echo "PATH=$PATH"
                  echo "Checking docker locations..."
                  command -v docker || true
                  ls -l /usr/local/bin/docker || true
                  ls -l /opt/homebrew/bin/docker || true
                  ls -l /Applications/Docker.app/Contents/Resources/bin/docker || true
                  echo "Docker version:" 
                  docker version || { echo "ERROR: Docker CLI not found or daemon unavailable"; exit 1; }
                  echo "Docker buildx version:"
                  docker buildx version || echo "WARN: buildx plugin not found"
                '''
            }
        }
        stage('Checkout') {
            steps {
                echo "1. Checking out code..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "2. Building Docker image (linux/amd64)..."
                    // 使用 Git Commit 的前 7 位作为唯一的镜像标签
                    env.IMAGE_TAG = env.GIT_COMMIT.substring(0, 7)
                    sh '''
                      docker buildx create --use || true
                      docker buildx version || true
                      docker buildx build --platform linux/amd64 -t ${ECR_REPO_URL}:${IMAGE_TAG} . --load
                    '''
                    // 额外：对齐 Terraform 初始部署，推送 latest 标签
                    sh "docker tag ${ECR_REPO_URL}:${env.IMAGE_TAG} ${ECR_REPO_URL}:latest"
                }
            }
        }

        stage('Push to ECR') {
            steps {
                echo "3. Logging in to ECR and pushing image..."
                // 假设 Jenkins 实例 Role 已有 ECR 权限
                sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URL}"
                sh "docker push ${ECR_REPO_URL}:${env.IMAGE_TAG}"
                sh "docker push ${ECR_REPO_URL}:latest"
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
                    --source-configuration '{"ImageRepository": {"ImageIdentifier": "${ECR_REPO_URL}:${env.IMAGE_TAG}", "ImageRepositoryType": "ECR", "ImageConfiguration": {"Port": "8080"}}}'
                """
                echo "✅ Deployment triggered!"
            }
        }
    }
}