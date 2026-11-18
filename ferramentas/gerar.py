"""Gera todas as artes, Reels, stories e destaques do Instagram do Tabelapp.

Uso:  python ferramentas/gerar.py          (na pasta raiz do kit)
Requer: Python 3.9+, playwright (pip install playwright && playwright install chromium), ffmpeg.

Saídas:
  midia/      -> arquivos prontos para publicar (só entram aqui posts com dados completos)
  previa/     -> modelos que ainda dependem de dados reais (marca d'água MODELO)
  perfil/     -> foto de perfil e capas de destaques
  stories/    -> modelos de Stories
"""
import json, shutil, subprocess, sys, html
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
FERR = RAIZ / "ferramentas"
BASE = FERR / "base"
FONTES = FERR / "fontes"
DADOS = RAIZ / "dados"
MIDIA, PREVIA, PERFIL, STORIES = RAIZ / "midia", RAIZ / "previa", RAIZ / "perfil", RAIZ / "stories"

AMARELO, PRETO, VERMELHO, CREME = "#FDDE03", "#141414", "#B10000", "#FAF7EA"
HANDLE = "@tabelapp.economia"
LOGO = (BASE / "logo.png").as_uri()

TEMAS = {
    "amarelo": (AMARELO, PRETO, PRETO, "#3A3300"),
    "preto": (PRETO, "#FFFFFF", AMARELO, "#C8C8C8"),
    "branco": ("#FFFFFF", PRETO, VERMELHO, "#555555"),
    "creme": (CREME, PRETO, VERMELHO, "#555555"),
}

def esc(t):
    return html.escape(str(t)).replace("\n", "<br>")

def css(w, h):
    f = FONTES.as_uri()
    return f"""
@font-face{{font-family:Inter;src:url({f}/Inter-Regular.otf);font-weight:400}}
@font-face{{font-family:Inter;src:url({f}/Inter-SemiBold.otf);font-weight:600}}
@font-face{{font-family:Inter;src:url({f}/Inter-Bold.otf);font-weight:700}}
@font-face{{font-family:Disp;src:url({f}/InterDisplay-Bold.otf);font-weight:700}}
@font-face{{font-family:Disp;src:url({f}/InterDisplay-ExtraBold.otf);font-weight:800}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{w}px;height:{h}px;font-family:Inter,sans-serif;overflow:hidden}}
.pg{{width:{w}px;height:{h}px;padding:80px;display:flex;flex-direction:column;position:relative}}
.top{{width:100%;display:flex;align-items:center;justify-content:space-between}}
.marca{{display:flex;align-items:center;gap:16px;font-weight:700;font-size:30px}}
.marca img{{width:60px;height:60px;border-radius:14px}}
.num{{font-weight:600;font-size:28px;opacity:.75}}
.kick{{font-family:Disp;font-weight:700;font-size:30px;letter-spacing:6px;text-transform:uppercase}}
.tit{{font-family:Disp;font-weight:800;letter-spacing:-3px;line-height:1.0}}
.corpo{{font-size:40px;line-height:1.35;font-weight:600}}
.rod{{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-weight:600;font-size:28px}}
.selo{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-18deg);font-family:Disp;font-weight:800;font-size:200px;color:rgba(177,0,0,.22);letter-spacing:10px}}
"""

def doc(w, h, corpo):
    return f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{css(w,h)}</style></head><body>{corpo}</body></html>'

def topo(cor, num=None):
    n = f'<span class="num">{num}</span>' if num else ""
    return f'<div class="top"><div class="marca" style="color:{cor}"><img src="{LOGO}" alt=""><span>{HANDLE}</span></div>{n}</div>'

def rodape(cor, dir_txt="Quem pesquisa economiza", esq=""):
    return f'<div class="rod" style="color:{cor}"><span>{esq}</span><span>{dir_txt}</span></div>'

