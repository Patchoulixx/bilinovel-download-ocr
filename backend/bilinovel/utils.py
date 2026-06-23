from backend.rubbish_secret_map import rubbish_secret_map, blank_list
from bs4 import BeautifulSoup
import re

# ═══════════════════════════════════════════════════════════════════
# LCG + Fisher-Yates 反洗牌 — 还原网站对段落的重排
# ═══════════════════════════════════════════════════════════════════
# 网站反扒机制：对 TextContent 中第 20 个及以后的非空 <p> 段落，
# 使用 LCG (a=9302, c=49397, m=233280) 生成随机序列执行 Fisher-Yates 洗牌。
# 种子 = chapterId × 126 + 232

_LCG_A = 9302
_LCG_C = 49397
_LCG_M = 233280


def unshuffle_paragraphs(shuffled_list, chapter_id):
    """
    逆向 Fisher-Yates 洗牌，还原被网站打乱的段落顺序。

    正向洗牌 (网站):
      for i from n-1 down to 1:
          j = random(0, i)
          swap(arr[i], arr[j])

    逆向恢复：
      1. 用相同 LCG 序列正向生成所有 j 值
      2. 从 i=1 到 n-1 依次反向 swap(arr[i], arr[j])

    Args:
        shuffled_list: 乱序后的列表（任意类型元素）
        chapter_id:   章节 ID（整数）

    Returns:
        恢复原始顺序后的新列表
    """
    n = len(shuffled_list)
    if n <= 1:
        return shuffled_list[:]

    result = list(shuffled_list)
    seed = (chapter_id * 126 + 232) % _LCG_M
    state = seed

    # Pass 1: 以正向顺序生成所有的 j 值（与网站洗牌时的顺序一致）
    j_values = [0] * n
    for i in range(n - 1, 0, -1):
        state = (state * _LCG_A + _LCG_C) % _LCG_M
        j_values[i] = int((state / _LCG_M) * (i + 1))

    # Pass 2: 反向执行 swap 还原（i 从小到大）
    for i in range(1, n):
        j = j_values[i]
        result[i], result[j] = result[j], result[i]

    return result


def extract_chapter_id(url):
    """
    从章节 URL 中提取 chapter ID。

    例如: https://www.linovelib.com/novel/1234/5678.html → 5678
    """
    m = re.search(r'/(\d+)\.html', url)
    return int(m.group(1)) if m else None

def get_container_html():
    text_html = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>"""
    return text_html

def get_cover_html(img_w, img_h):
    text_html = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Cover</title>
</head>
<body>
  <div style="text-align: center; padding: 0pt; margin: 0pt;">
    <svg xmlns="http://www.w3.org/2000/svg" height="100%" preserveAspectRatio="xMidYMid meet" version="1.1" viewBox="0 0 {img_w} {img_h}" width="100%" xmlns:xlink="http://www.w3.org/1999/xlink">
      <image width="{img_w}" height="{img_h}" xlink:href="../Images/00.jpg"/>
    </svg>
  </div>
</body>
</html>"""
    return text_html

def text2htmls(chap_name, text):
    text_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<!--?xml version="1.0" encoding="UTF-8" standalone="no"?--><html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chap_name}</title>
    <style>p {{ text-indent: 2em; }}</style>
</head>
<body>
<h1>{chap_name}</h1>
{text}
</body>
</html>"""
    return text_html

def get_toc_html(title, chap_names):
    toc_html_template = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
   "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">

<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:a18aac05-497d-476d-b66f-0211f609743d" />
    <meta name="dtb:depth" content="0" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle>
    <text>{title}</text>
  </docTitle>
  <navMap>
{nav_points}
  </navMap>
</ncx>"""
    nav_point_template = """    <navPoint id="navPoint-{nav_id}" playOrder="{play_order}">
    <navLabel>
        <text>{chap_name}</text>
    </navLabel>
    <content src="Text/{chap_no}.xhtml"/>
    </navPoint>"""
    nav_points = '\n'.join(
        nav_point_template.format(nav_id=i+1, play_order=i+1, chap_name=chap_name, chap_no=str(i).zfill(2))
        for i, chap_name in enumerate(chap_names)
    )
    return toc_html_template.format(title=title, nav_points=nav_points)



