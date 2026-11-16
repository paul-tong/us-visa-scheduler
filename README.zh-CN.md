# 武汉美国访客签证预约助手

[English](README.md)

本工具在本地 Windows 桌面运行，通过网站正常界面查询武汉 B1/B2 或 B2
面谈可预约日期，可选择对**已有预约进行至多一次受保护的改期提交**。
默认仅监控，必须明确开启自动改期。

**重要限制：**保存的登录页面明确禁止自动化访问。只有在服务提供方允许的
情况下使用自动化。任何检查间隔、浏览器模式或验证码辅助方法，都不能保证
不被限制、封锁，或保证通过人机验证。

## 功能

- 从 `https://www.usvisascheduling.com/zh-CN/SignIn` 进入，仅在预期的认证域名
  填写账号密码；按实际显示的问题文本匹配本地答案，支持 1/3、2/3 等问题组合。
- 可在认证页面尝试兼容的 SeleniumBase UC GUI 人机验证操作；每次挑战最多调用一次，
  并受当前进程的可配置总次数限制。关闭、用尽预算、不能安全操作或未通过时，
  发邮件，暂停并等待用户在原浏览器中手动验证。
  不使用第三方验证码代答服务。
- 首页仅点击已验证的“重新安排预约”链接；检查签证类别、武汉领馆、申请人组
  以及已有预约的日期时间，不点击取消、关闭申请或创建新申请。
- 登录后每次界面操作前等待 `CLICK_WAIT_SECONDS` 秒，并在等待后重新校验。
  登录、密保答案和人机验证操作不受该延迟影响。
- 被动观察网站正常请求返回的完整可预约日期列表，不仅限于屏幕显示的两个月；
  不重放私有 API，不导出认证 Cookie 来加速查询。
- 按配置列表的顺序匹配闭区间日期范围；优先级最高且有日期的范围中选择最早日期。
  不把两个范围之间的间隔误认为可接受日期。
- 仅监控时绝不点击日期、时段或提交；自动改期时仅点击偏好日期，选择第一个
  可用且人数容量足够的时段，并在提交前再次校验。
- 在点击 Submit **之前**持久化不可自动重置的提交标记。观察结果 90 秒，
  发结果邮件、关闭本工具拥有的浏览器并停止。异常、重启或邮件失败均不能触发第二次提交。
- 对已识别的访问限制持久化冷却时间；初次失败后最多进行三轮恢复重试。
  其他未预期错误直接停止并通知。
- 记录事件、日期可用性、改期结果三类本地日志；发送偏好日期、每日状态、
  手动验证、限制/异常和改期结果邮件。

**不能保证：**自动通过验证码、绝不封号、服务端如何计算改期次数、原预约的
原子替换/保留、提交时该时段仍有名额、邮件最终进入收件箱。
无法确认的提交结果标记为 **UNKNOWN（未知）**，不会当作失败后重新提交。

## 安装（Windows PowerShell）

需要交互式 Windows 桌面及已安装的 Google Chrome。本次验证使用 Python 3.9.13；
锁定的 SeleniumBase 版本支持 Python 3.9 及以上。不要在监控过程中自动升级依赖。

