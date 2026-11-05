# -*- coding: utf-8 -*-
# QQNT 9.9.36-53644 (wrapper.node 9.8.0.24541) 防撤回完整补丁集
# 覆盖：群聊撤回(F1) + 拍一拍撤回(F5) + 私聊(c2c)撤回全部路径
# 用法: py -3.14 patch_qqnt_antirevoke.py [apply] [wrapper.node 路径或 QQNT 安装目录]
# 不带 apply = 只检查当前状态；不带路径 = 自动查找（注册表 + 常见目录）
import sys, os, shutil

VERSION = "9.9.36-53644"
REL = os.path.join("versions", VERSION, "resources", "app", "wrapper.node")
DEFAULT_DIRS = [
    r"C:\Program Files\Tencent\QQNT",
    r"C:\Program Files (x86)\Tencent\QQNT",
    r"D:\Program Files\Tencent\QQNT",
    r"D:\Tencent\QQNT",
]

def registry_dir():
    try:
        import winreg
    except ImportError:
        return None
    for key in (r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\QQ",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QQ"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                icon = winreg.QueryValueEx(k, "DisplayIcon")[0]  # 形如 D:\Tencent\QQNT\QQ.exe,0
                return os.path.dirname(icon.split(",")[0].strip('"'))
        except OSError:
            pass
    return None

def resolve_path(arg):
    if arg:
        return arg if arg.lower().endswith(".node") else os.path.join(arg, REL)
    for d in [registry_dir()] + DEFAULT_DIRS:
        if d and os.path.exists(os.path.join(d, REL)):
            return os.path.join(d, REL)
    return None

# F1 群聊: HandleRecallSysMsg 长消息跳过替换。特征头全文件匹配 5 处，仅其中 4 处是撤回路径，
# 故按固定偏移打补丁（偏移 = 特征头起点，尾字节 0F 87 -> 0F 86 位于 +11）
F1_HEAD = bytes.fromhex("4C 89 C0 48 29 D0 48 83 F8 07 0F 87")
F1_HEAD_NEW = bytes.fromhex("4C 89 C0 48 29 D0 48 83 F8 07 0F 86")
F1_OFFS = [0x138B778, 0x13B48D7, 0x179B790, 0x274BE00]

# (offset, 旧字节, 新字节, 描述)
PATCHES = [(off, F1_HEAD, F1_HEAD_NEW, "F1 群聊撤回 0x%X" % (off + 11)) for off in F1_OFFS] + [
    # F5 拍一拍撤回
    (0x154E9C6, b"\xE8\xFB\x34\xFE\xFF", b"\x90"*5, "F5 拍一拍撤回 NOP"),
    # 私聊(c2c)撤回：4个解析变体入口直接返回false
    (0xCA8376,  b"\x55\x56\x57",     b"\x31\xC0\xC3", "私聊varA 入口返回false"),
    (0x168FF02, b"\x55\x41\x57",     b"\x31\xC0\xC3", "私聊varC 入口返回false"),
    (0x1A2062A, b"\x55\x41\x57",     b"\x31\xC0\xC3", "私聊varD 入口返回false"),
    # 私聊varB 执行撤回 4个调用点 NOP (call 0x3c5891c)
    (0x3C5289F, b"\xE8\x78\x60\x00\x00", b"\x90"*5, "私聊varB 执行1 NOP"),
    (0x3C528B9, b"\xE8\x5E\x60\x00\x00", b"\x90"*5, "私聊varB 执行2 NOP"),
    (0x3C528CD, b"\xE8\x4A\x60\x00\x00", b"\x90"*5, "私聊varB 执行3 NOP"),
    (0x3C528DE, b"\xE8\x39\x60\x00\x00", b"\x90"*5, "私聊varB 执行4 NOP"),
    # 撤回记录/删除执行核心：OnDeleteMsgs 两条路径 + 类型分发全部最终汇入 0x1534166
    # 共 6 个调用者（0x15339CF/0x1533D77/0x1534569/0x1534686/0x15358C4/0x1535CE8），入口返回即全部失效
    (0x1534166, b"\x55\x41\x57", b"\x31\xC0\xC3", "撤回执行核心 0x1534166 入口返回"),
]

def main():
    args = sys.argv[1:]
    apply = bool(args) and args[0].lower() == "apply"
    if apply:
        args = args[1:]
    PATH = resolve_path(args[0] if args else None)

    lines = []
    def W(s):
        lines.append(str(s))
        print(s)
    def done(code):
        open(os.path.join(os.environ["TEMP"], "patch_qqnt_result.txt"), "w", encoding="utf-8").write("\n".join(lines))
        sys.exit(code)

    if not PATH or not os.path.exists(PATH):
        W("ERROR: 未找到 QQNT %s 的 wrapper.node%s，请把路径作为参数传入" % (VERSION, " (%s)" % PATH if PATH else ""))
        done(1)

    data = open(PATH, "rb").read()
    W("=== QQNT 防撤回补丁 %s (file size=%d) ===" % (PATH, len(data)))

    issues = 0
    for off, old, new, desc in PATCHES:
        cur = data[off:off+len(old)]
        if cur == old:
            W("0x%X [%s] OLD-MATCH(可打)" % (off, desc))
        elif cur == new:
            W("0x%X [%s] NEW-ALREADY(已打)" % (off, desc))
        else:
            W("0x%X [%s] MISMATCH! cur=%s" % (off, desc, cur.hex(" ").upper()))
            issues += 1

    if not apply:
        W("[DRY-RUN] 未写入。加 apply 执行。")
        done(0)

    if issues:
        W("存在未知状态，中止。")
        done(1)

    out = bytearray(data)
    for off, old, new, desc in PATCHES:
        out[off:off+len(new)] = new
        W("OK 0x%X %s" % (off, desc))

    bak = PATH + ".antirevoke_full.bak"
    if not os.path.exists(bak):
        shutil.copyfile(PATH, bak)
        W("备份 -> %s" % bak)

    try:
        open(PATH, "wb").write(bytes(out))
        W("写入完成。")
    except PermissionError:
        W("ERROR: 写入被拒绝（QQ 正在运行？先关闭 QQ 再执行）")
        done(1)

    # 回读
    v = open(PATH, "rb").read()
    okall = True
    for off, old, new, desc in PATCHES:
        ok = v[off:off+len(new)] == new
        okall = okall and ok
        W("verify 0x%X [%s] %s" % (off, desc, "PASS" if ok else "FAIL"))
    W("ALL_PASS=%s" % okall)
    done(0 if okall else 2)

if __name__ == "__main__":
    main()
