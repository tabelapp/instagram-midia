"""Publica no Instagram os posts do calendario.json que já chegaram na hora marcada.

Usa a API oficial do Instagram (Instagram API with Instagram Login). Só biblioteca padrão do Python.

Variáveis de ambiente:
  IG_ACCESS_TOKEN  token de longa duração da conta @tabelapp.economia (NUNCA colocar no código)
  IG_USER_ID       ID da conta profissional do Instagram
  MIDIA_BASE_URL   endereço público da pasta midia/, ex.: https://tabelapp.github.io/instagram-midia/midia/
  IG_API_BASE      opcional, padrão https://graph.instagram.com/v25.0

Uso:
  python ferramentas/publicar.py              publica o que estiver vencido
  python ferramentas/publicar.py --simular    só mostra o que faria, sem chamar a API
  python ferramentas/publicar.py --agora P07  publica um post específico já, ignorando a data
  python ferramentas/publicar.py --status     lista o estado de todos os posts
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAL = RAIZ / "calendario.json"
ESTADO = RAIZ / "estado.json"
MIDIA = RAIZ / "midia"
TOLERANCIA = timedelta(hours=12)  # post atrasado mais que isso não sai sozinho: avisa e espera decisão

def carregar_estado():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}

def salvar_estado(e):
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")

def api(metodo, caminho, params):
    base = os.environ.get("IG_API_BASE", "https://graph.instagram.com/v25.0").rstrip("/")
    params = dict(params, access_token=os.environ["IG_ACCESS_TOKEN"])
    dados = urllib.parse.urlencode(params).encode()
    url = f"{base}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(url + "?" + dados.decode())
    else:
        req = urllib.request.Request(url, data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        raise RuntimeError(f"API {e.code} em {caminho}: {corpo}") from None

def esperar_pronto(container, limite=600):
    t0 = time.time()
    while time.time() - t0 < limite:
        st = api("GET", container, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Contêiner {container} falhou: {st}")
        time.sleep(10)
    raise RuntimeError(f"Contêiner {container} não ficou pronto em {limite} s")

def url_publica(pasta, arquivo):
    base = os.environ["MIDIA_BASE_URL"].rstrip("/") + "/"
    return base + urllib.parse.quote(f"{pasta}/{arquivo}")

def montar(post, cal):
    """Devolve (pasta, legenda, arquivos) ou levanta erro se faltar mídia."""
    pasta, legenda = post["pasta"], post["legenda"]
    if cal.get("usar_lancamento_disponivel") and "alternativa" in post:
        pasta, legenda = post["alternativa"]["pasta"], post["alternativa"]["legenda"]
    d = MIDIA / pasta
    if not d.is_dir():
        raise FileNotFoundError(f"{pasta}: não está em midia/ (falta preencher dados reais e rodar gerar.py?)")
    if post["tipo"] == "REELS":
        arquivos = ["reel.mp4", "capa.jpg"]
    else:
        arquivos = sorted(p.name for p in d.glob("*.jpg"))
    for a in arquivos:
        if not (d / a).exists():
            raise FileNotFoundError(f"{pasta}/{a} não existe")
    if post["tipo"] == "IMAGE" and len(arquivos) != 1:
        raise ValueError(f"{pasta}: IMAGE precisa de 1 imagem, achei {len(arquivos)}")
    if post["tipo"] == "CAROUSEL" and not 2 <= len(arquivos) <= 10:
        raise ValueError(f"{pasta}: carrossel precisa de 2 a 10 imagens, achei {len(arquivos)}")
    return pasta, legenda, arquivos

def publicar(post, cal, simular):
    pasta, legenda, arquivos = montar(post, cal)
    uid = os.environ.get("IG_USER_ID", "<IG_USER_ID>")
    urls = [url_publica(pasta, a) for a in arquivos] if not simular or os.environ.get("MIDIA_BASE_URL") else arquivos
    if simular:
        print(f"  [simulação] {post['id']} {post['tipo']} {pasta}: {len(arquivos)} arquivo(s); legenda {len(legenda)} caracteres")
        return "simulado"
    if post["tipo"] == "IMAGE":
        c = api("POST", f"{uid}/media", {"image_url": urls[0], "caption": legenda})["id"]
    elif post["tipo"] == "CAROUSEL":
        filhos = []
        for u in urls:
            filhos.append(api("POST", f"{uid}/media", {"image_url": u, "is_carousel_item": "true"})["id"])
        for f in filhos:
            esperar_pronto(f, 180)
        c = api("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": legenda})["id"]
    elif post["tipo"] == "REELS":
        c = api("POST", f"{uid}/media", {"media_type": "REELS", "video_url": urls[0], "cover_url": urls[1],
                                          "caption": legenda, "share_to_feed": "true"})["id"]
    else:
        raise ValueError(f"tipo desconhecido: {post['tipo']}")
    esperar_pronto(c)
    mid = api("POST", f"{uid}/media_publish", {"creation_id": c})["id"]
    link = api("GET", mid, {"fields": "permalink"}).get("permalink", "")
    print(f"  PUBLICADO {post['id']} -> {link}")
    return {"media_id": mid, "link": link, "em": datetime.now(timezone.utc).isoformat()}

def main():
    args = sys.argv[1:]
    simular = "--simular" in args
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    estado = carregar_estado()
    agora = datetime.now(timezone.utc)

    if "--status" in args:
        for p in cal["posts"]:
            q = datetime.fromisoformat(p["quando"])
            st = estado.get(p["id"])
            try:
                montar(p, cal); midia_ok = "mídia ok"
            except Exception as e:
                midia_ok = f"PENDENTE: {e}"
            print(f"{p['id']}  {q:%d/%m %H:%M}  {p['tipo']:<8}  {'publicado ' + st['link'] if isinstance(st, dict) else midia_ok}")
        return

    if "--agora" in args:
        alvo = args[args.index("--agora") + 1]
        posts = [p for p in cal["posts"] if p["id"] == alvo]
        if not posts:
            sys.exit(f"Post {alvo} não existe no calendário")
        if alvo in estado and not simular:
            sys.exit(f"{alvo} já foi publicado: {estado[alvo]}")
        r = publicar(posts[0], cal, simular)
        if not simular:
            estado[alvo] = r; salvar_estado(estado)
        return

    erros = []
    for p in sorted(cal["posts"], key=lambda x: x["quando"]):
        if p["id"] in estado:
            continue
        q = datetime.fromisoformat(p["quando"])
        if q > agora and not simular:
            continue
        if agora - q > TOLERANCIA and not simular:
            erros.append(f"{p['id']} atrasado desde {q:%d/%m %H:%M}: não publiquei sozinho. Use --agora {p['id']} se ainda fizer sentido.")
            continue
        try:
            r = publicar(p, cal, simular)
            if not simular:
                estado[p["id"]] = r; salvar_estado(estado)
        except Exception as e:
            erros.append(f"{p['id']}: {e}")
    for e in erros:
        print("  AVISO:", e)
    if erros and not simular and any("API" in e for e in erros):
        sys.exit(1)

if __name__ == "__main__":
    main()