```powershell
Set-Location C:\src\USVisa\us-visa-scheduler
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

不必激活虚拟环境。依赖锁定为 SeleniumBase 4.51.12（包含 PyAutoGUI extra）、
PyAutoGUI 0.9.54；SeleniumBase 根据 Python 版本选择对应的 Selenium。
首次启动可能下载匹配的 ChromeDriver，安装依赖/驱动需要网络。

## 配置 `main.py` 开头的设置

以下配置表及“运行预算”表中的全部 25 项优先读取环境变量；只有变量不存在时，才使用 `main.py` 对应
`os.environ.get(...)` 第二个参数中的默认值。修改默认值时请保留环境变量读取逻辑。
已存在的环境变量优先于文件修改。设置在 Python 启动时读取，修改外部终端不能改变已运行的进程。

环境变量是字符串。`build_config()` 在校验前转换布尔值、整数和 JSON。
已存在但格式错误（包括空的结构化值）的变量会明确报错，不会悄悄使用默认值。
特别是字符串 `"false"` **不会**开启自动提交。

| 属性 | 环境变量 | 格式 / 变量不存在时的默认值 |
|---|---|---|
| `USERNAME` | `VISA_USERNAME` | 字符串；默认为空。 |
| `PASSWORD` | `VISA_PASSWORD` | 签证账号密码；默认为空。 |
| `SECURITY_ANSWERS` | `VISA_SECURITY_ANSWERS` | JSON 问题到答案对象；默认使用文件中的映射，初始为空。整体替换，不合并。 |
| `EXPECTED_APPLICANTS` | `VISA_APPLICANTS` | 用分号 `;` 分隔准确姓名；默认空列表。 |
| `EXPECTED_VISA_CLASS` | `VISA_VISA_CLASS` | `B1/B2` 或 `B2`；默认 `B1/B2`。 |
| `EXPECTED_EXISTING_APPOINTMENT` | `VISA_EXISTING_APPOINTMENT` | 已有预约的北京时间 ISO 字符串；默认为空。 |
| `PREFERRED_DATE_RANGES` | `VISA_PREFERRED_DATE_RANGES` | JSON `[起始日期,结束日期]` 数组的数组；默认使用文件中的示例区间。 |
| `AUTO_BOOKING` | `VISA_AUTO_BOOKING` | `true`/`false` 或 `1`/`0`，不区分大小写；默认 `False`。 |
| `DAILY_EMAIL_TIMES` | `VISA_DAILY_EMAIL_TIMES` | 三个北京时间 HH:MM 的 JSON 数组；默认 `["08:00","12:00","17:00"]`。 |
| `SMTP_HOST` | `VISA_SMTP_HOST` | 主机名；默认 `smtp.gmail.com`。 |
| `SMTP_PORT` | `VISA_SMTP_PORT` | 整数字符串；默认 `465`，隐式 TLS。 |
| `SMTP_USERNAME` | `VISA_EMAIL_SENDER` | 发件人完整邮箱地址；默认为空。 |
| `SMTP_PASSWORD` | `VISA_SMTP_PASSWORD` | SMTP 应用专用密码；默认为空。 |
| `EMAIL_TO` | `VISA_EMAIL_TO` | 收件人邮箱地址；默认为空。 |

不要把真实密码和答案写入受版本控制的代码。环境变量**不是加密密码库**，
请保护电脑、会话和本地文件。下方全部 11 项运行预算同样遵循环境变量优先的规则。

### 当前进程作用域的 PowerShell 模板（推荐）

```powershell
Copy-Item .\Set-VisaEnvironment.template.ps1 .\Set-VisaEnvironment.local.ps1
# 编辑 .local.ps1：准确姓名、问题文本、日期、邮件地址。
# 运行时通过隐藏输入提示读取签证密码、三个答案和 SMTP 应用密码。
. .\Set-VisaEnvironment.local.ps1
.\.venv\Scripts\python.exe main.py --check-config
```

模板为每项提供注释和示例。按本次选择，它仅设置 **Process（当前进程）** 环境，
不写 User/Machine 注册表，也不需要管理员权限。收集完输入后再设置全部 25 项。
必须在同一个 PowerShell 窗口启动 Python；关闭窗口后设置不再保留。
另开 `powershell.exe` 执行脚本不能修改父终端的环境。
`.local.ps1` 副本已被 git 忽略；不要把真实凭据提交到模板中。
已有本地副本请合并模板新增的运行预算条目，不要覆盖已经填写的个人配置。
现有进程环境变量优先于 `main.py` 中修改的默认值；修改后应重新启动 Python。

### 登录、申请人和已有预约

```powershell
$env:VISA_USERNAME = 'your-username'
$env:VISA_PASSWORD = [System.Net.NetworkCredential]::new(
    '', (Read-Host 'Visa password' -AsSecureString)).Password
