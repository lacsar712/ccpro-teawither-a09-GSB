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
4. **LeafProvenance（茶青溯源条）**：`garden`（所属茶园）、`batch`（关联批次，一对一）、`villageGroup`（鲜叶村组）、`pickedOn`（采摘日）、`registrar`（登记人）

**业务规则**：

- 将槽位状态设为 `ready`（可下槽）时，若最新批次的 `actualMoisture` 为空或大于 40，抛出中文 `ValidationError`。
- **园批一致性**：溯源条上「关联批次」所属槽位的茶园必须与条上「所属茶园」一致，否则拒绝保存（模型 `clean()` 校验，表单与种子数据同受此约束）。
- **采摘日约束**：`pickedOn` 不得晚于批次 `startedAt` 的东八区（Asia/Shanghai）日期。
- **一批次一条**：`batch` 为 `OneToOneField`，同一批次只允许存在一条溯源条。

**删除策略**：

- 删除茶园：若该园仍存在茶青溯源条，**拒绝删除**（视图提示 + 数据库层 `PROTECT` 双保险）；无溯源条时，其下槽位与批次级联删除。
- 删除批次：**级联删除**其茶青溯源条（`batch` 外键 `on_delete=CASCADE`），删除确认页已注明。二选一采用级联方案，实现与此说明一致。

**对账口径**：首页「各园溯源条数对照」按 `garden` 外键统计条数，与「茶青溯源」列表页按园过滤（`?garden=<id>`）后的行数完全相等；列表顶部同时显示当前过滤条件下的总条数。

## 种子数据

```bash
python manage.py seed_data
```

幂等：已有茶园则只保证账号存在。亦可在环境变量 `TEAWITHER_AUTO_SEED=1` 时于 `post_migrate` 自动播种。种子含两个茶园、四条批次及对应的四条茶青溯源条（两园各两条）。

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
