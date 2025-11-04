# RAG App — GitHub Actions 部署到 AWS App Runner

本项目使用 GitHub Actions 在推送到 `main` 分支时自动构建 Docker 镜像并部署到 AWS App Runner。

## 工作流概览（`.github/workflows/main.yml`）
- 触发条件：`push` 到 `main`。
- 核心步骤：
  - `Checkout` 代码。
  - 通过 GitHub OIDC 假设 IAM 角色（`aws-actions/configure-aws-credentials@v4`）。
  - 登录 Amazon ECR（`aws-actions/amazon-ecr-login@v2`）。
  - 构建并推送镜像到 ECR（镜像标签为提交 SHA 的前 7 位）。
  - 校验 `APP_RUNNER_ARN` 格式（避免把 URL/名称误当 ARN）。
  - 从现有服务查询 `access-role-arn` 与 `instance-role-arn`。
  - 使用 `awslabs/amazon-app-runner-deploy` 将 ECR 镜像部署到既有服务，并等待到稳定状态。

### 部署步骤关键配置（简化片段）
```yaml
- name: Deploy to App Runner
  uses: awslabs/amazon-app-runner-deploy@main
  with:
    service: bee-edu-rag-service
    image: ${{ steps.ecr-login.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ env.TAG }}
    region: ${{ env.AWS_REGION }}
    access-role-arn: ${{ env.APP_RUNNER_ACCESS_ROLE_ARN }}
    instance-role-arn: ${{ env.APP_RUNNER_INSTANCE_ROLE_ARN }}
    port: 8080
    cpu: 1
    memory: 2
    wait-for-service-stability-seconds: 600
```

## 必需的仓库 Secrets / 变量
- `AWS_REGION`：部署区域，例如 `us-east-1`。
- `ECR_REPOSITORY`：ECR 仓库名，例如 `bee-edu-rag-app`。
- `APP_RUNNER_ARN`：App Runner 服务 ARN（Terraform 输出的值）。
- `AWS_IAM_ROLE_TO_ASSUME`：GitHub OIDC 假设的 IAM 角色 ARN（例如 `github-actions-deploy-role`）。

> 说明：日志中对 Secrets 的显示会被 GitHub 脱敏为 `***`，但运行时值有效。

## 权限与最小权限建议
- GitHub Actions 角色需要允许对现有服务执行更新（如 `apprunner:UpdateService`）。
- 需要允许 `iam:PassRole` 传递以下角色到 App Runner：
  - `bee-edu-apprunner-instance-role`
  - `bee-edu-apprunner-role`
- 可选：后续稳定后可移除 `apprunner:CreateService`，并收紧 `iam:PassRole` 的 `iam:PassedToService` 条件到 `apprunner.amazonaws.com`。

## 常见问题速查
- 服务名校验失败：确保 `service` 设置为现有服务名（这里为 `bee-edu-rag-service`）；`APP_RUNNER_ARN` 必须是合法 ARN。
- CPU/内存校验失败：按 Action 的单位使用 `cpu: 1`（vCPU）与 `memory: 2`（GB）。
- `iam:PassRole` 被拒绝：确认 GitHub Actions 角色策略已允许对上述两角色执行 `iam:PassRole`。

## 版本固定（可选）
- 为稳定性建议固定 Action 版本，例如：
  - `uses: awslabs/amazon-app-runner-deploy@v2.5.2`

---
如需进一步定制（环境变量、标签、自动扩缩容等），可直接编辑 `/.github/workflows/main.yml` 的对应输入项。