$env:VISA_APPLICANTS = 'Exact displayed applicant name'
# 多名申请人使用分号分隔，必须与网站显示的姓名一致。
$env:VISA_VISA_CLASS = 'B1/B2'
$env:VISA_EXISTING_APPOINTMENT = '2030-01-15T10:00:00'
```

最后一项必须替换为**当前已有预约**的北京时间，不是目标日期。
工具预期只有一个领事馆预约条目；其他预约/团体布局不支持时会安全停止。
将 `VISA_VISA_CLASS` 设置为首页实际显示的 `B1/B2` 或 `B2`。

环境变量的问题映射采用以下 JSON 结构（仅为格式示例；真实答案建议通过模板的隐藏提示输入）：

```json
{"Exact question text 1":"answer1","Exact question text 2":"answer2","Exact question text 3":"answer3"}
```

问题文本必须与显示的中文或英文匹配；可明确配置多语言别名。
JSON 支持中文及转义后的引号、反斜杠；重复键、非字符串答案或结构不正确会报错。
文件中的默认问题映射仍可引用 `VISA_ANSWER_1` 等单独变量，但只有在未设置
`VISA_SECURITY_ANSWERS` 整体映射时才生效。
工具会规范化空白及 Unicode，不模糊猜测答案；未知问题会停止。
本地另外限制**每个北京时间自然日最多提交两次账号密码**，并持久化计数。
该本地限制不是网站真实每日限额的声明。

### 偏好日期、自动改期和通知

```powershell
$env:VISA_PREFERRED_DATE_RANGES = '[["2026-12-01","2026-12-15"],["2026-12-22","2026-12-25"]]'
$env:VISA_AUTO_BOOKING = 'false'
$env:VISA_DAILY_EMAIL_TIMES = '["08:00","12:00","17:00"]'
```

过期的示例日期必须更新。启动时拒绝颠倒/已开始于过去的区间；监控期间不会
选择已经过去的日期。最偏好的区间放在最前面，即使它在日历上更晚。
仅监控模式也会发偏好日期邮件；关闭改期后不会为了“模拟”而点击日期或时段。

### 使用 Gmail 发信

使用完整 Gmail 地址和 Google 生成的应用专用密码，不使用普通 Google 登录密码。
应用密码需要开启 Google 两步验证，部分账号策略可能不提供该功能。
本工具实现的是密码式 SMTP，而不是 OAuth；若无法创建应用密码，不要改用普通账号密码。

```powershell
$env:VISA_SMTP_HOST = 'smtp.gmail.com'
$env:VISA_SMTP_PORT = '465'
$env:VISA_EMAIL_SENDER = 'your.name@gmail.com'
$env:VISA_EMAIL_TO = 'destination@example.com'
$env:VISA_SMTP_PASSWORD = [System.Net.NetworkCredential]::new(
    '', (Read-Host 'Gmail app password' -AsSecureString)).Password
.\.venv\Scripts\python.exe main.py --test-email
```

Gmail 隐式 TLS 地址为 `smtp.gmail.com:465`；本工具没有实现 STARTTLS/587。
输入 16 字符应用密码时不要包含显示时的分组空格。收件地址可以与 Gmail 发件地址相同。
`main.py` 的主机/端口默认值已改为 Gmail，但必须提供发件人、应用密码和收件人。
打开浏览器前必须成功发送启动通知（由 SMTP 服务器接受）；这不等于保证邮件到达收件箱。

Google 官方参考：`https://developers.google.com/workspace/gmail/imap/imap-smtp`
和 `https://support.google.com/accounts/answer/185833`。

### 运行预算

这些都是本地限制，不是网站公布的配额，也不保证不会被封锁。
所有数值预算必须为整数；轮询上下限、冷却、观察次数和超时必须为正数。
点击延迟和自动验证次数可以为零；恢复重试次数必须为 0–3。

