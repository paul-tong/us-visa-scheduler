# 武汉美国访客签证预约助手

[English](README.md)

本项目在本地 Windows 桌面运行，通过美国签证预约网站监控武汉 B1/B2 或 B2
面谈日期，可选择对**已有预约进行至多一次受保护的改期提交**。
默认仅监控，必须明确开启自动改期。

仅在服务提供方允许的情况下使用自动化。本工具不保证通过人机验证、不受账号限制、
持续可访问或成功预约，也不是通用抢号服务。

## 功能

- 自动填写账号密码，并按实际显示的问题匹配本地密保答案。
- 有次数限制的 GUI 人机验证辅助；必要时通过邮件通知手动验证。
- 通过网站正常界面观察响应返回的全部日期，而非仅屏幕上显示的月份。
- 按优先级匹配包含端点的日期区间；不偏好的日期只记录、不选择。
- 仅监控模式绝不选择日期、时段或提交。
- 校验已有预约、申请人、签证类别和武汉领馆；首页只使用经过验证的改期链接。
- 登录后点击延迟、随机观察暂停和有上限的恢复机制。
- 持久化单次提交保护、90 秒结果观察、本地按日日志和 SMTP 通知。

不支持首次新预约、其他领馆、OFC/生物信息预约、取消或重建申请。
客户端不调用取消操作，但不能保证服务端保留旧预约的原子性或如何扣减改期次数。

## 环境要求

- Windows、可交互桌面和已安装的 Google Chrome。
- PowerShell 7 或 Windows PowerShell 5.1。
- `PATH` 中可用的 Python，包含 `venv`、`pip`，并兼容 `requirements.txt`。
  锁定依赖最初在 Python 3.9.13 上验证，并非所有更新的 Python/Chrome 组合都经过测试。
- 已有武汉访客签证预约，以及可用的 SMTP 发信账号。
- 安装依赖、首次获取 ChromeDriver、发送邮件及访问网站所需的网络连接。

启动脚本不会安装 Python/Chrome、修改脚本执行策略或请求管理员权限。
请遵循本机执行策略。依赖由 `requirements.txt` 锁定，脚本不会使用 `--upgrade`。

## 快速开始

### 1. 创建私有启动脚本

在项目根目录打开 PowerShell，替换下面的示例路径：

```powershell
Set-Location 'C:\path\to\us-visa-scheduler'
New-Item -ItemType Directory -Force .\personal | Out-Null
if (-not (Test-Path .\personal\Set-VisaEnvironment.local.ps1)) {
    Copy-Item .\Set-VisaEnvironment.template.ps1 .\personal\Set-VisaEnvironment.local.ps1
}
notepad .\personal\Set-VisaEnvironment.local.ps1
```

编辑 **CUSTOMIZATION** 区域，填写账号密码、准确密保问题及答案、申请人、
已有预约、偏好日期和通知设置。替换所有占位内容及过期日期。
初始建议保持 `VISA_AUTO_BOOKING = 'false'`。

凭据直接填写为字符串，不会弹出密码或密保答案输入框。
PowerShell 单引号字符串内的单引号需重复，例如 `'example''s answer'`。
支持中文问题和答案；请使用当前 PowerShell 支持的文件编码。
若还使用 Windows PowerShell 5.1，包含中文的脚本应保存为带 BOM 的 UTF-8。

私有脚本包含明文秘密。`personal/` 和 `Set-VisaEnvironment.local.ps1`
已被 git 忽略，但并未加密。请保护文件访问权限，不要把真实凭据提交到模板中。

### 2. 运行启动脚本

在**项目根目录**运行，不要切换到 `personal`：

```powershell
pwsh -File .\personal\Set-VisaEnvironment.local.ps1
```

Windows PowerShell 用户可执行：

```powershell
powershell.exe -File .\personal\Set-VisaEnvironment.local.ps1
```

启动脚本依次：

1. 显示根目录提示，校验当前工作目录。
2. `.venv` 不存在时创建；已存在时复用其 Python。
3. 使用该 Python 执行 `pip install -r requirements.txt` 和 `pip check`。
4. 将自定义值写入当前进程环境，不输出秘密。
5. 显示菜单，执行一次所选模式。

| 选择 | Python 命令 | 效果 |
|---|---|---|
| `1` 或直接 Enter | `main.py --check-config` | 离线校验配置，不发邮件、不打开浏览器、不创建应用状态。 |
| `2` | `main.py --test-email` | 发送一封明确请求的测试邮件，不访问签证网站。 |
| `3` | `main.py` | 启动监控；若已开启自动改期，则允许受保护的单次提交。 |

