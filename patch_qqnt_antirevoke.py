# -*- coding: utf-8 -*-
# QQNT 9.9.36-53644 (wrapper.node 9.8.0.24541) 防撤回完整补丁集
# 覆盖：群聊撤回(F1) + 拍一拍撤回(F5) + 私聊(c2c)撤回全部路径
# 用法: py -3.14 patch_qqnt_antirevoke.py [apply]
# 不带 apply = 只检查当前状态
import sys, os, shutil

PATH = r"D:\Program Files\Tencent\QQNT\versions\9.9.36-53644\resources\app\wrapper.node"

# (offset, 旧字节, 新字节, 描述)
# F1 群聊: HandleRecallSysMsg 长消息跳过替换 (4处, 搜索头改尾字节)
F1_HEAD = bytes.fromhex("4C 89 C0 48 29 D0 48 83 F8 07 0F 87")
F1_HEAD_NEW = bytes.fromhex("4C 89 C0 48 29 D0 48 83 F8 07 0F 86")

def find_f1(data):
    hits = []
    idx = 0
    while True:
        i = data.find(F1_HEAD, idx)
        if i < 0:
            break
        hits.append(i + 8)  # 尾字节 0F 87 的偏移 = 头偏移+8
        idx = i + 1
    return hits

PATCHES = [
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
]

def main():
    data = open(PATH, "rb").read()
    lines = []
    def W(s):
        lines.append(str(s))
        print(s)

    W("=== QQNT 防撤回补丁 (file size=%d) ===" % len(data))

    # F1 检查/应用
    f1_offs = find_f1(data)
    W("F1 群聊补丁: 匹配头=%d 处" % len(f1_offs))
    if not f1_offs:
        W("  [警告] F1 搜索头未匹配，可能已是补丁态(0F 86)或版本不符")
        f1_done = data.count(F1_HEAD_NEW) >= 4
        W("  F1 是否已打(0F 86 计数=%d): %s" % (data.count(F1_HEAD_NEW), f1_done))
    else:
        f1_done = False

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

    apply = len(sys.argv) > 1 and sys.argv[1].lower() == "apply"
    if not apply:
        W("[DRY-RUN] 未写入。加 apply 执行。")
        open(os.path.join(os.environ["TEMP"], "patch_qqnt_result.txt"), "w", encoding="utf-8").write("\n".join(lines))
        sys.exit(0)

    if issues:
        W("存在未知状态，中止。")
        open(os.path.join(os.environ["TEMP"], "patch_qqnt_result.txt"), "w", encoding="utf-8").write("\n".join(lines))
        sys.exit(1)

    out = bytearray(data)
    # F1
    if not f1_done and f1_offs:
        for off in f1_offs:
            if out[off] == 0x87:
                out[off] = 0x86
        W("F1 已打 %d 处" % len(f1_offs))
    elif not f1_done:
        W("F1 跳过（搜索头不匹配，需人工检查版本）")
    # F5 + 私聊
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
        open(os.path.join(os.environ["TEMP"], "patch_qqnt_result.txt"), "w", encoding="utf-8").write("\n".join(lines))
        sys.exit(1)

    # 回读
    v = open(PATH, "rb").read()
    okall = True
    for off, old, new, desc in PATCHES:
        ok = v[off:off+len(new)] == new
        okall = okall and ok
        W("verify 0x%X [%s] %s" % (off, desc, "PASS" if ok else "FAIL"))
    if not f1_done and f1_offs:
        okall = okall and v.count(F1_HEAD_NEW) >= len(f1_offs)
    W("ALL_PASS=%s" % okall)
    open(os.path.join(os.environ["TEMP"], "patch_qqnt_result.txt"), "w", encoding="utf-8").write("\n".join(lines))
    sys.exit(0 if okall else 2)

if __name__ == "__main__":
    main()