def seta(cor):
    return f'<svg width="90" height="44" viewBox="0 0 96 48" fill="none"><path d="M4 24h80" stroke="{cor}" stroke-width="6" stroke-linecap="round"/><path d="M68 8l18 16-18 16" stroke="{cor}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# ---------- modelos de slide (1080x1350) ----------

def s_capa(tema, kicker, titulo, sub="", num=None, tam=124, modelo=False):
    bg, fg, ac, mu = TEMAS[tema]
    return f'''<div class="pg" style="background:{bg};color:{fg}">{topo(fg,num)}
<div style="margin-top:auto;margin-bottom:auto;display:flex;flex-direction:column;gap:30px">
<span class="kick" style="color:{ac}">{esc(kicker)}</span>
<h1 class="tit" style="font-size:{tam}px">{esc(titulo)}</h1>
{f'<p class="corpo" style="color:{mu}">{esc(sub)}</p>' if sub else ''}</div>
<div class="rod" style="color:{fg}"><span>Quem pesquisa economiza</span>{seta(fg)}</div>
{'<div class="selo">MODELO</div>' if modelo else ''}</div>'''

def s_texto(tema, kicker, titulo, corpo, num=None, tam=92):
    bg, fg, ac, mu = TEMAS[tema]
    return f'''<div class="pg" style="background:{bg};color:{fg}">{topo(fg,num)}
<div style="margin:auto 0;display:flex;flex-direction:column;gap:36px">
<span class="kick" style="color:{ac}">{esc(kicker)}</span>
<h2 class="tit" style="font-size:{tam}px">{esc(titulo)}</h2>
<p class="corpo" style="color:{mu}">{esc(corpo)}</p></div>{rodape(fg)}</div>'''

def s_passo(tema, n, titulo, corpo, num=None):
    bg, fg, ac, mu = TEMAS[tema]
    return f'''<div class="pg" style="background:{bg};color:{fg}">{topo(fg,num)}
<div style="margin:auto 0;display:flex;flex-direction:column;gap:32px">
<span class="tit" style="font-size:260px;color:{ac};line-height:.85">{n}</span>
<h2 class="tit" style="font-size:96px">{esc(titulo)}</h2>
<p class="corpo" style="color:{mu}">{esc(corpo)}</p></div>{rodape(fg)}</div>'''

def s_lista(tema, titulo, itens, num=None):
    bg, fg, ac, mu = TEMAS[tema]
    li = "".join(f'''<div style="display:flex;gap:28px;align-items:flex-start">
<span style="flex-shrink:0;width:64px;height:64px;border-radius:50%;background:{ac};color:{bg};display:flex;align-items:center;justify-content:center;font-family:Disp;font-weight:800;font-size:34px">✓</span>
<span style="font-size:42px;font-weight:600;line-height:1.3;padding-top:6px">{esc(i)}</span></div>''' for i in itens)
    return f'''<div class="pg" style="background:{bg};color:{fg}">{topo(fg,num)}
<div style="margin:auto 0"><h2 class="tit" style="font-size:96px">{esc(titulo)}</h2>
<div style="margin-top:72px;display:flex;flex-direction:column;gap:44px">{li}</div></div>{rodape(fg)}</div>'''

def s_cta(tema, titulo, sub, num=None):
    bg, fg, ac, mu = TEMAS[tema]
    return f'''<div class="pg" style="background:{bg};color:{fg};align-items:center;text-align:center">{topo(fg,num)}
<img src="{LOGO}" alt="" style="margin-top:110px;width:300px;height:300px;border-radius:60px">
<h2 class="tit" style="font-size:96px;margin-top:64px">{esc(titulo)}</h2>
<p class="corpo" style="margin-top:32px;color:{mu}">{esc(sub)}</p>
<div style="margin-top:auto;font-family:Disp;font-weight:800;font-size:44px">{HANDLE}</div></div>'''

