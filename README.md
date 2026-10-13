# RevokeMsgPatcher-QQNT-Features

PC 微信 / QQNT（QQ 新版）防撤回补丁特征与一键脚本。

## 支持版本

| 应用 | 版本 | 目标文件 | 说明 |
|---|---|---|---|
| QQNT | 9.9.36-53644 | `resources\app\wrapper.node`（9.8.0.24541，≈117.8MB） | 群聊 + 私聊 + 拍一拍撤回 |
| PC 微信 | 4.1.15.12 | `Weixin.dll` | 用果核 v2.1 `RevokeMsgPatcher.exe` 选"微信4.0+防撤回" |

> 官方工具 [RevokeMsgPatcher](https://github.com/huiyadanli/RevokeMsgPatcher) 内置特征最高仅支持 wrapper.node 9.8.0.19307，**9.8.0.24541 中官方特征全部 0 匹配**（代码结构已重构）。本仓库提供该版本的手动特征与一键脚本，**字节级验证通过**。
>
> 注意：QQNT 各版本 `wrapper.node` 内部偏移不同，本脚本的偏移仅对 9.9.36-53644 有效。其他版本请先反汇编核对偏移再使用。

## 一键补丁（QQNT）

```
py -3.14 patch_qqnt_antirevoke.py        # 只检查当前状态
py -3.14 patch_qqnt_antirevoke.py apply  # 打补丁（需先退出 QQ）
```

脚本自动备份为 `wrapper.node.antirevoke_full.bak`，可随时还原。幂等安全（已打过的会跳过）。

## 覆盖的撤回路径

### 群聊撤回（HandleRecallSysMsg）
搜索 4 处特征头 `4C 89 C0 48 29 D0 48 83 F8 07 0F 87`，尾字节 `0F 87 → 0F 86`。
语义：长消息(>7B)撤回时跳过替换，消息内容保留。

### 私聊(c2c)撤回（本仓库逆向新增）
QQNT 新版代码重构后，`wrapper.node` 中私聊撤回有 4 个解析变体
（日志引用 `[Msg] on c2c recall nfy!`），分别位于：

| 变体 | 偏移 | 补丁方式 | 说明 |
|---|---|---|---|
| varA | `0xCA8376` | 入口 `55 56 57 → 31 C0 C3`（直接返回 false） | 解析后经 `0xca7fac` 执行撤回 |
| varB | `0xCA8883` | 4 个 `call 0x3c5891c` 调用点 NOP（`0x3C5289F/B9/CD/DE`） | 无论解析成败都广播删除消息，全部阻断 |
| varC | `0x168FF02` | 入口 `55 41 57 → 31 C0 C3` | vtable 间接分发的通知处理器 |
| varD | `0x1A2062A` | 入口 `55 41 57 → 31 C0 C3` | 网络通知入口，阻断撤回 ID 提取 |
| **撤回执行核心** | `0x1534166` | 入口 `55 41 57 → 31 C0 C3` | **OnDeleteMsgs 两条路径 + 类型分发全部汇入点，共 6 个调用者（0x15339CF/0x1533D77/0x1534569/0x1534686/0x15358C4/0x1535CE8），入口返回即全部失效** |

### 拍一拍撤回
`0x154E9C6`：`E8 FB 34 FE FF → 90 90 90 90 90`（NOP 掉执行调用）。

## 验证

```
py -3.14 patch_qqnt_antirevoke.py
```

所有条目显示 `NEW-ALREADY(已打)` 且无 MISMATCH 即为正常。

## 注意事项（重要）

- **封号风险**：官方 RevokeMsgPatcher 2.1 明确说明防撤回功能存在**封号 / 警告 / 下线风险**，请自行评估，后果自负
- 请勿将本工具用于非法或恶意用途
- 本仓库只提供**特征与脚本**（文本形式），不包含任何修改过的程序二进制
- QQ 自动更新会覆盖补丁，失效后重新运行一次脚本即可

## 仓库文件

| 文件 | 说明 |
|---|---|
| `patch_qqnt_antirevoke.py` | 一键补丁脚本（需要 Python 3.14 / capstone 环境，`py -3.14`） |
| `QQNT_9.8.0.24541_防撤回特征.json` | 特征数据 |

## 致谢

- 原项目：[huiyadanli/RevokeMsgPatcher](https://github.com/huiyadanli/RevokeMsgPatcher)（GPL-3.0，防撤回补丁工具）
- 果核剥壳 v2.1 工具包（特征来源参考）
