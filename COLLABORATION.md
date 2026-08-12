# 四人协作 SOP

## 1. 加入仓库

组长：进入 GitHub 仓库 → **Settings** → **Collaborators** → **Add people**，邀请三位组员的 GitHub 用户名，并给予 **Write** 权限。

组员：接受 GitHub 邀请后，执行：

```bash
git clone https://github.com/123bingowinnn/death-education-hackathon.git
cd death-education-hackathon
```

## 2. 领取任务

在 GitHub 的 **Issues** 中新建或领取任务。一个任务由一个人负责；任务写清楚目标、交付物和截止时间。

建议分工：产品/内容、前端、后端/数据、整合与演示。

## 3. 每次开发

先同步主分支，再创建分支：

```bash
git switch main
git pull origin main
git switch -c feature/简短功能名
```

开发完成后提交并推送：

```bash
git add .
git commit -m "feat: 简短说明"
git push -u origin feature/简短功能名
```

然后在 GitHub 点击 **Compare & pull request**，说明：做了什么、如何验证、是否有待解决问题。

## 4. 合并规则

- 不直接把未确认的改动推到 `main`。
- 至少请一位队友快速查看 PR；紧急情况下在群里确认后合并。
- 合并前处理冲突并确认项目可运行。
- 合并后删除远程功能分支。

## 5. 黑客松节奏

- 每天开始：同步 `main`，确认自己负责的 Issue。
- 每完成一小块：推送一次，避免改动只留在本机。
- 每天结束：在群里同步进度、阻塞点和明天计划。
- 演示前：冻结新功能，只修关键问题；从 `main` 统一打包和演示。

## 6. 发生冲突或误操作

- 先不要强制推送（`git push --force`）。
- 把报错或冲突截图发给组长/负责整合的同学，一起处理。
- 如果误删内容，优先从 Git 提交记录或 PR 中恢复。
