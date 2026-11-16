"""Tema visual dan helper komponen UI."""
from __future__ import annotations

import html
import inspect

import streamlit as st

from . import config

# ---- Design tokens: Forest Green, Warm Ivory, White, Sage, Gold
IVORY = "#F7F3E8"
SURFACE = "#FFFFFF"
FOREST = "#173F31"
FOREST_SOFT = "#1F5140"
GREEN = "#2A7358"
SAGE = "#9DB8A0"
SAGE_PALE = "#E8F0E7"
GOLD = "#C9A64B"
GOLD_PALE = "#F8F0D9"
INK = "#25332C"
MUTED = "#76817A"
BORDER = "#E4E1D3"
RED, RED_PALE = "#B24848", "#FBEDEB"
AMBER, AMBER_PALE = "#9C6D17", "#FBF1D8"
BLUE, BLUE_PALE = "#3F6B8C", "#E9F0F5"
GREY_PALE = "#EEEDE6"

_STRETCH = {"width": "stretch"} if "width" in inspect.signature(st.button).parameters else {"use_container_width": True}


def stretch() -> dict:
    """Kompatibel lintas versi Streamlit (width='stretch' vs use_container_width)."""
    return dict(_STRETCH)


def esc(value) -> str:
    """Escape semua data (termasuk data dari blockchain) sebelum masuk HTML."""
    return html.escape(str(value if value is not None else ""), quote=True)


def inject_css():
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'DM Sans', sans-serif; color: {INK}; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {IVORY}; }}
[data-testid="stHeader"] {{ background: rgba(247,243,232,.9); }}
.block-container {{ max-width: 1360px; padding-top: 2rem; padding-bottom: 3rem; }}
h1,h2,h3,h4 {{ color: {FOREST} !important; font-family: 'Manrope', sans-serif !important; letter-spacing: -.4px; }}
p, label, li {{ color: {INK}; }}
[data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; font-size: .82rem; }}