| 配置项 | 环境变量 | 保守默认值 | 含义 |
|---|---|---:|---|
| `CLICK_WAIT_SECONDS` | `VISA_CLICK_WAIT_SECONDS` | 5 | 登录后每次界面操作前等待的秒数，不是只在登录成功后等一次。零关闭延迟；详细范围见下文。 |
| `POLL_SECONDS_MIN` | `VISA_POLL_SECONDS_MIN` | 1800 | 一轮观察完成后的随机暂停下限，包含端点。 |
| `POLL_SECONDS_MAX` | `VISA_POLL_SECONDS_MAX` | 3600 | 暂停上限，包含端点且不能小于下限；实际观察间隔还包含处理时间。 |
| `BLOCK_COOLDOWN_SECONDS` | `VISA_BLOCK_COOLDOWN_SECONDS` | 86400 | 限制后的默认冷却（24 小时）；采用更长的已观察到的 `Retry-After`。跨重启持久化，不是已验证的解封周期。 |
| `MAX_RECOVERY_RETRIES` | `VISA_MAX_RECOVERY_RETRIES` | 3 | 初次限制后额外恢复次数，按任务持久化。零表示首次限制即停止。绝不重试改期提交。 |
| `MAX_CHECKS_PER_RUN` | `VISA_MAX_CHECKS_PER_RUN` | 24 | 当前持久化任务的成功观察次数上限；尽管名称含 per-run，重启也不会清零。一次观察可能产生多个 HTTP 请求。 |
| `AUTO_VERIFICATION` | `VISA_AUTO_VERIFICATION` | `True` | 仅开启尽力而为的 Cloudflare GUI 辅助方法。`false` 或 `0` 关闭它，但不关闭账号密码/密保自动填写；持续挑战转为邮件通知的手动验证。 |
| `MAX_AUTO_VERIFICATIONS` | `VISA_MAX_AUTO_VERIFICATIONS` | 1 | 当前进程所有挑战中的辅助方法调用总上限。零关闭自动尝试；允许 10。每次挑战最多调用一次，未解决就转手动。 |
| `MANUAL_VERIFICATION_TIMEOUT_SECONDS` | `VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS` | 900 | 手动验证期限（15 分钟），在发送通知前开始计时。检测到预期下一页后继续，否则停止。与自动辅助调用后最多 60 秒的观察期独立。 |
| `PAGE_TIMEOUT_SECONDS` | `VISA_PAGE_TIMEOUT_SECONDS` | 45 | 普通页面/导航/响应等待，不是轮询间隔。浏览器进程看门狗额外预留命令开销和对应点击延迟。不改变提交后的固定 90 秒观察。 |
| `QUEUE_TIMEOUT_SECONDS` | `VISA_QUEUE_TIMEOUT_SECONDS` | 1800 | 每次虚拟排队的最大秒数（30 分钟）。让网站自行刷新，不强制刷新；超时停止并通知。 |

**自动验证的确切含义：**`AUTO_VERIFICATION=False` 或 `MAX_AUTO_VERIFICATIONS=0`
表示工具不会执行验证码点击。挑战自行消失时仍可继续，否则邮件提示手动验证。
开启时，即使辅助调用因窗口不安全等原因拒绝点击，也消耗一次调用预算。
总次数随新进程启动而重置，不随每次重试或登录重置；它计算的是辅助方法调用，
不是物理点击次数、库内部重新加载次数或 HTTP 请求数。
设置 10 **不代表对同一个复选框连续尝试十次**。一次调用后检测是否到达预期下一页；
未解决则进入有超时限制的手动流程。浏览器工作进程丢失则停止并通知人工处理。
一旦可能已经提交改期，禁止再调用验证辅助方法。