def s_imagem_unica(tema, kicker, titulo, sub, chamada):
    bg, fg, ac, mu = TEMAS[tema]
    return f'''<div class="pg" style="background:{bg};color:{fg}">{topo(fg)}
<div style="margin-top:auto;display:flex;flex-direction:column;gap:30px">
<span class="kick" style="color:{ac}">{esc(kicker)}</span>
<h1 class="tit" style="font-size:120px">{esc(titulo)}</h1>
<p class="corpo" style="color:{mu}">{esc(sub)}</p></div>
<div style="margin-top:64px;margin-bottom:auto;align-self:flex-start;background:{fg};color:{bg};border-radius:999px;padding:30px 52px;font-family:Disp;font-weight:800;font-size:52px">{esc(chamada)}</div>
{rodape(fg)}</div>'''

def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def s_produto(prod, data, num, modelo):
    precos = prod["precos"]
    vals = [p["preco"] for p in precos if p.get("preco")]
    menor = min(vals) if vals else None
    linhas = ""
    for p in sorted(precos, key=lambda x: (x.get("preco") is None, x.get("preco") or 0)):
        v = p.get("preco")
        best = v is not None and v == menor
        txt = brl(v) if v is not None else "[R$ 0,00]"
        sub_preco = (f'<span style="font-size:26px;font-weight:600;opacity:.8"><s>{brl(p["preco_normal"])}</s> · no app</span>'
                     if p.get("preco_normal") else "")
        tag = (f'<span style="align-self:flex-start;background:{PRETO};color:{AMARELO};border-radius:999px;padding:8px 20px;font-size:24px;font-weight:700">menor preço</span>'
               if best else "")
        linhas += f'''<div style="display:flex;align-items:center;justify-content:space-between;gap:24px;padding:30px 36px;border-radius:28px;background:{AMARELO if best else '#FFFFFF'};border:3px solid {PRETO if best else '#E2E2E2'}">
<span style="display:flex;flex-direction:column;gap:12px"><span style="font-size:40px;font-weight:700">{esc(p['mercado'])}</span>{tag}</span>
<span style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;white-space:nowrap"><span style="font-family:Disp;font-weight:800;font-size:56px">{txt}</span>{sub_preco}</span></div>'''
    return f'''<div class="pg" style="background:{CREME};color:{PRETO}">{topo(PRETO,num)}
<span class="kick" style="margin-top:90px;color:{VERMELHO}">Comparação</span>
<h2 class="tit" style="font-size:104px;margin-top:20px">{esc(prod['nome'])}</h2>
<div style="margin-top:56px;display:flex;flex-direction:column;gap:22px">{linhas}</div>
{rodape(PRETO, "Preços podem variar", f"Coletado em {esc(data)}")}
{'<div class="selo">MODELO</div>' if modelo else ''}</div>'''

