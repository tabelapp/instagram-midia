"""Publica na Página do Tabelapp no Facebook os posts do calendario-facebook.json que já chegaram na hora marcada.

Usa a API oficial da Meta (Graph API, Páginas). Só biblioteca padrão do Python.
Reaproveita as mídias de midia/, as mesmas do Instagram.

Variáveis de ambiente:
  FB_PAGE_ID      ID da Página do Tabelapp
  FB_PAGE_TOKEN   token da Página com pages_manage_posts (NUNCA colocar no código)
  MIDIA_BASE_URL  endereço público da pasta midia/ (o mesmo do Instagram)

Nada é publicado enquanto "ativo" for false no calendario-facebook.json.

Uso:
  python ferramentas/publicar_facebook.py              publica o que estiver vencido
  python ferramentas/publicar_facebook.py --simular    só mostra o que faria, sem chamar a API
  python ferramentas/publicar_facebook.py --agora P07  publica um post específico já, ignorando a data
  python ferramentas/publicar_facebook.py --status     lista o estado de todos os posts
  python ferramentas/publicar_facebook.py --verificar  testa o token e a Página, sem publicar
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAL = RAIZ / "calendario-facebook.json"
CAL_IG = RAIZ / "calendario.json"
ESTADO = RAIZ / "estado-facebook.json"
MIDIA = RAIZ / "midia"
BASE = "https://graph.facebook.com/v25.0"
RUPLOAD = "https://rupload.facebook.com/video-upload/v25.0"
TOLERANCIA = timedelta(hours=12)  # post atrasado mais que isso não sai sozinho: avisa e espera decisão

def carregar_estado():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}

def salvar_estado(e):
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")

def _abrir(req, caminho):
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        raise RuntimeError(f"API {e.code} em {caminho}: {corpo}") from None

def api(metodo, caminho, params):
    params = dict(params, access_token=os.environ["FB_PAGE_TOKEN"])
    dados = urllib.parse.urlencode(params).encode()
    url = f"{BASE}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(url + "?" + dados.decode())
    else:
        req = urllib.request.Request(url, data=dados, method="POST")
    return _abrir(req, caminho)

def url_publica(pasta, arquivo):
    base = os.environ["MIDIA_BASE_URL"].rstrip("/") + "/"
    return base + urllib.parse.quote(f"{pasta}/{arquivo}")

def montar(post):
    """Devolve (pasta, legenda, arquivos) ou levanta erro se faltar mídia."""
    pasta, legenda = post["pasta"], post["legenda"]
    cal_ig = json.loads(CAL_IG.read_text(encoding="utf-8"))
    if cal_ig.get("usar_lancamento_disponivel") and "alternativa" in post:
        pasta, legenda = post["alternativa"]["pasta"], post["alternativa"]["legenda"]
    d = MIDIA / pasta
    if not d.is_dir():
        raise FileNotFoundError(f"{pasta}: não está em midia/ (mídia ainda não pronta)")
    arquivos = ["reel.mp4"] if post["tipo"] == "REELS" else sorted(p.name for p in d.glob("*.jpg"))
    for a in arquivos:
        if not (d / a).exists():
            raise FileNotFoundError(f"{pasta}/{a} não existe")
    if post["tipo"] == "IMAGE" and len(arquivos) != 1:
        raise ValueError(f"{pasta}: IMAGE precisa de 1 imagem, achei {len(arquivos)}")
    if post["tipo"] == "CAROUSEL" and not 2 <= len(arquivos) <= 10:
        raise ValueError(f"{pasta}: post com várias fotos precisa de 2 a 10 imagens, achei {len(arquivos)}")
    return pasta, legenda, arquivos

def link_post(obj_id):
    try:
        l = api("GET", obj_id, {"fields": "permalink_url"}).get("permalink_url", "")
    except RuntimeError:
        return ""
    return "https://www.facebook.com" + l if l.startswith("/") else l

def publicar_reel(pagina, url_video, legenda):
    vid = api("POST", f"{pagina}/video_reels", {"upload_phase": "start"})["video_id"]
    req = urllib.request.Request(f"{RUPLOAD}/{vid}", data=b"", method="POST", headers={
        "Authorization": f"OAuth {os.environ['FB_PAGE_TOKEN']}", "file_url": url_video})
    _abrir(req, f"rupload/{vid}")
    api("POST", f"{pagina}/video_reels", {"upload_phase": "finish", "video_id": vid,
                                          "video_state": "PUBLISHED", "description": legenda})
    t0 = time.time()
    while time.time() - t0 < 600:
        st = api("GET", vid, {"fields": "status"}).get("status", {})
        if st.get("video_status") == "error":
            raise RuntimeError(f"Reel {vid} falhou: {st}")
        if st.get("publishing_phase", {}).get("status") == "complete":
            return vid
        time.sleep(10)
    raise RuntimeError(f"Reel {vid} não terminou de publicar em 600 s (pode sair mais tarde; confira a Página)")

def publicar(post, simular):
    pasta, legenda, arquivos = montar(post)
    if simular:
        print(f"  [simulação] FB {post['id']} {post['tipo']} {pasta}: {len(arquivos)} arquivo(s); legenda {len(legenda)} caracteres")
        return "simulado"
    pagina = os.environ["FB_PAGE_ID"]
    urls = [url_publica(pasta, a) for a in arquivos]
    if post["tipo"] == "IMAGE":
        r = api("POST", f"{pagina}/photos", {"url": urls[0], "message": legenda, "published": "true"})
        pid = r.get("post_id") or r["id"]
    elif post["tipo"] == "CAROUSEL":
        fotos = [api("POST", f"{pagina}/photos", {"url": u, "published": "false"})["id"] for u in urls]
        params = {"message": legenda}
        for i, f in enumerate(fotos):
            params[f"attached_media[{i}]"] = json.dumps({"media_fbid": f})
        pid = api("POST", f"{pagina}/feed", params)["id"]
    elif post["tipo"] == "REELS":
        pid = publicar_reel(pagina, urls[0], legenda)
    else:
        raise ValueError(f"tipo desconhecido: {post['tipo']}")
    link = link_post(pid)
    print(f"  PUBLICADO FB {post['id']} -> {link or pid}")
    return {"post_id": pid, "link": link, "em": datetime.now(timezone.utc).isoformat()}

def main():
    args = sys.argv[1:]
    simular = "--simular" in args
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    estado = carregar_estado()
    agora = datetime.now(timezone.utc)

    if "--status" in args:
        print(f"Facebook {'ATIVO' if cal.get('ativo') else 'DESATIVADO (ativo=false)'}")
        for p in sorted(cal["posts"], key=lambda x: x["quando"]):
            q = datetime.fromisoformat(p["quando"])
            st = estado.get(p["id"])
            try:
                montar(p); midia_ok = "mídia ok"
            except Exception as e:
                midia_ok = f"PENDENTE: {e}"
            print(f"FB {p['id']}  {q:%d/%m %H:%M}  {p['tipo']:<8}  {'publicado ' + st['link'] if isinstance(st, dict) else midia_ok}")
        return

    if not simular and not (os.environ.get("FB_PAGE_ID") and os.environ.get("FB_PAGE_TOKEN")):
        print("Facebook não configurado (faltam FB_PAGE_ID/FB_PAGE_TOKEN). Nada a fazer.")
        return

    if "--verificar" in args:
        pg = api("GET", os.environ["FB_PAGE_ID"], {"fields": "name,link"})
        print(f"Conexão ok com a Página '{pg.get('name')}'. Nada foi publicado.")
        return

    if not cal.get("ativo") and not simular:
        print("Facebook desativado no calendario-facebook.json (ativo=false). Nada foi publicado.")
        return

    if "--agora" in args:
        alvo = args[args.index("--agora") + 1]
        posts = [p for p in cal["posts"] if p["id"] == alvo]
        if not posts:
            sys.exit(f"Post {alvo} não existe no calendário do Facebook")
        if alvo in estado and not simular:
            sys.exit(f"FB {alvo} já foi publicado: {estado[alvo]}")
        r = publicar(posts[0], simular)
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
            erros.append(f"FB {p['id']} atrasado desde {q:%d/%m %H:%M}: não publiquei sozinho. Use --agora {p['id']} se ainda fizer sentido.")
            continue
        try:
            r = publicar(p, simular)
            if not simular:
                estado[p["id"]] = r; salvar_estado(estado)
        except Exception as e:
            erros.append(f"FB {p['id']}: {e}")
    for e in erros:
        print("  AVISO:", e)
    if erros and not simular and any("API" in e for e in erros):
        sys.exit(1)

if __name__ == "__main__":
    main()