**点击延迟的范围：**只有验证已登录的签证首页后才启用，包括首页改期链接、
两次领馆下拉框选择、日历年/月选择、偏好日期、第一个可用时段和 Submit。
人机验证、账号密码/密保页面、只读检查和结果观察不增加该延迟，也不增加强制刷新。
每次操作记录 `CLICK_WAIT`，字段为 `target_action`、`delay_seconds`；等待后重新读取
上下文及控件。日期、申请人、已有预约或提交选择变化时安全停止，不使用旧控件继续提交；
时段消失时不提交。浏览器等待期间，主进程继续正常心跳工作。
提交后的 90 秒从 Submit 命令返回或抛出异常后开始，避免点击前等待及命令耗时吃掉观察期；
模糊结果仍保留永久提交标记，绝不重试。

每轮观察完成后，若允许继续查询，程序从 `[POLL_SECONDS_MIN, POLL_SECONDS_MAX]`
中重新均匀随机选择一个整数秒数。上下限都可能被选中，连续两次抽样也可能相同。
默认间隔为 30–60 分钟。等待从本轮工作结束后开始；两次观察开始时间之间还包含
处理本轮页面/通知所花的时间。空结果和仅监控模式使用相同逻辑。

```powershell
$env:VISA_POLL_SECONDS_MIN = '1800'
$env:VISA_POLL_SECONDS_MAX = '3600'
```

上下限必须为正整数，且最小值不能大于最大值。两项都设置为 `1800` 可保持原先
固定 30 分钟等待。原 `POLL_SECONDS` 已移除；请更新已有本地设置脚本副本，使用两个新变量。
某个变量不存在时，仅该项使用 `main.py` 中的默认值；空值或错误格式会报错。
不需要迁移或删除已有持久化任务状态。

每次抽样会写入 `EventLog`，操作为 `POLL_WAIT`，字段包含 `delay_seconds`、
`minimum_seconds`、`maximum_seconds`。提交后或达到查询预算时不再抽样等待。
限制冷却、`Retry-After`、验证超时、提交后的 90 秒观察以及北京时间每日三次邮件
**不会随机化**。随机等待期间仍执行心跳日志轮转和邮件调度。随机化不保证避免封锁。

#### 较活跃的观察配置

你提出的配置**通过参数校验**，但不是网站已确认的安全频率。
`300–600` 表示暂停 5–10 分钟，**不保证两次观察间隔小于十分钟**：
点击延迟、页面请求、认证、排队和邮件处理都会额外耗时。

如果服务方允许主动观察，可先采用下面较克制的起始示例：

```powershell
$env:VISA_CLICK_WAIT_SECONDS = '3'
$env:VISA_POLL_SECONDS_MIN = '300'
$env:VISA_POLL_SECONDS_MAX = '540'
$env:VISA_BLOCK_COOLDOWN_SECONDS = '86400'
$env:VISA_MAX_RECOVERY_RETRIES = '3'
$env:VISA_MAX_CHECKS_PER_RUN = '24'
$env:VISA_AUTO_VERIFICATION = 'true'
$env:VISA_MAX_AUTO_VERIFICATIONS = '1'
$env:VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS = '900'
$env:VISA_PAGE_TIMEOUT_SECONDS = '45'
$env:VISA_QUEUE_TIMEOUT_SECONDS = '1800'
```

暂停 5–9 分钟为处理时间预留一些余量，仍不能保证实际间隔小于十分钟。
`main.py` 和模板中的保守默认值保持不变。

| 你提出的值 | 评价 |
|---|---|
| 点击延迟 `3` | 支持；每次登录后操作均等待，但不能保证不封锁。 |
| 轮询 `300–600` | 支持；`300–540` 只是活跃观察的起始示例，不是绕过限制或安全保证。 |
| 冷却 `7200` | 支持；两小时不是已经验证的解封/重置周期。建议初始保留 `86400`，更长的服务器等待要求优先。 |
| 观察 `150` 次 | 暴露量明显增大。150 次成功观察包含 149 次暂停，按 300–600 秒计算为 12 小时 25 分钟到 24 小时 50 分钟，另加处理时间；一次观察不等于一个请求，本地登录/恢复上限可能提前停止。 |
| 自动验证 `True`、上限 `10` | 支持跨多次挑战计数；建议从 `1` 开始，重复挑战不应导致对同一复选框快速重试十次。 |
| 重试 `3`；手动/页面/排队 `900/45/1800` | 与保守默认值相同；重试针对访问限制，不针对改期提交。 |