输入数字后按 Enter。非法选项会重新询问；默认离线校验，不会默认启动预约。
**安装阶段在菜单之前执行，即使选择 1，也可能访问软件包网络服务。**
安装或依赖检查失败时，不进入菜单或启动监控。损坏的已有 `.venv` 会明确报错，
不会自动删除重建。应用退出码原样返回，不自动重试失败运行。

Python 由已配置的 PowerShell 进程直接启动，因此 `pwsh -File ...`
无需把变量传回父终端。此工作流不需要额外激活虚拟环境、执行安装命令或手动启动 Python。

已有私有副本不会自动升级。升级时将自定义区域合并到当前模板的新副本，
不要覆盖凭据，也不要假定旧的仅配置脚本已经包含新菜单。

## 配置参考

启动脚本按自定义区域显式设置全部 25 个变量，覆盖其进程中继承的同名值。
Python 优先读取环境变量；只有变量不存在时才采用 `main.py` 开头的默认值。
已存在但为空或格式不合法的结构化值会报错，不会悄悄回退。Python 启动时读取配置。

### 账号、预约和邮件

| 属性 | 环境变量 | 格式 / 默认值 |
|---|---|---|
| `USERNAME` | `VISA_USERNAME` | 签证账号；Python 默认值为空。 |
| `PASSWORD` | `VISA_PASSWORD` | 签证密码；默认为空。 |
| `SECURITY_ANSWERS` | `VISA_SECURITY_ANSWERS` | JSON 问题到答案对象；默认空映射。模板自动将 PowerShell 映射转换为 JSON。 |
| `EXPECTED_APPLICANTS` | `VISA_APPLICANTS` | 用 `;` 分隔准确姓名；默认为空。 |
| `EXPECTED_VISA_CLASS` | `VISA_VISA_CLASS` | 首页实际显示的 `B1/B2` 或 `B2`；默认 `B1/B2`。 |
| `EXPECTED_EXISTING_APPOINTMENT` | `VISA_EXISTING_APPOINTMENT` | 已有预约的北京时间 ISO 字符串，例如 `2030-01-15T10:00:00`；默认为空。 |
| `PREFERRED_DATE_RANGES` | `VISA_PREFERRED_DATE_RANGES` | JSON `[起始日期,结束日期]` 数组的数组，最高优先级在前；须替换示例范围。 |
| `AUTO_BOOKING` | `VISA_AUTO_BOOKING` | `true`/`false` 或 `1`/`0`，不区分大小写；默认 `False`。 |
| `DAILY_EMAIL_TIMES` | `VISA_DAILY_EMAIL_TIMES` | 三个不重复的北京时间 HH:MM；默认 `["08:00","12:00","17:00"]`。 |
| `SMTP_HOST` | `VISA_SMTP_HOST` | SMTP 主机；默认 `smtp.gmail.com`。 |
| `SMTP_PORT` | `VISA_SMTP_PORT` | 隐式 TLS 端口；默认 `465`。 |
| `SMTP_USERNAME` | `VISA_EMAIL_SENDER` | 发件人完整邮箱地址；默认为空。 |
| `SMTP_PASSWORD` | `VISA_SMTP_PASSWORD` | SMTP 应用专用密码；默认为空。 |
| `EMAIL_TO` | `VISA_EMAIL_TO` | 收件人邮箱地址；默认为空。 |

密保问题必须匹配页面实际文本。环境中的 JSON 对象整体替换默认映射，不做合并；
重复键、未知问题或不合法结构会安全失败。
日期选择先找第一个有可用日期的偏好区间，再取该区间中最早日期。
区间包含端点，区间之间的空隙仍被排除。已有预约时间用于安全校验，不是目标日期。

Gmail 使用 `smtp.gmail.com:465`、完整 Gmail 地址和 Google 应用专用密码，
不能使用普通账号密码。应用密码是否可用取决于账号策略和两步验证设置。
本工具实现隐式 TLS、密码式 SMTP，不支持 STARTTLS/587 或 OAuth。
SMTP 接受邮件不等于保证进入收件箱。

官方参考：
`https://developers.google.com/workspace/gmail/imap/imap-smtp`
和 `https://support.google.com/accounts/answer/185833`。

### 运行预算

以下都是本地限制，不是网站公布配额或安全频率保证。数值必须为整数；
超时、冷却、观察次数和轮询上下限必须为正数；点击延迟及辅助调用上限允许零；
恢复重试次数为 0–3。

