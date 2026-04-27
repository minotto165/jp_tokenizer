"""
!!! VIBE-CODED !!!

日本語自然言語処理用コーパス収集スクリプト
========================================
ソース:
  1. 青空文庫 (aozora.gr.jp) - パブリックドメイン近代文学 ~20作品
  2. Wikipedia日本語版 API   - 各種記事 ~100件

使い方:
  python collect_japanese_corpus.py

出力:
  japanese_corpus.txt     -- 結合済みコーパス
  corpus_stats.txt        -- 収集統計

依存ライブラリ: 標準ライブラリのみ (Python 3.6+)
"""

import urllib.request
import urllib.parse
import urllib.error
import zipfile
import io
import re
import os
import sys
import json
import time
import datetime

# ─────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────
OUTPUT_FILE = "testdata/input.txt"
STATS_FILE  = "testdata/corpus_stats.txt"

# 青空文庫: リクエスト間隔（マナー）
AOZORA_SLEEP = 1.0
# Wikipedia API: リクエスト間隔
WIKI_SLEEP   = 0.5
# Wikipedia: 1回のAPIリクエストで取得する記事数
WIKI_BATCH   = 5

# ─────────────────────────────────────────────
# 青空文庫 作品リスト
#   (zip_url, タイトル表示名)
# ─────────────────────────────────────────────
AOZORA_WORKS = [
    # 夏目漱石
    ("https://www.aozora.gr.jp/cards/000148/files/789_ruby_5639.zip",  "吾輩は猫である（漱石）"),
    ("https://www.aozora.gr.jp/cards/000148/files/752_ruby_2438.zip",  "坊っちゃん（漱石）"),
    ("https://www.aozora.gr.jp/cards/000148/files/773_ruby_5968.zip",   "こころ（漱石）"),
    ("https://www.aozora.gr.jp/cards/000148/files/794_ruby_4237.zip",  "三四郎（漱石）"),
    ("https://www.aozora.gr.jp/cards/000148/files/1746_ruby_18324.zip",  "それから（漱石）"),
    # 芥川龍之介
    ("https://www.aozora.gr.jp/cards/000879/files/127_ruby_150.zip",   "羅生門（芥川）"),
    ("https://www.aozora.gr.jp/cards/000879/files/42_ruby_154.zip",   "鼻（芥川）"),
    ("https://www.aozora.gr.jp/cards/000879/files/55_ruby_1843.zip",   "芋粥（芥川）"),
    ("https://www.aozora.gr.jp/cards/000879/files/179_ruby_168.zip", "藪の中（芥川）"),
    ("https://www.aozora.gr.jp/cards/000879/files/45761_ruby_38235.zip",  "河童（芥川）"),
    ("https://www.aozora.gr.jp/cards/000879/files/60_ruby_821.zip", "地獄変（芥川）"),
    # 森鴎外
    ("https://www.aozora.gr.jp/cards/000129/files/58126_ruby_73643.zip",  "舞姫（鴎外）"),
    ("https://www.aozora.gr.jp/cards/000129/files/691_ruby_15351.zip","高瀬舟（鴎外）"),
    ("https://www.aozora.gr.jp/cards/000129/files/689_ruby_23256.zip",  "山椒大夫（鴎外）"),
    # 太宰治
    ("https://www.aozora.gr.jp/cards/000035/files/1567_ruby_4948.zip", "走れメロス（太宰）"),
    ("https://www.aozora.gr.jp/cards/000035/files/1565_ruby_8220.zip",  "斜陽（太宰）"),
    ("https://www.aozora.gr.jp/cards/000035/files/301_ruby_5915.zip",  "人間失格（太宰）"),
    # 宮沢賢治
    ("https://www.aozora.gr.jp/cards/000081/files/456_ruby_145.zip",  "銀河鉄道の夜（賢治）"),
    ("https://www.aozora.gr.jp/cards/000081/files/462_ruby_716.zip",  "風の又三郎（賢治）"),
    ("https://www.aozora.gr.jp/cards/000081/files/43737_ruby_19028.zip","注文の多い料理店（賢治）"),
    # 樋口一葉
    ("https://www.aozora.gr.jp/cards/000064/files/389_ruby_15296.zip",  "たけくらべ（一葉）"),
    ("https://www.aozora.gr.jp/cards/000064/files/387_ruby_15292.zip",  "にごりえ（一葉）"),
    # 島崎藤村
    ("https://www.aozora.gr.jp/cards/000158/files/1502_ruby_24534.zip", "破戒（藤村）"),
    # 志賀直哉
    ("https://www.aozora.gr.jp/cards/000083/files/1388_ruby_17236.zip", "暗夜行路（志賀）"),
    # 幸田露伴
    ("https://www.aozora.gr.jp/cards/000051/files/43289_ruby_16762.zip",  "五重塔（露伴）"),
]

