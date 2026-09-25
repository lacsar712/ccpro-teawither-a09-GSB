# TeaWither-01 · 茶萎凋台账

Django 5 + PostgreSQL 服务端渲染应用：Templates + HTMX + 自定义 CSS，无 Vue/React SPA。

## 技术栈

- Django 5、PostgreSQL
- Session 登录
- HTMX（CDN）局部刷新列表
- Docker Compose：`web` + `db`

## 端口与数据库

| 服务 | 端口 |
|------|------|
| Web  | **4100** |
| Postgres | **5440**（容器内 5432） |

数据库账号：`teawither` / `teawither` / 库名 `teawither`

## 快速启动

```bash
cd TeaWither/TeaWither-01
docker compose up --build -d
```

浏览器打开：http://localhost:4100

演示账号：

- `admin` / `123456`（超级用户）
- `witherer` / `123456`（普通用户）

容器启动时会自动：`migrate` → `seed_data` → `collectstatic` → `gunicorn`

## 本地开发（可选）

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 确保本机 Postgres 监听 5440，或先 docker compose up -d db
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5440
python manage.py migrate
python manage.py seed_data
python manage.py runserver 0.0.0.0:4100
```

## 业务模型

1. **Garden（茶园）**：`name`、`altitudeBand`、`notes`
2. **Trough（萎凋槽）**：归属茶园、`troughCode`、`cultivar`、`loadKg`、状态 `loading|withering|ready`；同一茶园内槽位编号唯一
3. **WitherBatch（萎凋批次）**：归属槽位、`startedAt`、`targetMoisture`、`actualMoisture`（可空）、`rollGrade`
4. **LeafProvenance（茶青溯源条）**：所属茶园、关联批次、`villageGroup`（鲜叶村组）、`pickingDate`（采摘日）、`registrar`（登记人）

**业务规则**：

- 将槽位状态设为 `ready`（可下槽）时，若最新批次的 `actualMoisture` 为空或大于 40，抛出中文 `ValidationError`。
- **园批一致性**：溯源条上的「所属茶园」必须等于关联批次所属槽位的茶园，否则表单与模型层均以 `ValidationError` 拒绝（模型 `save()` 内强制 `full_clean()`）。
- **一批一条**：同一批次仅允许一条溯源条（`batch` 为 `OneToOneField`，数据库唯一约束）。
- **采摘日口径**：`pickingDate` 不得晚于批次 `startedAt` 的东八区（Asia/Shanghai）日期。
- **删除策略**：
  - 删茶园：若该园仍有溯源条则**拒绝删除**（`garden` 外键 `PROTECT`，删除视图同步拦截并提示）。
  - 删批次：**级联删除**其溯源条（`batch` 一对一 `CASCADE`）；删槽位随之级联批次与溯源条。
- **对账**：首页「各园茶青溯源条数对照」与「茶青溯源」列表按园过滤后的行数同一口径（均按 `garden` 归属统计），两者完全相等。

## 种子数据

```bash
python manage.py seed_data
```

幂等：已有茶园则只保证账号存在；溯源条单独幂等（已有溯源条则跳过）。种子覆盖两个茶园、多条溯源条（每批次一条，园批一致）。亦可在环境变量 `TEAWITHER_AUTO_SEED=1` 时于 `post_migrate` 自动播种。

## 目录结构

```
TeaWither-01/
  manage.py
  requirements.txt
  Dockerfile
  entrypoint.sh
  docker-compose.yml
  config/           # 项目配置
  apps/gardens/     # 模型、视图、种子命令
  templates/        # Django 模板
  static/css/       # 自定义样式（茶绿色顶栏）
```