| 属性 | 环境变量 | 默认值 | 含义 |
|---|---|---:|---|
| `CLICK_WAIT_SECONDS` | `VISA_CLICK_WAIT_SECONDS` | 5 | 登录后每次受控界面操作前的等待；零关闭延迟。 |
| `POLL_SECONDS_MIN` | `VISA_POLL_SECONDS_MIN` | 1800 | 完成一轮观察后的随机暂停下限，包含端点。 |
| `POLL_SECONDS_MAX` | `VISA_POLL_SECONDS_MAX` | 3600 | 包含端点的暂停上限，不小于下限；相同上下限产生固定暂停。 |
| `BLOCK_COOLDOWN_SECONDS` | `VISA_BLOCK_COOLDOWN_SECONDS` | 86400 | 限制后的默认冷却；采用更长的已观察 `Retry-After`，跨重启持久化。 |
| `MAX_RECOVERY_RETRIES` | `VISA_MAX_RECOVERY_RETRIES` | 3 | 初次限制后额外恢复次数，按任务持久化；绝不重试提交。 |
| `MAX_CHECKS_PER_RUN` | `VISA_MAX_CHECKS_PER_RUN` | 24 | 当前持久化任务的成功观察次数；尽管名称含 per-run，重启不会清零。 |
| `AUTO_VERIFICATION` | `VISA_AUTO_VERIFICATION` | `True` | 只控制 GUI 验证辅助；关闭时账号/答案仍自动填写，挑战转手动。 |
| `MAX_AUTO_VERIFICATIONS` | `VISA_MAX_AUTO_VERIFICATIONS` | 1 | 当前进程跨挑战的辅助调用上限；零关闭自动尝试，每次挑战最多调用一次后转手动。 |
| `MANUAL_VERIFICATION_TIMEOUT_SECONDS` | `VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS` | 900 | 手动验证期限，在通知发送前开始计时。 |
| `PAGE_TIMEOUT_SECONDS` | `VISA_PAGE_TIMEOUT_SECONDS` | 45 | 普通页面/响应等待；进程超时额外预留点击延迟和命令开销。 |
| `QUEUE_TIMEOUT_SECONDS` | `VISA_QUEUE_TIMEOUT_SECONDS` | 1800 | 每次网站排队的等待上限，不强制刷新。 |

点击延迟只有在已登录首页通过校验后才启用，覆盖改期链接、领馆/日历下拉框、
偏好日期、时段和提交。每次等待后重新检查上下文和控件。
登录、密保、人机验证和只读结果检查不受此延迟影响。

每轮继续观察前重新随机抽取整数暂停时间。实际间隔还包含处理耗时，
因此 `300–600` 秒不保证十分钟内再次观察。更快轮询、更大观察预算或更多辅助调用
都会增加活动量，不能用于绕过限制。冷却、验证期限和 90 秒结果窗口不会随机化。

辅助上限计算调用次数，包括拒绝执行或不安全的调用，不等于内部点击或请求数。
设置 10 不表示对同一个复选框连续尝试十次。未解决的挑战进入邮件通知的手动流程；
自动交互后另有最多 60 秒的结果观察。一旦可能已经提交，禁止再进行验证。
工具还持久化限制每个北京时间自然日最多提交两次账号密码，与网站实际限额无关。

## 流程和安全保护

```text
启动脚本：校验目录 -> 创建/复用环境 -> 安装/检查 -> 配置 -> 选择模式
监控程序：校验 -> 单实例锁与持久状态 -> 邮件预检查 -> 登录
  -> 自动验证/手动交接 -> 密保 -> 校验首页
  -> 仅改期链接 -> 校验申请人与已有预约 -> 观察日期
  -> 无匹配/仅监控：记录、通知、等待并在预算内继续
  -> 偏好日期：首个可用时段 -> 再次校验 -> 持久化提交标记
  -> 提交一次 -> 观察 90 秒 -> 报告结果 -> 关闭浏览器并停止
```

首个可用时段必须有足够容纳全部申请人的容量；名额消失时不提交。
SUCCESS 需要网站 `AllScheduled` 响应与请求的日期/时段匹配；
明确拒绝为 FAILURE；缺失或冲突的证据为 UNKNOWN。仅跳转或标题变化不能证明成功。

完整结果窗口从 Submit 命令返回或抛出异常后开始，避免点击前等待缩短观察期。
一旦可能已发送提交，禁止自动验证、刷新、重新登录或再次提交。
中断可能缩短观察，但持久化标记仍阻止重复尝试。

浏览器使用北京时间；GUI 验证时需保持可见。收到手动验证通知后，只完成当前窗口
的人机验证，不要自行选日期或提交。检测到预期下一页后继续；工作进程挂起或丢失则停止。
工具拥有的浏览器进程被隔离，不按进程名称终止其他 Chrome 窗口。

## 日志、通知与恢复

路径均相对于项目根目录：