不假定任何未公开的网站配额或挑战接受阈值。Cloudflare 官方将生产环境中的自动化
挑战处理列为不支持的场景：
`https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/`。

接近页面浏览上限的警告也会被视为限制。冷却期间不发送预约查询，
但冷却不会清除服务端限制。一次恢复可能包含正常导航和认证请求，
不是 HTTP 层面只发送一次请求。本地查询/登录预算可能使任务提前停止。

## 运行

```powershell
.\.venv\Scripts\python.exe main.py --check-config
.\.venv\Scripts\python.exe main.py --test-email
.\.venv\Scripts\python.exe main.py
```

`--check-config` 仅本地校验，不写运行状态、不访问网站。
`--test-email` 仅明确发送一封测试邮件，不打开浏览器。
正常运行会先校验设置、获取单实例锁、检查持久化停止/提交状态并发送启动通知。

建议先使用 `VISA_AUTO_BOOKING = 'false'`，文件默认值也是 `False`。
只有在确认设置、访问许可及上述风险后，才把环境值改为 `'true'`。
运行测试不需要真实改期。

浏览器时区固定为 `Asia/Shanghai`，每次选择前检查，避免电脑处于美国时区导致日期偏移。
GUI 验证时保持窗口可见且位于前台，不要最小化或同时操作鼠标/键盘。
窗口不安全、被遮挡或不在前台时使用手动回退。GUI 辅助方法仅限认证页，
不会在已选择预约的页面上尝试点击。

收到手动验证邮件后，只在现有窗口内完成验证，不要自行选择日期或提交预约。
程序暂停浏览器操作并发送截止时间，只有识别到预期下一页面才继续。
如果自动验证辅助方法卡死，工具会终止自己拥有的进程树并停止；
这种情况无法保留原窗口继续手动验证。

Windows 下使用 kill-on-close Job Object 管理浏览器工作进程及其 Chrome 子进程，
不会按进程名终止其他 Chrome 窗口。通过计划任务运行时，GUI 操作需要已登录且
未锁定的交互式桌面。

## 总体流程与结果含义

```text
校验配置 -> 单实例锁/持久化状态 -> 启动邮件 -> 登录
 -> 自动验证或邮件通知手动回退 -> 匹配安全问题
 -> 校验首页 -> 仅点击改期 -> 校验已有预约/申请人
 -> 正常选择领馆 -> 观察返回日期 -> 日志和邮件
 -> 无匹配或仅监控：等待并按预算继续
 -> 有偏好日期：选择第一个可用时段 -> 再次校验
 -> 先写永久提交标记 -> Submit 一次 -> 观察 90 秒
 -> SUCCESS / FAILURE / UNKNOWN -> 结果邮件 -> 关闭浏览器并停止
```

SUCCESS 必须有网站 `AllScheduled` 响应，并能关联到本次请求的日期和时段编号，
不是只看标题/跳转。FAILURE 必须有明确错误响应；证据缺失或冲突为 UNKNOWN。
申请人、已有预约或选择内容变化时，拒绝提交。
偏好日期没有可用时段时不提交，本次观察结束后继续监控。

一旦可能已经提交，就不再自动处理验证码、刷新、重新登录、取消或重试提交。
网站自身的正常回调仍可能运行，但客户端不会再次提交。
Ctrl+C、进程/电脑故障可以中断 90 秒观察；永久提交标记仍阻止再次尝试。

## 日志、持久化及邮件恢复

路径均以项目根目录为基准，与启动命令所在目录无关：

- `logs\EventLog_YYYY_MM_DD.jsonl`：操作、结果、错误和重试。
- `logs\AvailabilityLog_YYYY_MM_DD.jsonl`：每次成功返回的完整日期观察，
  含非偏好日期及明确的偏好标记/优先级。
