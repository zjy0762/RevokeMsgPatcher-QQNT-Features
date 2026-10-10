# QQNT 防撤回补丁特征（wrapper.node 9.8.0.24541）

针对 **QQ 9.9.36-53644**（`wrapper.node` 版本 **9.8.0.24541**）的防撤回补丁特征与一键脚本。

> 官方工具 [RevokeMsgPatcher](https://github.com/huiyadanli/RevokeMsgPatcher) 内置特征（20250803 / 20260816）最高仅支持 wrapper.node 9.8.0.19307，**9.8.0.24541 中官方特征全部 0 匹配**（代码结构已重构）。本仓库提供该版本的手动特征与一键脚本，**字节级验证通过**。

---

## 快速使用（小白版）

1. 下载本仓库的 `patch_qqnt_antirevoke.ps1`
2. 右键该文件 → **使用 PowerShell 运行**（推荐以管理员身份运行）
3. 脚本自动完成：定位特征 → 备份原文件 → 打补丁（4 处）
4. **重启 QQ**，生效

> 脚本自动备份原文件为 `wrapper.node.bak`（仅首次运行备份），想还原时把 `.bak` 改回 `wrapper.node` 即可。
>
> QQ 自动更新会覆盖补丁，失效后重新运行一次脚本即可。已打过补丁时脚本会提示"0 匹配"，不会重复修改。

## 技术说明

| 项目 | 内容 |
|---|---|
| 适用版本 | QQ 9.9.36-53644 / wrapper.node 9.8.0.24541 |
| 特征（Search） | `4C 89 C0 48 29 D0 48 83 F8 07 0F 87` |
| 替换（Replace） | `4C 89 C0 48 29 D0 48 83 F8 07 0F 86` |
| 匹配数量 | 4 处（撤回消息内容长度检查分支 `HandleRecallSysMsg`） |
| 修改位置 | `0x138B783` / `0x13B48E2` / `0x179B79B` / `0x274BE0B`（`0F 87`→`0F 86`） |
| 验证日期 | 2026-10-11 |
| 验证方式 | 字节级 diff 仅 4 字节差异；补丁后 QQ 启动正常（10 进程无崩溃） |

特征 JSON 见 `QQNT_9.8.0.24541_防撤回特征.json`（可直接对照提交给 RevokeMsgPatcher 官方）。

## 注意事项（重要）

- **封号风险**：官方 RevokeMsgPatcher 2.1 明确说明防撤回功能存在**封号 / 警告 / 下线风险**，请自行评估，后果自负
- 请勿将本工具用于非法或恶意用途
- 本仓库只提供**特征与脚本**（文本形式），不包含任何修改过的程序二进制

## 致谢

- 原项目：[huiyadanli/RevokeMsgPatcher](https://github.com/huiyadanli/RevokeMsgPatcher)（GPL-3.0，防撤回补丁工具）
- 果核剥壳 v2.1 工具包（特征来源参考）

## 仓库文件

| 文件 | 说明 |
|---|---|
| `patch_qqnt_antirevoke.ps1` | 一键补丁脚本（Windows PowerShell，无需安装任何环境） |
| `QQNT_9.8.0.24541_防撤回特征.json` | 特征数据（PatchJson 增量格式，可提交官方） |
