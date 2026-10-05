"""Busca fotos e vídeos de uso livre no Wikimedia Commons, só com licença que permite uso com crédito.

    python busca_commons.py lista "Viaturas PMERJ" "filetype:video TV ALERJ" ...
        → imprime largura x altura | licença | autor | título, e guarda em busca.json
    python busca_commons.py baixa <pasta_img> "File:Viaturas PMERJ 7.jpg" ...
        → baixa em 2400 px de largura (miniatura do Commons) e acrescenta o crédito em <pasta_img>/creditos.json

Aceita: domínio público, CC0, CC BY (qualquer versão). Recusa SA (obriga a licenciar o vídeo inteiro igual),
ND (proíbe editar) e NC. Fotos do Governo do RJ ("Carlos Magno / Governo do Rio de Janeiro") e da Agência Brasil
costumam vir em CC BY; vídeos da TV Alerj, CanalGov, STJ e Prefeitura de Santos, em CC BY 3.0.
O Commons limita requisições (429): o script espera e tenta de novo; não acelere.
Vídeo: baixe o original pelo "url" do busca.json (ou a versão transcodificada .720p.vp9.webm) e corte o
trecho com preparar.py apoio. Evite trecho com rosto de pessoa em destaque, político, operação policial ou
caso criminal real; prefira prédios, viaturas, multidão de longe, mãos, documentos.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "SilvaPintoAdvocacia/1.0 (https://silvapintoadvocacia.com) python-urllib"}
OK = re.compile(r"^(public domain|cc0|cc by(?!-sa|-nd|-nc)[ \d.a-z]*)$", re.I)
API = "https://commons.wikimedia.org/w/api.php?"


def _get(u):
    for k in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(20 * (k + 1))
    raise SystemExit("o Commons continuou recusando (429); tente mais tarde")


def lista(termos):
    res = {}
    for termo in termos:
        p = {"action": "query", "generator": "search", "gsrsearch": termo, "gsrnamespace": 6, "gsrlimit": 30,
             "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "format": "json",
             "iiextmetadatafilter": "LicenseShortName|Artist"}
        d = json.loads(_get(API + urllib.parse.urlencode(p)))
        out = []
        for pg in (d.get("query", {}).get("pages", {}) or {}).values():
            ii = pg["imageinfo"][0]
            m = ii.get("extmetadata", {})
            lic = m.get("LicenseShortName", {}).get("value", "?").strip()
            if not OK.match(lic) or (ii["width"] < 1600 and not ii["mime"].startswith("video")):
                continue
            autor = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip()[:80]
            out.append(dict(t=pg["title"], lic=lic, autor=autor, w=ii["width"], h=ii["height"], mime=ii["mime"],
                            url=ii["url"].split("?")[0], page=ii["descriptionurl"]))
        res[termo] = out
        print("==", termo, len(out))
        for x in out:
            print(f'  {x["w"]}x{x["h"]} | {x["lic"]} | {x["autor"][:30]} | {x["t"][5:90]}')
        time.sleep(6)
    json.dump(res, open("busca.json", "w"), ensure_ascii=False, indent=1)


def baixa(pasta, titulos):
    os.makedirs(pasta, exist_ok=True)
    p = {"action": "query", "titles": "|".join(titulos), "prop": "imageinfo", "iiprop": "url|extmetadata",
         "iiurlwidth": 2400, "format": "json", "iiextmetadatafilter": "LicenseShortName|Artist"}
    d = json.loads(_get(API + urllib.parse.urlencode(p)))
    cred_p = os.path.join(pasta, "creditos.json")
    cred = json.load(open(cred_p)) if os.path.exists(cred_p) else {}
    for pg in d["query"]["pages"].values():
        ii = pg["imageinfo"][0]
        m = ii["extmetadata"]
        lic = m["LicenseShortName"]["value"].strip()
        if not OK.match(lic):
            print("recusada (licença):", pg["title"], lic)
            continue
        nome = re.sub(r"[^a-z0-9]+", "_", pg["title"][5:].lower()).strip("_")[:50]
        nome = nome.rsplit("_", 1)[0] + "." + ("png" if pg["title"].lower().endswith(".png") else "jpg")
        time.sleep(4)
        open(os.path.join(pasta, nome), "wb").write(_get(ii["thumburl"]))
        autor = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip()
        cred[nome] = dict(titulo=pg["title"], licenca=lic, autor=autor, pagina=ii["descriptionurl"],
                          credito_na_tela=f"Foto: {autor} · {lic}")
        print(nome, "·", lic, "·", autor[:60])
    json.dump(cred, open(cred_p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "lista":
        lista(sys.argv[2:])
    elif sys.argv[1] == "baixa":
        baixa(sys.argv[2], sys.argv[3:])