- `logs\BookingLog_YYYY_MM_DD.jsonl`：尝试的北京时间和结果。
- `.state\state.json`：停止/冷却/重试计数、上次观察、每日通知及邮件发件箱；
  不保存签证密码或安全问题答案。
- `.state\submission.json`：以独占创建并 fsync 的方式写入，永久阻止自动重复提交。

每条日志都有 PST（固定 UTC-08:00）、UTC、北京时间三个时间戳。
按北京时间日期切换文件，等待/冷却期间也执行轮转。
同一天重启会创建带唯一后缀的新文件，不截断旧文件。
午夜轮转由事件循环心跳驱动，不是硬实时保证。

**每次成功观察发现偏好日期时都会发邮件**，即使日期与上次相同。
每日三次邮件使用缓存的最新观察并标注时间/状态，不额外强制访问网站。
启动前错过多个通知时段时只补发最近一次；已记录的时段重启后不重复发送。
任务停止后不再继续每日通知。

邮件最多尝试发送三次，失败保存在本地。只重发未发送邮件、不打开浏览器：

```powershell
.\.venv\Scripts\python.exe main.py --send-pending
```

该命令仅明确重置未发送邮件的尝试次数。SMTP 接受邮件后、写入本地确认前若崩溃，
恢复时可能重复发送；邮件失败永远不会解除预约提交锁或重启改期。

**不要删除 `.state` 来绕过停止状态。** 提交后必须先人工核实真实预约及剩余改期次数。
确实需要新任务时，应在所有实例停止、人工核对并更新配置之后，明确离线归档/重置
对应状态；没有自动重置命令。每个账号只使用一个项目副本；
本地锁不能协调不同目录、电脑上的实例。

日志、状态和浏览器资料包含个人信息，应限制访问，不要上传含认证信息的网页或截图。
`.gitignore` 已排除状态、日志、虚拟环境及 SeleniumBase 测试产物。

退出码：`0` 正常完成或达到查询预算；`1` 异常、失败/未知的改期结果或仍有未发邮件；
`2` 配置/启动错误或拒绝重启。退出码为零本身不能证明预约成功。

## 验证与边界

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
# 可选：真实 Chrome，仅访问本地合成测试页面
$env:VISA_LOCAL_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:\VISA_LOCAL_BROWSER_TESTS
```

本地浏览器测试阻止访问签证、认证、Cloudflare 域名；独立 UC 冒烟测试仅打开默认
空白页面并验证工作进程清理。测试覆盖日期优先级/间隔、安全问题组合、不点击
非偏好日期、空结果、跨月份、真实时段列、陈旧状态、一次提交/重启、90 秒结果观察、
重试上限、邮件失败及午夜日志轮转。
配置测试还覆盖全部 25 项环境覆盖及缺省值、严格的布尔/JSON 转换、不泄露敏感值的错误，
并在一次性 PowerShell 子进程中使用模拟密码输入验证 Process 作用域和 Python 继承。
轮询测试覆盖包含端点、每次重新抽样、相等上下限、非法范围、日志内容，以及不额外等待或改变安全等待。
预算/延迟测试覆盖关闭及用尽自动验证、跨挑战计数、所有登录后界面操作、认证不增加等待、
真实首页延迟、等待后重新校验、工作进程进度和超时处理，以及延迟或模糊提交后完整的 90 秒观察。

**未验证真实账号登录、实际 Cloudflare 接受情况、服务端次数扣减或真实改期交易。**
网站结构变化会安全失败，而不是伪造可用日期或成功结果。
不支持首次新预约、其他领馆、OFC/生物信息预约、取消或重建申请。

详细资源分析和逐项需求评估位于
`C:\src\USVisa\CopilotOutput\VisaTool_analysis_astra.md`。

原始项目致谢：`SYuan03/VisaAppointmentWatcher` 和 `CChen19/us-visa-scheduler` 草稿。