# ─────────────────────────────────────────────
# Wikipedia: 取得するカテゴリ・記事タイトルリスト
# ─────────────────────────────────────────────
WIKI_TITLES = [
    # 日本史
    "江戸時代", "明治維新", "大正時代", "昭和時代", "平安時代", "鎌倉時代",
    "室町時代", "戦国時代_(日本)", "江戸幕府", "徳川家康", "豊臣秀吉",
    "織田信長", "坂本龍馬", "西郷隆盛", "伊藤博文", "福沢諭吉",
    "聖徳太子", "源頼朝", "足利尊氏", "北条時宗", "上杉謙信", "武田信玄",
    # 地理・都市
    "東京都", "大阪府", "京都府", "北海道", "沖縄県", "富士山",
    "琵琶湖", "瀬戸内海", "日本アルプス", "本州", "四国", "九州",
    "東海道", "中山道", "奥州街道", "長崎街道",
    # 文化・芸術
    "能楽", "歌舞伎", "文楽", "茶道", "華道", "書道", "俳句",
    "和歌", "短歌", "連歌", "狂言", "落語", "講談", "浪曲",
    "日本画", "浮世絵", "蒔絵", "陶磁器", "漆器",
    "日本建築", "神社建築", "寺院建築", "城郭",
    # 科学・技術
    "量子力学", "相対性理論", "進化論", "DNA", "光合成",
    "人工知能", "機械学習", "深層学習", "自然言語処理",
    "インターネット", "半導体", "新幹線", "リニアモーターカー",
    "宇宙開発", "国際宇宙ステーション", "ブラックホール",
    # 文学・思想
    "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "三島由紀夫",
    "松尾芭蕉", "与謝野晶子", "正岡子規", "石川啄木",
    "儒教", "仏教", "神道", "禅", "武士道",
    # 社会・政治
    "日本国憲法", "民主主義", "国会_(日本)", "内閣総理大臣",
    "日本の経済", "高度経済成長", "バブル景気", "少子高齢化",
    "社会保障", "環境問題", "地球温暖化", "再生可能エネルギー",
    # 自然・生物
    "桜", "竹", "松", "梅", "菊", "蓮",
    "タヌキ", "キツネ", "ニホンザル", "ツル", "カラス",
    "日本海", "太平洋", "地震", "台風", "津波", "火山",
    # スポーツ・娯楽
    "相撲", "柔道", "剣道", "空手", "弓道", "合気道",
    "野球", "サッカー", "バスケットボール",
    "将棋", "囲碁", "花札", "かるた",
    # 食文化
    "日本料理", "寿司", "天ぷら", "そば", "うどん", "ラーメン",
    "味噌", "醤油", "豆腐", "納豆", "日本酒", "緑茶",
    # 現代文化
    "アニメ", "漫画", "ゲーム", "ラノベ", "ボカロ",
    "東京ディズニーリゾート", "秋葉原", "渋谷", "新宿",
]


# ─────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────
def log(msg):
    print(msg, flush=True)

