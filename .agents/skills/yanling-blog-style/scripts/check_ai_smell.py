#!/usr/bin/env python3
"""言零博客（blog.caowo.de）去 AI 味、防人机感与顶部引流守卫静态检查器（v3 终版）。"""

import re
import sys
from pathlib import Path

PROSE_PATTERNS = [
    ("禁用转折句式「不是…而是」", re.compile(r"(?:不是|并不是)[^。！？；\n]{1,80}而是")),
    ("禁用转折句式「并非…而是」", re.compile(r"并非[^。！？；\n]{1,80}而是")),
    ("禁用递进句式「不仅…更」", re.compile(r"(?:不仅|不但)[^。！？；\n]{1,80}(?:更|而且还)")),
    ("禁用对仗句式「不在于…而在于」", re.compile(r"不在于[^。！？；\n]{1,80}而在于")),
    ("禁用对仗句式「与其说…不如说」", re.compile(r"与其说[^。！？；\n]{1,80}不如说")),
    (
        "AI 腔套话或自媒体词汇",
        re.compile(
            r"总而言之|综上所述|值得注意的是|需要指出的是|显而易见|不难发现|众所周知|毫无疑问|"
            r"换句话说|某种意义上|从某种程度上|之所以|双刃剑|赋能|抓手|闭环|心智|全景|多维度|深度剖析|"
            r"保姆级|干货满满|一分钟速读|家人们|宝子们|兄弟们"
        ),
    ),
    ("破折号「——」（标杆文为 0 处，请改用冒号、逗号或拆成短句）", re.compile(r"——")),
    ("生硬括号补丁「（注：…）」", re.compile(r"[（(]注[：:]")),
    ("列表项加粗冒号模板「- **标题**：」（AI 典型排版指纹）", re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*[^*]+\*\*\s*[：:]")),
    ("日文假名或乱码字符", re.compile(r"[\u3040-\u30ff\ufffd]")),
    (
        "疑似隐私路径、过时服务/邮箱或非官方弃用域名",
        re.compile(
            r"yileina|UserRelocate|/root/\.openclaw|/root/blog-repo|wizawn\.com|ccwu\.cc|"
            r"api\.caowo\.de|ruanzhu\.caowo\.de|hihacker@foxmail\.com"
        ),
    ),
    ("残留模板标记", re.compile(r"geo_target:|<!-- JSON-LD|CVE-202\d-XXXX")),
    ("手写旧版群二维码（会屏蔽 Hugo 顶部统一交流群引流卡片渲染！）", re.compile(r"qq-group-qr\.jpg")),
    ("Markdown 空表格单元格", re.compile(r"\|\s*\|\s*\|")),
    ("模板式章节标题（前言/引言/总结/写在最后/结语/相关阅读）", re.compile(r"^##\s+(?:前言|引言|总结|写在最后|结语|小结|相关阅读|回顾)\s*$")),
]

MACRO_OPENING_RE = re.compile(
    r"随着.{1,20}的(?:发展|普及|演进|兴起)|在当今.{1,15}时代|近年来，随着|本文将从.{1,20}(?:维度|角度|方面)|下面我们将(?:深入|详细|全面)"
)
PREACHY_ENDING_RE = re.compile(
    r"永无止境的.{0,6}博弈|任重而道远|希望本文能对.{1,10}有所帮助|欢迎在评论区留言|让我们拭目以待|共同守护网络"
)
TITLE_CLICHE_RE = re.compile(r"深度拆解|全解析|终极版|保姆级|全景|底层原理与实现|——")
BOX_RE = re.compile(r"[┌┐└┘├┤┬┴┼─│▼▲]|──▶|◀──")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2705\u274c\u26a0\u2b50\u2728\u2764]")


def strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def extract_anchor_tokens(title: str, fm_block: str) -> list[str]:
    """提取标题和 tags 里的关键检索锚点词，用于校验开篇是否丢了核心引流词。"""
    tokens: list[str] = []
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_.-]{2,}", title):
        tok = m.group(0)
        if tok.lower() not in {"the", "and", "with", "for", "from", "api"}:
            tokens.append(tok)
    tag_line = re.search(r"^tags:\s*\[(.*?)\]", fm_block, re.M)
    if tag_line:
        for tm in re.finditer(r'"([^"]+)"|\'([^\']+)\'', tag_line.group(1)):
            val = (tm.group(1) or tm.group(2) or "").strip()
            if len(val) >= 2:
                tokens.append(val)
    return tokens


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    fm_end = None
    is_page = False
    is_post = False
    title_val = ""
    fm_block = ""

    if not text.startswith("---\n"):
        errors.append(f"{path}:1: 缺少顶部 YAML frontmatter (---)")
    else:
        for idx in range(1, min(35, len(lines))):
            if lines[idx].strip() == "---":
                fm_end = idx
                break
        if fm_end is None:
            errors.append(f"{path}:1: YAML frontmatter 未闭合")
        else:
            if fm_end + 1 < len(lines) and lines[fm_end + 1].strip() == "---":
                errors.append(f"{path}:{fm_end + 2}: 存在多余的连续 --- 分隔线")
            fm_block = "\n".join(lines[1:fm_end])
            is_page = (
                'type: "page"' in fm_block
                or "type: page" in fm_block
                or path.name == "_index.md"
                or re.search(r"^layout\s*:", fm_block, re.M) is not None
            )
            is_post = (not is_page) and ("_build:" not in fm_block)
            if is_post:
                if not re.search(r"^weight\s*:", fm_block, re.M):
                    errors.append(f"{path}:1: 原创文章需显式设置 weight: 10（排在 weight: 100 的聚合资讯之前）")
                for req_field in ("description", "categories", "tags"):
                    if not re.search(rf"^{req_field}\s*:", fm_block, re.M):
                        errors.append(f"{path}:1: Frontmatter 缺少 {req_field} 字段（影响 SEO 引流与顶部配套服务匹配）")
            tm = re.search(r'^title:\s*"(.*)"\s*$', fm_block, re.M)
            if tm:
                title_val = tm.group(1)
                if path.name != "index.md":
                    m_tc = TITLE_CLICHE_RE.search(title_val)
                    if m_tc:
                        errors.append(f"{path}:2: 标题含自媒体/AI 套话词「{m_tc.group(0)}」 -> {title_val}")

    body_start = (fm_end + 1) if fm_end is not None else 0
    in_fence = False
    prose_bold_count = 0
    table_count = 0
    non_empty_prose_lines = 0
    bullet_lines = 0
    has_curly_quote = False
    has_straight_quote = False
    prose_paragraphs: list[str] = []

    for offset, line in enumerate(lines[body_start:]):
        lineno = body_start + offset + 1
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if EMOJI_RE.search(line):
            errors.append(f"{path}:{lineno}: 存在装饰性 Emoji -> {line.strip()[:60]}")
        if BOX_RE.search(line):
            errors.append(f"{path}:{lineno}: 存在 ASCII 框图/流程图字符 -> {line.strip()[:60]}")
        if in_fence:
            continue

        if line.strip() == "↓":
            errors.append(f"{path}:{lineno}: 存在独立成行的线性箭头 ↓")

        if re.search(r"\\\$\d", line):
            errors.append(f"{path}:{lineno}: Hugo Markdown 中美元金额请直接写 $数字，切勿转义 \\$（反引号内会渲染出反斜杠）")

        stripped = line.strip()
        if stripped:
            non_empty_prose_lines += 1
            if re.match(r"^(?:[-*]|\d+\.)\s+", stripped):
                bullet_lines += 1
            if not stripped.startswith(("#", "|", "---")):
                prose_paragraphs.append(stripped)

        if re.match(r"^\|[-:| ]+\|$", stripped):
            table_count += 1

        clean_line = strip_inline_code(line)
        clean_no_links = re.sub(r"\]\([^)]*\)", "]", clean_line)
        clean_no_html = re.sub(r"<[^>]+>", "", clean_no_links)
        clean_no_shortcodes = re.sub(r"\{\{<.*?>\}\}", "", clean_no_html)

        is_table_row = clean_line.lstrip().startswith("|")
        if not is_table_row and not is_page:
            prose_bold_count += len(re.findall(r"\*\*[^*]+\*\*", clean_no_shortcodes))

        if "“" in clean_no_shortcodes or "”" in clean_no_shortcodes:
            has_curly_quote = True
        if '"' in clean_no_shortcodes:
            has_straight_quote = True

        for label, pat in PROSE_PATTERNS:
            if label.startswith("列表项加粗冒号模板") and is_page:
                continue
            raw_or_clean = (
                line
                if label in ("Markdown 空表格单元格", "手写旧版群二维码（会屏蔽 Hugo 顶部统一交流群引流卡片渲染！）")
                else clean_line
            )
            target = (
                raw_or_clean.replace("wizawn.com", "")
                if (label.startswith("疑似隐私路径") and path.name == "domain-ownership-clarification.md")
                else raw_or_clean
            )
            m = pat.search(target)
            if m:
                errors.append(f"{path}:{lineno}: {label} ({m.group(0)})")

    if in_fence:
        errors.append(f"{path}:{len(lines)}: 存在未闭合的代码块 (```)")

    if not is_page and prose_bold_count > 2:
        errors.append(
            f"{path}: 正文自然段加粗过多（当前 {prose_bold_count} 处，标杆文为 0 处，上限 2 处；请改用反引号 `...` 或自然语序）"
        )

    if table_count > 2:
        errors.append(f"{path}: 表格数量偏多（当前 {table_count} 张，上限 2 张；非核心结构化数据请改用自然段叙述）")

    if is_post and non_empty_prose_lines >= 15 and (bullet_lines / non_empty_prose_lines) > 0.35:
        pct = int(round(100 * bullet_lines / non_empty_prose_lines))
        errors.append(
            f"{path}: 列表行占比过高（{bullet_lines}/{non_empty_prose_lines} = {pct}%，上限 35%），提纲/说明书人机感过重，请改写为连贯自然段"
        )

    if is_post and prose_paragraphs:
        opening_window = " ".join(prose_paragraphs[:3])
        m_open = MACRO_OPENING_RE.search(opening_window)
        if m_open:
            errors.append(f"{path}: 开篇出现宏大叙事/导语套话「{m_open.group(0)}」，请第一句直接切入具体现象与数据")

        closing_window = " ".join(prose_paragraphs[-2:])
        m_close = PREACHY_ENDING_RE.search(closing_window)
        if m_close:
            errors.append(f"{path}: 结尾出现升华说教/求互动套话「{m_close.group(0)}」，讲完技术要点请直接收笔")

        anchors = extract_anchor_tokens(title_val, fm_block)
        if anchors and path.stem not in ("404-not-found", "502-bad-gateway", "connection-reset", "hello-world"):
            lower_open = (title_val_free := " ".join(prose_paragraphs[:4])).lower()
            if not any(tok.lower() in lower_open for tok in anchors):
                errors.append(
                    f"{path}: 开篇前四段未命中任何标题/标签核心引流词（候选: {anchors[:5]}），请确保开头保留核心搜索引流词"
                )

    if has_curly_quote and has_straight_quote:
        errors.append(f"{path}: 正文混用了中文弯引号 “...” 与直引号 \"...\"，请全文统一")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: check_ai_smell.py <file1.md> [file2.md ...]", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    checked = 0
    for arg in argv[1:]:
        p = Path(arg)
        if p.is_dir():
            for sub in sorted(p.rglob("*.md")):
                if not sub.name.startswith("auto-"):
                    checked += 1
                    all_errors.extend(check_file(sub))
        else:
            checked += 1
            all_errors.extend(check_file(p))

    if all_errors:
        print(f"检查 {checked} 个文件，发现 {len(all_errors)} 处规范问题：")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"OK ({checked} files checked, 0 issues)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