def get_content_html(book_name, volume_name, volume_no, author, publisher, brief, tag_list, num_chap, num_img, img_exist=False):
    content_html_template = """<?xml version="1.0" encoding="utf-8"?>
<package version="2.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>zh-CN</dc:language>
    <meta name="calibre:series" content="{series_name}" />
    <meta name="calibre:series_index" content="{series_no}"/>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:publisher>{publisher}</dc:publisher>
    <dc:description>{brief}</dc:description>
{subjects}
    <meta name="cover" content="x00.jpg"/>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="cover.xhtml" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
{xcolor}
{chapters}
{images}
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover.xhtml"/>
{spine_xcolor}
{spine_chapters}
  </spine>
  <guide>
    <reference type="cover" title="封面" href="Text/cover.xhtml"/>
  </guide>
</package>"""

    subjects = '\n'.join(f'    <dc:subject>{tag}</dc:subject>' for tag in tag_list)
    chapters = '\n'.join(
        f'    <item id="x{str(chap_no).zfill(2)}.xhtml" href="Text/{str(chap_no).zfill(2)}.xhtml" media-type="application/xhtml+xml"/>'
        for chap_no in range(num_chap)
    )
    images = '\n'.join(
        f'    <item id="x{str(img_no).zfill(2)}.jpg" href="Images/{str(img_no).zfill(2)}.jpg" media-type="image/jpeg"/>'
        for img_no in range(num_img)
    )
    spine_chapters = '\n'.join(
        f'    <itemref idref="x{str(chap_no).zfill(2)}.xhtml"/>'
        for chap_no in range(num_chap)
    )

    xcolor = '    <item id="xcolor" href="Text/color.xhtml" media-type="application/xhtml+xml"/>\n' if img_exist else ''
    spine_xcolor = '    <itemref idref="xcolor"/>\n' if img_exist else ''

    return content_html_template.format(
        series_name=book_name,
        series_no = volume_no,
        title=book_name+'-'+volume_name,
        author=author,
        publisher=publisher,
        brief = brief,
        subjects=subjects,
        chapters=chapters,
        images=images,
        xcolor=xcolor,
        spine_xcolor=spine_xcolor,
        spine_chapters=spine_chapters
    )

def check_chars(win_chars):
    win_illegal_chars = '?*"<>|:/'
    new_chars = ''
    for char in win_chars:
        if char in win_illegal_chars:
            new_chars += '\u25A0'
        else:
            new_chars += char
    return new_chars

# def replace_rubbish_text(content_html):
#     soup = BeautifulSoup(content_html, 'html.parser')
#     ps = soup.find_all('p')
#     if not ps:
#         return str(soup)
#     last_p = ps[-1]
#     text = last_p.get_text()
#     sb = []
#     for blank_char in text:
#         # if blank_char in blank_list:
#         #     continue
#         replacement = rubbish_secret_map.get(blank_char)
#         t = replacement if replacement else blank_char
#         sb.append(t)
#     last_p.string = ''.join(sb)
#     return str(soup)

chinese_punctuation = "，。！？、；：“”‘’（）《》〈〉【】『』〖〗…—～＋－＝×÷·—‘’“”『』【】（）《》〈〉「」『』〖〗〘〙〚〛〚〛〘〙〖〗〘〙〚〛〘〙〖〗〘〙"

def replace_rubbish_text(content_html):
    soup = BeautifulSoup(content_html, 'html.parser')
    ps = soup.find_all('p')
    if not ps:
        return str(soup)

    for i in range(-1, max(-len(ps) - 1, -10), -1):
      last_p = ps[i]
      text = last_p.get_text()
      if text != '':
          break
    sb = []
    for blank_char in text:
        replace_strr = rubbish_secret_map.get(blank_char)
        if replace_strr is not None:
            sb.append(replace_strr)
        elif blank_char in chinese_punctuation:
            sb.append(blank_char)
    last_p.string = ''.join(sb)
    return str(soup)