def fetch_bytes(url, timeout=30):
    headers = {"User-Agent": "JapaneseCorpusCollector/1.0 (educational use)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_text(url, encoding="utf-8", timeout=30):
    return fetch_bytes(url, timeout).decode(encoding, errors="replace")


# ─────────────────────────────────────────────
# 青空文庫
# ─────────────────────────────────────────────
def fetch_aozora(zip_url):
    data = fetch_bytes(zip_url)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        txt_files = [n for n in z.namelist() if n.endswith(".txt")]
        if not txt_files:
            return ""
        raw = z.read(txt_files[0])
        return raw.decode("shift_jis", errors="replace")

def clean_aozora(text):
    # ヘッダ除去（区切り線まで）
    text = re.sub(r'^.*?-{50,}', '', text, count=1, flags=re.DOTALL)
    # フッタ除去
    text = re.sub(r'底本：.*$', '', text, flags=re.DOTALL)
    # ルビ《》除去
    text = re.sub(r'《[^》]*》', '', text)
    # ［＃注記］除去
    text = re.sub(r'［＃[^］]*］', '', text)
    # ルビ開始記号
    text = text.replace('|', '')
    # ※行除去
    text = re.sub(r'※[^\n]*\n', '', text)
    # 連続空行圧縮
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def collect_aozora():
    log("\n【青空文庫】収集開始")
    log(f"{'作品名':<30} {'文字数':>10} {'状態'}")
    log("-" * 55)

    results = []
    for url, title in AOZORA_WORKS:
        try:
            raw = fetch_aozora(url)
            text = clean_aozora(raw)
            n = len(text)
            results.append({"title": title, "text": text, "chars": n, "ok": True})
            log(f"{title:<30} {n:>10,}  ✓")
        except Exception as e:
            results.append({"title": title, "text": "", "chars": 0, "ok": False, "error": str(e)})
            log(f"{title:<30} {'---':>10}  ✗  {e}")
        time.sleep(AOZORA_SLEEP)

    ok = [r for r in results if r["ok"]]
    log(f"\n青空文庫: {len(ok)}/{len(AOZORA_WORKS)} 作品取得, "
        f"合計 {sum(r['chars'] for r in ok):,} 文字")
    return results


# ─────────────────────────────────────────────
# Wikipedia日本語版
# ─────────────────────────────────────────────
WIKI_API = "https://ja.wikipedia.org/w/api.php"

def fetch_wiki_batch(titles):
    """複数タイトルを1リクエストで取得"""
    params = {
        "action":          "query",
        "format":          "json",
        "prop":            "extracts",
        "explaintext":     "1",
        "exsectionformat": "plain",
        "titles":          "|".join(titles),
    }
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    data = json.loads(fetch_text(url))
    pages = data["query"]["pages"]
    results = {}
    for page in pages.values():
        title  = page.get("title", "")
        extract = page.get("extract", "")
        if extract and not page.get("missing"):
            results[title] = extract
    return results

def clean_wiki(text):
    # セクション見出し（== ... ==）を削除
    text = re.sub(r'={2,}[^=]+={2,}', '', text)
    # 連続空行圧縮
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def collect_wikipedia():
    log("\n【Wikipedia日本語版】収集開始")
    log(f"対象記事数: {len(WIKI_TITLES)} 件")
    log("-" * 55)

    results = []
    # バッチに分割
    batches = [WIKI_TITLES[i:i+WIKI_BATCH] for i in range(0, len(WIKI_TITLES), WIKI_BATCH)]

    for batch_idx, batch in enumerate(batches):
        try:
            pages = fetch_wiki_batch(batch)
            for title, text in pages.items():
                cleaned = clean_wiki(text)
                n = len(cleaned)
                results.append({"title": title, "text": cleaned, "chars": n, "ok": True})
                log(f"  [{batch_idx*WIKI_BATCH + len(results):>3}] {title:<28} {n:>8,} 文字")
        except Exception as e:
            log(f"  バッチ {batch_idx+1} エラー: {e}")
            for title in batch:
                results.append({"title": title, "text": "", "chars": 0, "ok": False, "error": str(e)})
        time.sleep(WIKI_SLEEP)

    ok = [r for r in results if r["ok"]]
    log(f"\nWikipedia: {len(ok)}/{len(WIKI_TITLES)} 記事取得, "
        f"合計 {sum(r['chars'] for r in ok):,} 文字")
    return results


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────
def main():
    log("=" * 60)
    log("日本語コーパス収集スクリプト")
    log(f"開始: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    # ── 収集 ──
    aozora_results = collect_aozora()
    wiki_results   = collect_wikipedia()

    all_results = aozora_results + wiki_results
    ok_results  = [r for r in all_results if r["ok"]]
    total_chars = sum(r["chars"] for r in ok_results)

    # ── コーパスファイル出力 ──
    log(f"\n【出力】{OUTPUT_FILE}")

    header = (
        f"# 日本語自然言語処理用コーパス\n"
        f"# 収集日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"# ソース: 青空文庫 (パブリックドメイン) + Wikipedia日本語版 (CC BY-SA 3.0)\n"
        f"# 総文字数: {total_chars:,} 文字\n"
        f"# 収録数: {len(ok_results)} 件\n"
        f"{'#' * 60}\n\n"
    )

    sections = []
    for r in ok_results:
        sep = "=" * 60
        sections.append(f"\n\n{sep}\n■ {r['title']}\n{sep}\n\n{r['text']}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(header + "".join(sections))

    log(f"  → {total_chars:,} 文字 を書き込みました")

    # ── 統計ファイル出力 ──
    # with open(STATS_FILE, "w", encoding="utf-8") as f:
    #     f.write(f"収集統計レポート\n")
    #     f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    #     f.write("=" * 50 + "\n\n")

    #     f.write("【青空文庫】\n")
    #     for r in aozora_results:
    #         mark = "✓" if r["ok"] else "✗"
    #         err  = f"  ({r.get('error','')})" if not r["ok"] else ""
    #         f.write(f"  {mark} {r['title']:<30} {r['chars']:>10,} 文字{err}\n")

    #     f.write("\n【Wikipedia】\n")
    #     for r in wiki_results:
    #         mark = "✓" if r["ok"] else "✗"
    #         err  = f"  ({r.get('error','')})" if not r["ok"] else ""
    #         f.write(f"  {mark} {r['title']:<30} {r['chars']:>10,} 文字{err}\n")

    #     f.write("\n" + "=" * 50 + "\n")
    #     f.write(f"合計: {total_chars:,} 文字 / {len(ok_results)} 件\n")

    # ── サマリ表示 ──
    log("\n" + "=" * 60)
    log("収集完了サマリ")
    log("=" * 60)
    aok = [r for r in aozora_results if r["ok"]]
    wok = [r for r in wiki_results   if r["ok"]]
    log(f"  青空文庫 : {len(aok):>3} 作品  {sum(r['chars'] for r in aok):>10,} 文字")
    log(f"  Wikipedia: {len(wok):>3} 記事  {sum(r['chars'] for r in wok):>10,} 文字")
    log(f"  合計     :          {total_chars:>10,} 文字")
    log(f"\n出力ファイル:")
    log(f"  {OUTPUT_FILE}  ({os.path.getsize(OUTPUT_FILE):,} bytes)")
    log(f"  {STATS_FILE}")
    log(f"\n終了: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()