#!/usr/bin/env python3
"""Lê o feed público do canal do MamyCast no YouTube e grava os últimos
episódios (sem Shorts) em episodios.json. Rodado pelo GitHub Actions."""
import json, re, sys, urllib.request, urllib.error, html, pathlib

CANAL_ID = "UCXn7N4rmJ1Obw5rce2k72WA"  # youtube.com/@mamycast
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CANAL_ID}"
MAX = 6
SAIDA = pathlib.Path(__file__).resolve().parent.parent / "episodios.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; mamycast-links-bot)"}


def baixar(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8")


class SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def eh_short(vid):
    """youtube.com/shorts/ID devolve 200 para Short e redireciona (303) para vídeo normal."""
    op = urllib.request.build_opener(SemRedirect)
    try:
        r = op.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers=UA), timeout=20)
        return r.status == 200
    except urllib.error.HTTPError as e:
        return e.code == 200


def limpar(t):
    t = html.unescape(t).strip()
    t = re.sub(r"\s*\|\s*MamyCast\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*#\w+", "", t).strip()
    return t.rstrip(".").strip()


def main():
    xml = baixar(FEED)
    eps = []
    for e in re.findall(r"<entry>.*?</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>(.*?)<", e).group(1)
        pub = re.search(r"<published>(.*?)<", e).group(1)
        titulo = limpar(re.search(r"<title>(.*?)</title>", e, re.S).group(1))
        if eh_short(vid):
            continue
        eps.append({"id": vid, "titulo": titulo, "publicado": pub})
        if len(eps) >= MAX:
            break
    if not eps:
        sys.exit("Nenhum episódio encontrado; mantendo o arquivo atual.")
    novo = json.dumps({"canal": f"https://www.youtube.com/channel/{CANAL_ID}", "episodios": eps}, ensure_ascii=False, indent=2) + "\n"
    antigo = SAIDA.read_text(encoding="utf-8") if SAIDA.exists() else ""
    if novo != antigo:
        SAIDA.write_text(novo, encoding="utf-8")
        print("episodios.json atualizado:", [e["titulo"] for e in eps])
    else:
        print("Sem novidades.")


if __name__ == "__main__":
    main()