| 路径 | 内容 |
|---|---|
| `logs\EventLog_YYYY_MM_DD.jsonl` | 操作、错误、重试、`POLL_WAIT` 和 `CLICK_WAIT`。 |
| `logs\AvailabilityLog_YYYY_MM_DD.jsonl` | 全部返回日期、偏好标记及优先级。 |
| `logs\BookingLog_YYYY_MM_DD.jsonl` | 尝试的北京时间和结果。 |
| `.state\state.json` | 停止/重试/观察计数、冷却、日期快照及邮件发件箱。 |
| `.state\submission.json` | 独占创建的永久提交保护标记。 |

日志包含固定 PST（UTC-08:00）、UTC、北京时间。
心跳按北京时间日期切换文件；同一天重启使用新后缀，不覆盖旧内容。
日志、状态和浏览器资料应按个人信息保护。

通知包括偏好日期、改期结果、手动验证、限制/异常，以及每天三次北京时间摘要。
每轮命中偏好日期都可能再次通知。每日摘要使用已有快照及其数据年龄，不强制查询。
通知随任务停止而结束。

邮件重试有上限，未发送记录持久化。仅重发未发送邮件时，先用 `-ConfigureOnly`
加载配置，再执行：

```powershell
.\.venv\Scripts\python.exe main.py --send-pending
```

此命令只重置未发送邮件的重试次数，不打开浏览器、不清除预约保护。
SMTP 接受后、记录确认前发生崩溃，可能导致重复邮件。

**不要为了重新运行而直接删除 `.state`。** 应先核对真实预约和剩余次数，
再有意识地归档/重置任务；没有自动重置操作。本地锁不能协调不同目录副本或机器，
同一账号只使用一个活动实例。

## 手动命令与故障排查

只加载配置、不安装、不显示菜单时，在后续执行 Python 的同一 PowerShell 进程运行：

```powershell
. .\personal\Set-VisaEnvironment.local.ps1 -ConfigureOnly
.\.venv\Scripts\python.exe main.py --check-config
```

手动安装的对应命令：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

| 问题 | 处理 |
|---|---|
| 根目录提示/错误 | 切换到包含 `main.py`、`requirements.txt`、`visa_tool` 的目录，而非私有脚本所在目录。 |
| Python 或 `.venv` 错误 | 检查 Python 安装和虚拟环境；启动脚本不会删除或替换损坏的环境。 |
| 安装或 `pip check` 失败 | 先解决报告的依赖/网络问题，再启动监控。 |
| 缺少 SMTP 变量 | 使用启动菜单，或先点加载 `-ConfigureOnly` 再手动运行 Python；独立配置子进程不能修改父进程环境。 |
| 没有菜单 | 保留自定义值，将旧私有配置副本升级为当前启动脚本。 |
| 验证超时/页面不匹配 | 检查停止原因；未知页面会安全失败，不伪造可用日期或成功结果。 |
| UNKNOWN 或拒绝重启 | 手动核对官方账号，不绕过提交保护。 |

应用退出码：`0` 为正常结束/到达观察上限，`1` 为运行错误、失败/未知改期或未发送通知，
`2` 为配置/启动错误或拒绝重启。启动脚本自身的安装错误返回 `1`。
零退出码不等于预约成功。

## 开发与验证

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
# 可选 Chrome 测试，仅使用本地合成页面：
$env:VISA_LOCAL_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:\VISA_LOCAL_BROWSER_TESTS
```

启动脚本测试使用临时项目及记录调用的 `pip`/应用替身，不真正下载依赖、发邮件或访问签证服务。
覆盖可用的两种 PowerShell、环境继承、首次安装、菜单路由和错误处理。
其他测试覆盖日期优先级、禁止点击模式、认证问题匹配、点击延迟、持久化提交限制、
结果判断、恢复、日志及邮件。可选浏览器测试访问本地页面；工作进程冒烟测试只打开空白页。

| 组件 | 职责 |
|---|---|
| `Set-VisaEnvironment.template.ps1` | 环境准备、私有配置模板及启动菜单。 |
| `main.py`、`visa_tool\settings.py` | 环境/默认值配置与严格转换。 |
| `visa_tool\app.py` | 监控状态机和命令行模式。 |
| `visa_tool\browser.py` | 受保护界面适配及隔离浏览器进程。 |
| `visa_tool\core.py` | 校验、持久化、锁、日志、邮件和时钟。 |
| `tests` | 单元测试及可选浏览器/PowerShell 集成测试。 |

这些测试不能证明真实 CAPTCHA 接受情况、网站配额或服务端预约语义。
在线页面变化可能需要调整适配器。

原始项目致谢：`SYuan03/VisaAppointmentWatcher` 和 `CChen19/us-visa-scheduler`。