/* ---------- Sidebar (rata kiri) ---------- */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{ background: {FOREST}; border-right: 1px solid #234F3F; }}
[data-testid="stSidebar"] * {{ text-align: left; }}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{ padding-top: .4rem; }}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{ color: #EAF3EC; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: #B9D0C0 !important; }}
[data-testid="stSidebar"] hr {{ border-color: #2E5A49; margin: 1rem 0; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button {{
  width: 100%; min-height: 43px; display: flex; align-items: center; justify-content: flex-start;
  gap: 4px; padding: 9px 12px !important; margin: 1px 0 !important; border-radius: 10px !important;
  border: 1px solid transparent !important; background: transparent !important; box-shadow: none !important;
  transition: background .15s ease; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button > div {{ justify-content: flex-start !important; width: 100%; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button p {{ color: #EAF4ED !important; font-size: .88rem !important; font-weight: 600 !important; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button [data-testid="stIconMaterial"] {{ color: #CFE6D7 !important; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{ background: #245746 !important; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
  background: #EEF5EC !important; border-color: {GOLD} !important; box-shadow: inset 3px 0 0 {GOLD} !important; }}
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] [data-testid="stIconMaterial"] {{ color: {FOREST} !important; font-weight: 700 !important; }}
.sb-title {{ color: #CFE0D4; font-size: .7rem; font-weight: 800; letter-spacing: 1.1px; margin: 4px 0 9px; text-transform: uppercase; }}
.brand {{ display: flex; align-items: center; gap: 11px; padding: 6px 2px 16px; border-bottom: 1px solid #2E5A49; margin-bottom: 16px; }}
.brand-mark {{ width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, #EEF5EC, {SAGE}); display: flex; align-items: center; justify-content: center; flex: none; }}
.brand-name {{ color: #FFFFFF; font: 800 1.1rem 'Manrope', sans-serif; letter-spacing: -.3px; line-height: 1.1; }}
.brand-sub {{ color: {GOLD}; font-size: .62rem; letter-spacing: 1.6px; font-weight: 700; margin-top: 2px; }}

/* kartu wallet hijau dengan gelembung transparan */
.wallet-card {{
  position: relative; overflow: hidden; border-radius: 15px; padding: 15px; margin: 4px 0 10px; border: 1px solid #4A7A66;
  background:
    radial-gradient(circle at 90% 10%, rgba(232,246,236,.20) 0 26px, transparent 27px),
    radial-gradient(circle at 103% 20%, rgba(232,246,236,.10) 0 54px, transparent 55px),
    radial-gradient(circle at 12% 112%, rgba(201,166,75,.20) 0 38px, transparent 39px),
    radial-gradient(circle at 68% 118%, rgba(232,246,236,.09) 0 30px, transparent 31px),
    linear-gradient(135deg, #1F5140, #2A7358); box-shadow: 0 6px 16px rgba(4,25,18,.18); }}
.wallet-card > * {{ position: relative; z-index: 1; }}
.wc-cap {{ color: #C6DDCE; font-size: .68rem; letter-spacing: 1px; font-weight: 700; margin-bottom: 7px; display: flex; justify-content: space-between; align-items: center; }}
.wc-addr {{ color: #F3FAF5; font: 600 .72rem ui-monospace, Menlo, Consolas, monospace; overflow-wrap: anywhere; line-height: 1.5; }}
.wc-bal {{ color: #EBD58F; font-weight: 700; font-size: .95rem; margin-top: 9px; }}
.role-badge {{ display: inline-block; padding: 2px 9px; border-radius: 99px; font-size: .66rem; font-weight: 800; letter-spacing: .5px; background: {GOLD}; color: {FOREST}; }}
.role-badge.off {{ background: rgba(255,255,255,.16); color: #DDEBE1; }}
.auth-row {{ display: flex; justify-content: space-between; gap: 8px; font-size: .74rem; color: #CFE0D4; padding: 3px 0; }}
.auth-row b {{ color: #F2F8F3; font: 600 .72rem ui-monospace, Menlo, monospace; }}

/* ---------- Konten ---------- */
.eyebrow {{ color: {GREEN}; font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; margin-bottom: 6px; }}
.page-title {{ color: {FOREST}; font: 800 1.85rem 'Manrope', sans-serif; letter-spacing: -.8px; margin: 0 0 5px; }}
.page-desc {{ color: {MUTED}; font-size: .92rem; margin-bottom: 20px; max-width: 760px; }}
.banner {{ position: relative; overflow: hidden; border-radius: 20px; padding: 28px 32px; margin-bottom: 20px; color: #fff;
  background: radial-gradient(circle at 88% 15%, rgba(255,255,255,.10) 0 70px, transparent 71px),
              radial-gradient(circle at 96% 85%, rgba(201,166,75,.22) 0 90px, transparent 91px),
              linear-gradient(115deg, {FOREST} 0%, #1D5A44 62%, {GREEN} 100%); box-shadow: 0 8px 26px rgba(23,63,49,.14); }}
.banner .kick {{ color: #CFE3D5; font-size: .72rem; letter-spacing: 1.4px; text-transform: uppercase; }}
.banner .ttl {{ font: 800 1.8rem 'Manrope', sans-serif; margin: 6px 0 6px; letter-spacing: -.7px; color: #fff; }}
.banner .cp {{ color: #DCEBE0; font-size: .9rem; margin: 0; max-width: 560px; }}
.pill {{ display: inline-block; margin: 16px 8px 0 0; padding: 5px 11px; border: 1px solid rgba(225,242,230,.3); border-radius: 99px; color: #E8F4EB; font-size: .72rem; background: rgba(255,255,255,.08); }}
.card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(40,50,30,.04); }}
.card + .card {{ margin-top: 14px; }}
.sec-h {{ color: {FOREST}; font: 700 1.02rem 'Manrope', sans-serif; margin: 0 0 3px; }}
.sec-s {{ color: {MUTED}; font-size: .8rem; margin-bottom: 12px; }}
.metric {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px; padding: 16px 17px; min-height: 118px; box-shadow: 0 2px 8px rgba(40,50,30,.04); }}
.metric.hero {{ background: linear-gradient(135deg, {FOREST}, {GREEN}); border-color: {FOREST}; }}
.metric.hero .m-l, .metric.hero .m-n {{ color: #CFE3D5; }} .metric.hero .m-v {{ color: #fff; }}
.m-top {{ display: flex; justify-content: space-between; align-items: center; }}
.m-l {{ color: {MUTED}; font-size: .76rem; font-weight: 600; }}
.m-i {{ width: 30px; height: 30px; border-radius: 9px; background: {SAGE_PALE}; color: {GREEN}; display: flex; align-items: center; justify-content: center; font-size: .95rem; }}
.metric.hero .m-i {{ background: rgba(255,255,255,.14); color: #fff; }}
.m-v {{ color: {FOREST}; font: 800 1.7rem 'Manrope', sans-serif; margin-top: 9px; letter-spacing: -.5px; }}
.m-n {{ color: {MUTED}; font-size: .7rem; margin-top: 1px; }}
.chip {{ display: inline-block; border-radius: 99px; padding: 4px 11px; font-size: .72rem; font-weight: 700; white-space: nowrap; }}
.chip.info {{ background: {BLUE_PALE}; color: {BLUE}; }} .chip.warn {{ background: {AMBER_PALE}; color: {AMBER}; }}
.chip.bad {{ background: {RED_PALE}; color: {RED}; }} .chip.ok {{ background: {SAGE_PALE}; color: {GREEN}; }} .chip.muted {{ background: {GREY_PALE}; color: #6B6B60; }}
.notice {{ border-radius: 12px; padding: 13px 16px; font-size: .86rem; border: 1px solid {BORDER}; background: #FBFAF4; color: {INK}; margin-bottom: 14px; }}
.notice.danger {{ background: {RED_PALE}; border-color: #F0CDCA; color: #8A3636; }}
.notice.ok {{ background: {SAGE_PALE}; border-color: #CFE0D2; color: {FOREST}; }}
.notice.warn {{ background: {AMBER_PALE}; border-color: #EEDDB0; color: #7A5410; }}
.notice.info {{ background: {BLUE_PALE}; border-color: #CFDEE9; color: #2F5671; }}
.drow {{ display: flex; justify-content: space-between; gap: 18px; padding: 10px 0; border-bottom: 1px solid {BORDER}; font-size: .85rem; }}
.drow:last-child {{ border-bottom: 0; }} .dl {{ color: {MUTED}; flex: none; }}
.dv {{ color: {INK}; font-weight: 600; text-align: right; overflow-wrap: anywhere; }}
.mono {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .78rem; }}
.verdict {{ border-radius: 18px; padding: 22px 26px; margin-bottom: 16px; display: flex; gap: 16px; align-items: center; border: 1px solid; }}
.verdict .vi {{ font-size: 2.1rem; line-height: 1; }} .verdict .vt {{ font: 800 1.3rem 'Manrope', sans-serif; letter-spacing: -.4px; }} .verdict .vs {{ font-size: .86rem; margin-top: 3px; }}
.verdict.ok {{ background: #E5F1E7; border-color: #BFD9C6; color: {FOREST}; }} .verdict.bad {{ background: {RED_PALE}; border-color: #EBC5C2; color: #7F2E2E; }}
.verdict.warn {{ background: {AMBER_PALE}; border-color: #E9D6A2; color: #6F4C0D; }} .verdict.info {{ background: {BLUE_PALE}; border-color: #C9DAE6; color: #2B5069; }}
.check {{ display: flex; gap: 9px; align-items: flex-start; font-size: .84rem; padding: 6px 0; }}
.check .ck {{ width: 20px; height: 20px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; font-size: .72rem; font-weight: 800; color: #fff; }}
.ck.y {{ background: {GREEN}; }} .ck.n {{ background: {RED}; }} .ck.w {{ background: {GOLD}; }}
.steps {{ display: flex; gap: 0; margin: 4px 0 6px; }} .step {{ flex: 1; text-align: left; position: relative; padding-top: 22px; font-size: .74rem; color: {MUTED}; }}
.step:before {{ content: ''; position: absolute; top: 5px; left: 0; right: 0; height: 3px; background: {BORDER}; }}
.step:after {{ content: ''; position: absolute; top: 0; left: 0; width: 13px; height: 13px; border-radius: 50%; background: {BORDER}; }}
.step.done {{ color: {FOREST}; font-weight: 700; }} .step.done:before, .step.done:after {{ background: {GREEN}; }}
.step.fail {{ color: {RED}; font-weight: 700; }} .step.fail:before, .step.fail:after {{ background: {RED}; }}
.step.exp {{ color: {AMBER}; font-weight: 700; }} .step.exp:before, .step.exp:after {{ background: {GOLD}; }}
.tl {{ border-left: 2px solid {BORDER}; margin-left: 6px; padding-left: 16px; }} .tl-i {{ position: relative; padding: 0 0 14px; }}
.tl-i:before {{ content: ''; position: absolute; left: -23px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: {GREEN}; border: 2px solid #fff; box-shadow: 0 0 0 1px {GREEN}; }}
.tl-t {{ font-weight: 700; font-size: .86rem; color: {FOREST}; }} .tl-m {{ color: {MUTED}; font-size: .74rem; overflow-wrap: anywhere; }}
.bar {{ display: flex; height: 12px; border-radius: 99px; overflow: hidden; background: {GREY_PALE}; margin: 6px 0 12px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: .76rem; color: {MUTED}; }} .legend i {{ display: inline-block; width: 9px; height: 9px; border-radius: 3px; margin-right: 6px; }}
.thead {{ color: {MUTED}; font-size: .7rem; font-weight: 800; letter-spacing: .8px; text-transform: uppercase; padding: 8px 0; border-bottom: 2px solid {BORDER}; }}
.tcell {{ font-size: .86rem; padding: 6px 0; display: flex; align-items: center; min-height: 40px; overflow-wrap: anywhere; }}

/* ---------- Kontrol ---------- */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{ background: #fff !important; color: {INK} !important; border: 1px solid #D9DDCF !important; border-radius: 10px !important; }}
[data-baseweb="select"] > div {{ background: #fff !important; border: 1px solid #D9DDCF !important; border-radius: 10px !important; }}
[data-baseweb="select"] * {{ color: {INK} !important; }}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{ border-color: {GREEN} !important; box-shadow: 0 0 0 1px {GREEN} !important; }}
[data-testid="stMain"] .stButton > button, [data-testid="stMain"] .stDownloadButton > button {{ border-radius: 10px; min-height: 42px; font-weight: 700; border: 1px solid #D3D9C8; color: {FOREST}; background: #fff; transition: all .15s ease; }}
[data-testid="stMain"] .stButton > button:hover {{ border-color: {GREEN}; color: {GREEN}; background: {SAGE_PALE}; }}
[data-testid="stMain"] .stButton > button[kind="primary"] {{ background: {GREEN}; color: #fff; border: 1px solid {GREEN}; }}
[data-testid="stMain"] .stButton > button[kind="primary"] p {{ color: #fff !important; }}
[data-testid="stMain"] .stButton > button[kind="primary"]:hover {{ background: {FOREST}; border-color: {FOREST}; color: #fff; }}
[data-testid="stMain"] .stButton > button:disabled {{ opacity: .5; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: {SURFACE}; border-color: {BORDER}; border-radius: 16px; }}
[data-testid="stTabs"] [role="tab"] p {{ font-weight: 700; }}
code {{ color: {FOREST} !important; background: #F0F2E8 !important; border: 1px solid #E1E5D6; border-radius: 5px; padding: 1px 5px; }}
@media (max-width: 800px) {{
  .block-container {{ padding: 1rem 1rem 2rem; }} .banner {{ padding: 22px; }} .banner .ttl {{ font-size: 1.4rem; }}
  .page-title {{ font-size: 1.5rem; }} .drow {{ flex-direction: column; gap: 2px; }} .dv {{ text-align: left; }}
  .verdict {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def page_heading(eyebrow: str, title: str, desc: str = ""):
    st.markdown(
        f'<div class="eyebrow">{esc(eyebrow)}</div><div class="page-title">{esc(title)}</div>'
        f'<div class="page-desc">{esc(desc)}</div>',
        unsafe_allow_html=True,
    )


def metric(label: str, value, icon: str, note: str = "", hero: bool = False) -> str:
    return (
        f'<div class="metric{" hero" if hero else ""}"><div class="m-top"><div class="m-l">{esc(label)}</div>'
        f'<div class="m-i">{icon}</div></div><div class="m-v">{esc(value)}</div><div class="m-n">{esc(note)}</div></div>'
    )


def chip(status: int) -> str:
    label, tone = config.STATUS.get(status, ("Tidak diketahui", "muted"))
    return f'<span class="chip {tone}">{label}</span>'


def rows(pairs, mono=()):
    out = ""
    for label, value in pairs:
        cls = "dv mono" if label in mono else "dv"
        shown = value if (isinstance(value, str) and value.startswith("<span class=\"chip")) else esc(value if value not in ("", None) else "-")
        out += f'<div class="drow"><span class="dl">{esc(label)}</span><span class="{cls}">{shown}</span></div>'
    return out


def card(title: str, subtitle: str, body_html: str) -> str:
    sub = f'<div class="sec-s">{esc(subtitle)}</div>' if subtitle else ""
    return f'<div class="card"><div class="sec-h">{esc(title)}</div>{sub}{body_html}</div>'


def notice(text_html: str, tone: str = ""):
    st.markdown(f'<div class="notice {tone}">{text_html}</div>', unsafe_allow_html=True)


def goto(page: str, **state):
    """Callback navigasi (aman dipakai pada on_click)."""
    st.session_state["page"] = page
    for k, v in state.items():
        st.session_state[k] = v
    tx = st.session_state.get("tx")
    if tx and tx.get("stage") != "signing":
        st.session_state["tx"] = None