def s_total(d, num, modelo):
    tot = {}
    for prod in d["produtos"]:
        for p in prod["precos"]:
            if p.get("preco") is not None:
                tot[p["mercado"]] = tot.get(p["mercado"], 0) + p["preco"]
    ordem = sorted(tot.items(), key=lambda x: x[1])
    linhas = "".join(f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:30px 0;border-bottom:3px solid rgba(255,255,255,.18)">
<span style="font-size:42px;font-weight:700">{i+1}º {esc(m)}</span><span style="font-family:Disp;font-weight:800;font-size:58px;color:{AMARELO if i==0 else '#FFFFFF'}">{brl(v)}</span></div>''' for i, (m, v) in enumerate(ordem))
    if not linhas:
        linhas = '<p class="corpo">[total por mercado]</p>'
    dif = f"Diferença entre a cesta mais barata e a mais cara: {brl(ordem[-1][1]-ordem[0][1])}" if len(ordem) > 1 else ""
    return f'''<div class="pg" style="background:{PRETO};color:#FFFFFF">{topo('#FFFFFF',num)}
<span class="kick" style="margin-top:90px;color:{AMARELO}">Resultado</span>
<h2 class="tit" style="font-size:104px;margin-top:20px">A cesta completa</h2>
<div style="margin-top:48px">{linhas}</div>
<p class="corpo" style="margin-top:44px;color:{AMARELO}">{esc(dif)}</p>
{rodape('#FFFFFF', "Manda pra quem faz as compras da casa")}
{'<div class="selo">MODELO</div>' if modelo else ''}</div>'''

# ---------- Reels e Stories (1080x1920) ----------

def q_reel(tema, grande, peq="", logo=False, tam=120, extra=""):
    bg, fg, ac, mu = TEMAS[tema]
    lg = f'<img src="{LOGO}" alt="" style="width:340px;height:340px;border-radius:70px;margin-bottom:60px">' if logo else ""
    return f'''<div class="pg" style="background:{bg};color:{fg};padding:140px 90px;align-items:center;justify-content:center;text-align:center">
{lg}<h1 class="tit" style="font-size:{tam}px">{grande}</h1>
{f'<p class="corpo" style="margin-top:40px;font-size:48px;color:{mu}">{peq}</p>' if peq else ''}{extra}
<div style="position:absolute;bottom:150px;left:0;right:0;text-align:center;font-weight:700;font-size:34px;color:{fg}">{HANDLE}</div></div>'''

def capa_destaque(icone, rotulo):
    return f'''<div class="pg" style="background:{AMARELO};padding:0;align-items:center;justify-content:center">
<div style="width:620px;height:620px;border-radius:50%;background:{PRETO};display:flex;align-items:center;justify-content:center">{icone}</div>
<div style="position:absolute;bottom:260px;font-family:Disp;font-weight:800;font-size:64px;color:{PRETO}">{esc(rotulo)}</div></div>'''

ICONES = {
    "O que é": '<svg width="300" height="300" viewBox="0 0 48 48" fill="none"><circle cx="20" cy="20" r="13" stroke="#FDDE03" stroke-width="4"/><path d="M30 30 L42 42" stroke="#FDDE03" stroke-width="5" stroke-linecap="round"/></svg>',
    "Como usar": '<svg width="280" height="280" viewBox="0 0 48 48" fill="none"><rect x="13" y="4" width="22" height="40" rx="5" stroke="#FDDE03" stroke-width="3.5"/><path d="M21 38h6" stroke="#FDDE03" stroke-width="3.5" stroke-linecap="round"/></svg>',
    "Preços": '<svg width="280" height="280" viewBox="0 0 48 48" fill="none"><path d="M6 8h6l5 24h22l5-16H15" stroke="#FDDE03" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/><circle cx="20" cy="40" r="3" fill="#FDDE03"/><circle cx="36" cy="40" r="3" fill="#FDDE03"/></svg>',
    "Comerciante": '<svg width="280" height="280" viewBox="0 0 48 48" fill="none"><path d="M6 18l4-10h28l4 10" stroke="#FDDE03" stroke-width="3.5" stroke-linejoin="round"/><path d="M6 18h36v4a6 6 0 0 1-12 0 6 6 0 0 1-12 0 6 6 0 0 1-12 0z" stroke="#FDDE03" stroke-width="3.5" stroke-linejoin="round"/><path d="M10 28v14h28V28" stroke="#FDDE03" stroke-width="3.5" stroke-linejoin="round"/></svg>',
    "Testador": '<svg width="280" height="280" viewBox="0 0 48 48" fill="none"><path d="M10 25l9 9 19-20" stroke="#FDDE03" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

# ---------- motor ----------

class Render:
    def __init__(self, pw):
        self.b = pw.chromium.launch()
        self.p = self.b.new_page()
    def png(self, corpo, saida, w=1080, h=1350):
        saida.parent.mkdir(parents=True, exist_ok=True)
        tmp = FERR / "_tmp.html"
        tmp.write_text(doc(w, h, corpo), encoding="utf-8")
        self.p.set_viewport_size({"width": w, "height": h})
        self.p.goto(tmp.as_uri()); self.p.wait_for_timeout(150)
        self.p.screenshot(path=str(saida), clip={"x": 0, "y": 0, "width": w, "height": h})
        tmp.unlink()
    def fechar(self):
        self.b.close()

def video(quadros, duracoes, saida):
    """Junta quadros 1080x1920 num Reel MP4 com transição suave e trilha silenciosa."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for q, d in zip(quadros, duracoes):
        args += ["-loop", "1", "-t", str(d + 0.5), "-i", str(q)]
    args += ["-f", "lavfi", "-t", str(sum(duracoes) + 0.5), "-i", "anullsrc=r=44100:cl=stereo"]
    # cada entrada dura d+0.5 s; a transição de 0.5 s começa ao fim de cada quadro
    filtros, ant, off = [], "0:v", 0.0
    for i in range(1, len(quadros)):
        off += duracoes[i - 1]
        filtros.append(f"[{ant}][{i}:v]xfade=transition=slideup:duration=0.5:offset={off:.2f}[v{i}]")
        ant = f"v{i}"
    filtros.append(f"[{ant}]format=yuv420p,fps=30[vout]")
    args += ["-filter_complex", ";".join(filtros), "-map", "[vout]", "-map", f"{len(quadros)}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-shortest",
             "-movflags", "+faststart", str(saida)]
    subprocess.run(args, check=True)

def carregar(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))

def completo_comparacao(d):
    return d.get("pronto") and all(p.get("preco") is not None for pr in d["produtos"] for p in pr["precos"])

def main():
    for pasta in (MIDIA, PREVIA):
        if pasta.exists():
            shutil.rmtree(pasta)
    with sync_playwright() as pw:
        r = Render(pw)
        S = lambda nome: MIDIA / nome

        # P01 O que é o Tabelapp
        sl = [
            s_capa("amarelo", "Prazer, Tabelapp", "Onde está mais barato? Agora dá pra saber.", "Arrasta pro lado →", "1/5", 118),
            s_texto("preto", "O problema", "O mesmo produto muda de preço de um mercado pro outro.", "E a gente só descobre no caixa, quando já passou tudo.", "2/5"),
            s_lista("branco", "O que o Tabelapp faz", ["Compara preços de mercados perto de você", "Mostra encartes e ofertas da semana", "Usa preços reais de notas fiscais"], "3/5"),
            s_texto("creme", "De Petrópolis", "Feito aqui, por quem faz compras aqui.", "Cada preço que entra no app ajuda outra pessoa da cidade a economizar.", "4/5"),
            s_cta("amarelo", "Siga e não pague mais caro.", "Manda pra quem faz as compras da casa.", "5/5"),
        ]
        for i, c in enumerate(sl, 1): r.png(c, S(f"P01-o-que-e/{i:02d}.png"))

        # P02 Como funciona
        sl = [
            s_capa("preto", "Como funciona", "3 passos pra pagar menos.", "", "1/5", 130),
            s_passo("amarelo", "1", "Busque o produto", "Arroz, café, sabão, fralda… digite o que você precisa.", "2/5"),
            s_passo("branco", "2", "Compare os preços", "Veja onde está mais barato perto de você, com data e origem de cada preço.", "3/5"),
            s_passo("creme", "3", "Escolha onde comprar", "Leu o QR Code da nota? O preço entra no app e ajuda a cidade toda.", "4/5"),
            s_cta("amarelo", "Quer testar antes de todo mundo?", "Comente EU TESTO que a gente te chama.", "5/5"),
        ]
        for i, c in enumerate(sl, 1): r.png(c, S(f"P02-como-funciona/{i:02d}.png"))

        # P03 Parceiro Fundador (artes do LinkedIn)
        for i in range(1, 6):
            dst = S(f"P03-parceiro-fundador/{i:02d}.png"); dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(BASE / f"06-parceiro-fundador-p{i}.png", dst)

        # P04 Reel "Você compara?"
        fr = [q_reel("amarelo", "Você compara preço antes de ir ao mercado?", tam=118),
              q_reel("preto", "O mesmo produto pode custar bem diferente de um mercado pro outro."),
              q_reel("branco", "E a diferença só aparece no caixa.", tam=130),
              q_reel("amarelo", "Com o Tabelapp, você descobre antes de sair de casa.", tam=110),
              q_reel("preto", "Quem pesquisa<br>economiza.", "Siga pra ver os preços de Petrópolis", logo=True, tam=110)]
        qs = []
        for i, c in enumerate(fr, 1):
            q = FERR / f"_q/P04-{i}.png"; r.png(c, q, 1080, 1920); qs.append(q)
        video(qs, [2.6, 3.0, 2.4, 3.0, 3.0], S("P04-reel-voce-compara/reel.mp4"))
        shutil.copy(qs[0], S("P04-reel-voce-compara/capa.png"))

        # P05 / P11 Comparações (dependem de dados reais)
        for pid, arq in (("P05-comparacao-1", "comparacao-1.json"), ("P11-comparacao-2", "comparacao-2.json")):
            d = carregar(arq); ok = completo_comparacao(d); destino = MIDIA if ok else PREVIA
            n = len(d["produtos"]) + 2
            r.png(s_capa("amarelo", d["titulo"], d["subtitulo"], f"{d['bairro']} · {d['data']}  →", f"1/{n}", 116, not ok), destino / pid / "01.png")
            for i, prod in enumerate(d["produtos"], 2):
                r.png(s_produto(prod, d["data"], f"{i}/{n}", not ok), destino / pid / f"{i:02d}.png")
            r.png(s_total(d, f"{n}/{n}", not ok), destino / pid / f"{n:02d}.png")

        # P06 Reel investigação do café (depende de dados reais)
        d = carregar("cafe.json"); ok = d.get("pronto") and all(p.get("preco") is not None for p in d["precos"])
        destino = MIDIA if ok else PREVIA
        tab = BASE / "tabelinha.png"
        tab_html = f'<img src="{tab.as_uri()}" alt="" style="width:460px;margin-top:50px">' if tab.exists() else ""
        precos = sorted(d["precos"], key=lambda x: (x["preco"] is None, x["preco"] or 0))
        fr = [q_reel("amarelo", "Investigação:<br>quanto custa o café em Petrópolis?", "Tabelinha foi a campo com a lupa 🔍", tam=104, extra=tab_html)]
        for p in reversed(precos):
            v = brl(p["preco"]) if p["preco"] is not None else "[R$ 0,00]"
            fr.append(q_reel("preto", f'{esc(p["mercado"])}<br><span style="color:{AMARELO};font-size:170px">{v}</span>', esc(d["produto"]), tam=96))
        vals = [p["preco"] for p in precos if p["preco"] is not None]
        dif = brl(max(vals) - min(vals)) if len(vals) > 1 else "[R$ 0,00]"
        fr.append(q_reel("amarelo", f"Diferença:<br>{dif}", f"no mesmo café · {esc(d['data'])}", tam=130))
        fr.append(q_reel("preto", "Quem pesquisa<br>economiza.", "Siga e veja os preços da semana", logo=True, tam=110))
        qs = []
        for i, c in enumerate(fr, 1):
            q = FERR / f"_q/P06-{i}.png"; r.png(c, q, 1080, 1920); qs.append(q)
        video(qs, [3.0] + [1.8] * len(precos) + [2.6, 2.8], destino / "P06-reel-cafe/reel.mp4")
        shutil.copy(qs[0], destino / "P06-reel-cafe/capa.png")

        # P07 Testadores
        r.png(s_imagem_unica("amarelo", "Fase de testes", "Teste o Tabelapp antes de todo mundo.", "Grátis · celular Android · conta Google", "Comente EU TESTO"), S("P07-testadores/01.png"))

        # P08 Black Friday: 5 dicas
        sl = [
            s_capa("preto", "Black Friday", "5 dicas pra não cair em cilada.", "Salve pra usar na sexta →", "1/7", 120),
            s_passo("amarelo", "1", "Anote o preço de hoje", "Os itens que você quer comprar: anote o preço antes da Black Friday.", "2/7"),
            s_passo("branco", "2", "Desconfie da porcentagem", "-70% sobre um preço inflado não é desconto. Olhe o valor final.", "3/7"),
            s_passo("creme", "3", "Compare entre lojas", "No mesmo dia, o mesmo produto muda de preço de uma loja pra outra.", "4/7"),
            s_passo("amarelo", "4", "Veja o preço por kg ou litro", "Embalagem maior nem sempre sai mais barata.", "5/7"),
            s_passo("branco", "5", "Guarde a nota fiscal", "É a sua garantia e ajuda a comparar depois.", "6/7"),
            s_cta("amarelo", "Salve e mande pra quem vai às compras.", "Quem pesquisa economiza.", "7/7"),
        ]
        for i, c in enumerate(sl, 1): r.png(c, S(f"P08-black-friday-dicas/{i:02d}.png"))

        # P09, P10, P13, P15 (artes do LinkedIn)
        for pid, arq in (("P09-nota-fiscal", "07-nota-fiscal-pdf.png"), ("P10-black-friday", "08-black-friday.png"),
                         ("P13-economia-local", "10-economia-local.png")):
            dst = S(f"{pid}/01.png"); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(BASE / arq, dst)

        # P15 Lançamento (duas versões; o calendário escolhe qual sai)
        def lanc(tema, kicker, titulo, sub, faixa):
            bg, fg, ac, mu = TEMAS[tema]
            return f'''<div class="pg" style="background:{bg};color:{fg};align-items:center;text-align:center">
<img src="{LOGO}" alt="" style="margin-top:90px;width:380px;height:380px;border-radius:80px">
<span class="kick" style="margin-top:70px;color:{ac}">{esc(kicker)}</span>
<h1 class="tit" style="font-size:118px;margin-top:22px">{esc(titulo)}</h1>
<p class="corpo" style="margin-top:30px;color:{mu}">{esc(sub)}</p>
<div style="margin-top:auto;background:{fg};color:{bg};border-radius:999px;padding:26px 56px;font-family:Disp;font-weight:800;font-size:46px">{esc(faixa)}</div></div>'''
        r.png(lanc("amarelo", "Em breve", "na Google Play", "Tabelapp: Pesquisa de Preços", "Ative as notificações do perfil"), S("P15-lancamento-em-breve/01.png"))
        r.png(lanc("preto", "Já disponível", "na Google Play", "Baixe grátis e compare preços perto de você.", "Link na bio"), S("P15-lancamento-disponivel/01.png"))

        # P12 Reel bastidores (depende de números reais)
        d = carregar("bastidores.json")
        ok = d.get("pronto") and all(d.get(k) is not None for k in ("precos_cadastrados", "mercados", "notas_fiscais", "testadores"))
        destino = MIDIA if ok else PREVIA
        n = lambda k: f'{d[k]:,}'.replace(",", ".") if d.get(k) is not None else "[000]"
        fr = [q_reel("amarelo", "Um app feito em Petrópolis.", "Os números reais do nosso teste:", tam=120),
              q_reel("preto", f'<span style="color:{AMARELO};font-size:240px">{n("precos_cadastrados")}</span><br>preços cadastrados', tam=90),
              q_reel("preto", f'<span style="color:{AMARELO};font-size:240px">{n("notas_fiscais")}</span><br>notas fiscais lidas', tam=90),
              q_reel("preto", f'<span style="color:{AMARELO};font-size:240px">{n("mercados")}</span><br>mercados', tam=90),
              q_reel("preto", f'<span style="color:{AMARELO};font-size:240px">{n("testadores")}</span><br>testadores', tam=90),
              q_reel("amarelo", "Obrigado a quem está construindo isso com a gente.", logo=True, tam=96)]
        qs = []
        for i, c in enumerate(fr, 1):
            q = FERR / f"_q/P12-{i}.png"; r.png(c, q, 1080, 1920); qs.append(q)
        video(qs, [2.6, 2.0, 2.0, 2.0, 2.0, 3.0], destino / "P12-reel-bastidores/reel.mp4")
        shutil.copy(qs[0], destino / "P12-reel-bastidores/capa.png")

        # P14 Reel 3 erros
        fr = [q_reel("preto", "3 erros que deixam suas compras mais caras", tam=120),
              q_reel("amarelo", "1. Ir ao mercado sem lista", "Quem vai sem lista compra o que não precisa.", tam=110),
              q_reel("branco", "2. Não olhar o preço por quilo", "O pacote maior nem sempre é o mais barato.", tam=110),
              q_reel("amarelo", "3. Comprar sempre no mesmo lugar sem comparar", "O hábito custa caro.", tam=100),
              q_reel("preto", "Quem pesquisa<br>economiza.", "Siga e compare antes de comprar", logo=True, tam=110)]
        qs = []
        for i, c in enumerate(fr, 1):
            q = FERR / f"_q/P14-{i}.png"; r.png(c, q, 1080, 1920); qs.append(q)
        video(qs, [2.6, 3.0, 3.0, 3.0, 3.0], S("P14-reel-3-erros/reel.mp4"))
        shutil.copy(qs[0], S("P14-reel-3-erros/capa.png"))

        # Perfil: foto e capas de destaques
        PERFIL.mkdir(exist_ok=True)
        shutil.copy(BASE / "logo.png", PERFIL / "foto-de-perfil.png")
        for i, (rot, ic) in enumerate(ICONES.items(), 1):
            r.png(capa_destaque(ic, rot), PERFIL / f"destaque-{i}-{rot.lower().replace(' ', '-').replace('ç','c').replace('é','e')}.png", 1080, 1920)

        # Modelos de Stories
        STORIES.mkdir(exist_ok=True)
        r.png(q_reel("amarelo", "Preço do dia", '<span style="display:inline-block;margin-top:40px;background:#fff;border-radius:28px;padding:40px 60px;font-size:44px;color:#141414">[produto] · [mercado]<br><b style="font-size:110px">[R$ 0,00]</b></span>', tam=130), STORIES / "story-preco-do-dia.png", 1080, 1920)
        r.png(q_reel("preto", "Enquete rápida", "Coloque aqui a figurinha de enquete do Instagram", tam=130), STORIES / "story-enquete-fundo.png", 1080, 1920)
        r.png(q_reel("amarelo", "Quer testar o app antes de todo mundo?", "Responde aqui ou manda EU TESTO no direct", logo=True, tam=104), STORIES / "story-testador.png", 1080, 1920)
        r.fechar()
    shutil.rmtree(FERR / "_q", ignore_errors=True)
    # A API do Instagram trabalha melhor com JPEG: cria uma cópia .jpg de cada imagem publicável.
    from PIL import Image
    for png in list(MIDIA.rglob("*.png")) + list(PREVIA.rglob("*.png") if PREVIA.exists() else []):
        Image.open(png).convert("RGB").save(png.with_suffix(".jpg"), "JPEG", quality=92, optimize=True)
    print("Pronto. Publicáveis em midia/, modelos pendentes em previa/.")
    for p in sorted(PREVIA.glob("*")) if PREVIA.exists() else []:
        print("  PENDENTE (falta dado real):", p.name)

if __name__ == "__main__":
    main()
