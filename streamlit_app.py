import streamlit as st
import pandas as pd
import re
import calendar
from datetime import date

st.set_page_config(page_title="IDM Biomata", page_icon="🚛", layout="wide")

st.markdown("""
<style>
.card {
    padding: 22px;
    border-radius: 18px;
    color: white;
    min-height: 310px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}
.verde { background: linear-gradient(135deg, #15803d, #22c55e); }
.laranja { background: linear-gradient(135deg, #f59e0b, #f97316); }
.vermelho { background: linear-gradient(135deg, #dc2626, #ef4444); }
.card-title { font-size: 17px; font-weight: 700; }
.card-score { font-size: 58px; font-weight: 900; margin-top: 18px; }
.card-status { font-size: 22px; font-weight: 800; margin-bottom: 25px; }
.card-detail { font-size: 14px; line-height: 1.8; }
.kpi {
    padding: 20px;
    border-radius: 16px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    min-height: 120px;
}
.kpi-title { font-size: 14px; color: #64748b; }
.kpi-value { font-size: 30px; font-weight: 800; color: #0f172a; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🚛 IDM – Índice de Desempenho do Motorista Biomata")
st.caption("Performance, segurança, economia, RPM e produtividade operacional")

arquivo = st.file_uploader("📁 Envie o relatório da Maxtrack", type=["xlsx"])


def limpar_nome_coluna(nome):
    return re.sub(r"\s+", " ", str(nome).strip())


def encontrar_linha_cabecalho(arquivo_excel):
    bruto = pd.read_excel(arquivo_excel, header=None)
    for i in range(len(bruto)):
        valores = bruto.iloc[i].astype(str).str.strip().tolist()
        if "Motorista" in valores:
            return i
    return None


def encontrar_coluna(df, palavras):
    for coluna in df.columns:
        nome = str(coluna).lower()
        if all(p.lower() in nome for p in palavras):
            return coluna
    return None


def encontrar_coluna_opcional(df, opcoes):
    for palavras in opcoes:
        coluna = encontrar_coluna(df, palavras)
        if coluna is not None:
            return coluna
    return None


def tempo_para_horas(valor):
    if pd.isna(valor):
        return 0

    texto = str(valor).lower().strip()
    h = re.search(r"(\d+)\s*h", texto)
    m = re.search(r"(\d+)\s*m", texto)
    s = re.search(r"(\d+)\s*s", texto)

    horas = int(h.group(1)) if h else 0
    minutos = int(m.group(1)) if m else 0
    segundos = int(s.group(1)) if s else 0

    return horas + minutos / 60 + segundos / 3600


def horas_para_texto(horas):
    h = int(horas)
    m = int((horas - h) * 60)
    return f"{h}h {m}min"


def classificar(nota):
    if nota >= 85:
        return "Excelente"
    elif nota >= 75:
        return "Bom"
    elif nota >= 60:
        return "Atenção"
    return "Crítico"


def cor_classe(nota):
    if nota >= 75:
        return "verde"
    elif nota >= 60:
        return "laranja"
    return "vermelho"


def nota_seguranca(velocidade):
    if velocidade <= 80:
        return 100
    elif velocidade <= 85:
        return 70
    elif velocidade <= 90:
        return 50
    return 20


def calcular_notas(row, media_consumo, media_km):
    km = row["Distância (Km)"]
    consumo = row["Km/l"]
    velocidade = row["Velocidade Máxima"]
    parado = row["Horas Parado"]
    conducao = row["Horas Condução"]

    rpm_verde = row["RPM Verde (%)"]
    rpm_azul = row["RPM Azul (%)"]
    rpm_amarela = row["RPM Amarela (%)"]

    seguranca = nota_seguranca(velocidade)

    economia = 100
    if consumo <= 0:
        economia -= 50
    elif media_consumo > 0 and consumo < media_consumo:
        economia -= 25
    if km <= 0:
        economia -= 30
    if media_km > 0 and km < media_km * 0.5:
        economia -= 15
    economia = max(economia, 0)

    rpm = 100
    if rpm_verde > 0 or rpm_azul > 0 or rpm_amarela > 0:
        rpm = (rpm_verde * 1.0) + (rpm_azul * 0.75) - (rpm_amarela * 0.7)
        rpm = max(min(rpm, 100), 0)

    produtividade = 100
    if parado > 4:
        produtividade -= 30
    if parado > 6:
        produtividade -= 25
    if conducao <= 0:
        produtividade -= 30
    produtividade = max(produtividade, 0)

    nota_geral = round(
        (seguranca * 0.40)
        + (economia * 0.25)
        + (rpm * 0.20)
        + (produtividade * 0.15),
        0
    )

    return seguranca, economia, rpm, produtividade, nota_geral


def gerar_resumo(dados, grupo, media_consumo_base=None, media_km_base=None):
    resumo = dados.groupby(grupo).agg({
        "Distância (Km)": "sum",
        "Km/l": "mean",
        "Velocidade Máxima": "max",
        "Horas Parado": "sum",
        "Horas Condução": "sum",
        "Litros": "sum",
        "CO2": "sum",
        "RPM Verde (%)": "mean",
        "RPM Azul (%)": "mean",
        "RPM Amarela (%)": "mean"
    }).reset_index()

    if media_consumo_base is None:
        media_consumo = resumo[resumo["Km/l"] > 0]["Km/l"].mean()
    else:
        media_consumo = media_consumo_base

    if media_km_base is None:
        media_km = resumo[resumo["Distância (Km)"] > 0]["Distância (Km)"].mean()
    else:
        media_km = media_km_base

    if pd.isna(media_consumo):
        media_consumo = 0
    if pd.isna(media_km):
        media_km = 0

    notas = resumo.apply(lambda row: calcular_notas(row, media_consumo, media_km), axis=1)

    resumo["Segurança"] = [n[0] for n in notas]
    resumo["Economia"] = [n[1] for n in notas]
    resumo["RPM"] = [n[2] for n in notas]
    resumo["Produtividade"] = [n[3] for n in notas]
    resumo["Nota IDM Biomata"] = [n[4] for n in notas]
    resumo["Classificação"] = resumo["Nota IDM Biomata"].apply(classificar)

    return resumo, media_consumo, media_km


def card_categoria(titulo, nota, detalhes):
    html_detalhes = "".join([f"<div>• {d}</div>" for d in detalhes])
    html = f"""
    <div class="card {cor_classe(nota)}">
        <div class="card-title">{titulo}</div>
        <div class="card-score">{nota:.0f}</div>
        <div class="card-status">{classificar(nota)}</div>
        <hr style="border:0.5px solid rgba(255,255,255,0.45);">
        <div class="card-detail">{html_detalhes}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card_indicador(titulo, valor):
    html = f"""
    <div class="kpi">
        <div class="kpi-title">{titulo}</div>
        <div class="kpi-value">{valor}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


if arquivo is not None:
    linha_cabecalho = encontrar_linha_cabecalho(arquivo)

    if linha_cabecalho is None:
        st.error("Não encontrei a linha do cabeçalho com Motorista.")
        st.stop()

    df = pd.read_excel(arquivo, header=linha_cabecalho)
    df.columns = [limpar_nome_coluna(c) for c in df.columns]

    col_motorista = encontrar_coluna(df, ["motorista"])
    col_distancia = encontrar_coluna(df, ["distância"])
    col_velocidade = encontrar_coluna(df, ["velocidade"])
    col_consumo = encontrar_coluna(df, ["km/l"])
    col_parado = encontrar_coluna(df, ["tempo", "parado"])
    col_conducao = encontrar_coluna(df, ["tempo", "condu"])
    col_frota = encontrar_coluna_opcional(df, [["frota"], ["prefixo"], ["veículo"]])
    col_placa = encontrar_coluna_opcional(df, [["placa"]])
    col_litros = encontrar_coluna_opcional(df, [["litros"], ["combustível"]])
    col_co2 = encontrar_coluna_opcional(df, [["co2"], ["co₂"]])
    col_rpm_verde = encontrar_coluna_opcional(df, [["rpm", "verde"], ["faixa", "verde"]])
    col_rpm_azul = encontrar_coluna_opcional(df, [["rpm", "azul"], ["faixa", "azul"]])
    col_rpm_amarela = encontrar_coluna_opcional(df, [["rpm", "amarela"], ["faixa", "amarela"]])

    obrigatorias = {
        "Motorista": col_motorista,
        "Distância (Km)": col_distancia,
        "Velocidade Máxima": col_velocidade,
        "Km/l": col_consumo,
        "Tempo Parado": col_parado,
        "Tempo Condução": col_conducao
    }

    faltando = [nome for nome, coluna in obrigatorias.items() if coluna is None]

    if faltando:
        st.error("Colunas obrigatórias faltando:")
        st.write(faltando)
        st.write("Colunas encontradas:")
        st.write(df.columns.tolist())
        st.stop()

    renomear = {
        col_motorista: "Motorista",
        col_distancia: "Distância (Km)",
        col_velocidade: "Velocidade Máxima",
        col_consumo: "Km/l",
        col_parado: "Tempo Parado",
        col_conducao: "Tempo Condução"
    }

    if col_frota:
        renomear[col_frota] = "Prefixo"
    if col_placa:
        renomear[col_placa] = "Placa"
    if col_litros:
        renomear[col_litros] = "Litros"
    if col_co2:
        renomear[col_co2] = "CO2"
    if col_rpm_verde:
        renomear[col_rpm_verde] = "RPM Verde (%)"
    if col_rpm_azul:
        renomear[col_rpm_azul] = "RPM Azul (%)"
    if col_rpm_amarela:
        renomear[col_rpm_amarela] = "RPM Amarela (%)"

    df = df.rename(columns=renomear)

    df = df[df["Motorista"].notna()]
    df = df[df["Motorista"].astype(str).str.strip() != ""]

    if "Prefixo" not in df.columns:
        if "Placa" in df.columns:
            df["Prefixo"] = df["Placa"]
        else:
            df["Prefixo"] = "Sem prefixo"

    df["Prefixo"] = df["Prefixo"].astype(str).str.strip()
    df["Distância (Km)"] = pd.to_numeric(df["Distância (Km)"], errors="coerce").fillna(0)
    df["Velocidade Máxima"] = pd.to_numeric(df["Velocidade Máxima"], errors="coerce").fillna(0)
    df["Km/l"] = pd.to_numeric(df["Km/l"], errors="coerce").fillna(0)

    df["Litros"] = pd.to_numeric(df["Litros"], errors="coerce").fillna(0) if "Litros" in df.columns else 0
    df["CO2"] = pd.to_numeric(df["CO2"], errors="coerce").fillna(0) if "CO2" in df.columns else 0
    df["RPM Verde (%)"] = pd.to_numeric(df["RPM Verde (%)"], errors="coerce").fillna(0) if "RPM Verde (%)" in df.columns else 0
    df["RPM Azul (%)"] = pd.to_numeric(df["RPM Azul (%)"], errors="coerce").fillna(0) if "RPM Azul (%)" in df.columns else 0
    df["RPM Amarela (%)"] = pd.to_numeric(df["RPM Amarela (%)"], errors="coerce").fillna(0) if "RPM Amarela (%)" in df.columns else 0

    df["Horas Parado"] = df["Tempo Parado"].apply(tempo_para_horas)
    df["Horas Condução"] = df["Tempo Condução"].apply(tempo_para_horas)

    resumo, media_consumo, media_km = gerar_resumo(df, ["Motorista"])
    resumo = resumo.sort_values(by="Nota IDM Biomata", ascending=False)

    st.sidebar.header("🔎 Filtros")

    tipo_periodo = st.sidebar.radio("📅 Tipo de período", ["Dia", "Período", "Mês"])

    if tipo_periodo == "Dia":
        data_inicio = st.sidebar.date_input("Escolha o dia", value=date.today(), format="DD/MM/YYYY")
        data_fim = data_inicio
        periodo_texto = data_inicio.strftime("%d/%m/%Y")
    elif tipo_periodo == "Período":
        intervalo = st.sidebar.date_input("Escolha o período", value=(date.today(), date.today()), format="DD/MM/YYYY")
        if isinstance(intervalo, tuple) and len(intervalo) == 2:
            data_inicio, data_fim = intervalo
        else:
            data_inicio = date.today()
            data_fim = date.today()
        periodo_texto = f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
    else:
        data_mes = st.sidebar.date_input("Escolha qualquer dia do mês", value=date.today(), format="DD/MM/YYYY")
        ultimo_dia = calendar.monthrange(data_mes.year, data_mes.month)[1]
        data_inicio = date(data_mes.year, data_mes.month, 1)
        data_fim = date(data_mes.year, data_mes.month, ultimo_dia)
        periodo_texto = data_mes.strftime("%m/%Y")

    st.sidebar.info(f"Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")

    motoristas = sorted(resumo["Motorista"].dropna().unique().tolist())
    motorista_selecionado = st.sidebar.selectbox("👤 Motorista", motoristas)

    df_motorista = df[df["Motorista"] == motorista_selecionado]

    resumo_prefixo, _, _ = gerar_resumo(
        df_motorista,
        ["Prefixo"],
        media_consumo_base=media_consumo,
        media_km_base=media_km
    )

    resumo_prefixo = resumo_prefixo.sort_values(by="Nota IDM Biomata", ascending=False)

    prefixos = ["Todos"] + sorted(resumo_prefixo["Prefixo"].dropna().unique().tolist())
    prefixo_selecionado = st.sidebar.selectbox("🚛 Prefixo / Caminhão", prefixos)

    if prefixo_selecionado == "Todos":
        dados_motorista = resumo[resumo["Motorista"] == motorista_selecionado].copy()
        m = dados_motorista.iloc[0]
        titulo_painel = motorista_selecionado
    else:
        dados_motorista = resumo_prefixo[resumo_prefixo["Prefixo"] == prefixo_selecionado].copy()
        m = dados_motorista.iloc[0]
        titulo_painel = f"{motorista_selecionado} | {prefixo_selecionado}"

    st.success("Arquivo processado com sucesso!")

    aba1, aba2, aba3 = st.tabs(["🚛 Painel do Motorista", "🏆 Ranking", "📋 Relatório"])

    with aba1:
        st.subheader(f"🚛 {titulo_painel}")
        st.caption(f"Período selecionado: {periodo_texto}")

        c0, c1, c2, c3, c4 = st.columns([1.35, 1, 1, 1, 1])

        with c0:
            card_categoria(
                "IDM Biomata",
                m["Nota IDM Biomata"],
                [
                    "Índice geral do motorista",
                    "Segurança: peso 40%",
                    "Economia: peso 25%",
                    "RPM: peso 20%",
                    "Produtividade: peso 15%"
                ]
            )

        with c1:
            card_categoria(
                "🛡️ Segurança",
                m["Segurança"],
                [
                    f"Velocidade máxima: {m['Velocidade Máxima']:.0f} km/h",
                    "Até 80 km/h: ideal",
                    "Acima de 80 km/h: penaliza forte"
                ]
            )

        with c2:
            card_categoria(
                "⛽ Economia",
                m["Economia"],
                [
                    f"Consumo: {m['Km/l']:.2f} km/l",
                    f"Média frota: {media_consumo:.2f} km/l",
                    "Avalia eficiência no diesel"
                ]
            )

        with c3:
            card_categoria(
                "⚙️ RPM",
                m["RPM"],
                [
                    f"Faixa verde: {m['RPM Verde (%)']:.1f}%",
                    f"Faixa azul: {m['RPM Azul (%)']:.1f}%",
                    f"Faixa amarela: {m['RPM Amarela (%)']:.1f}%"
                ]
            )

        with c4:
            card_categoria(
                "🅿️ Produtividade",
                m["Produtividade"],
                [
                    f"Tempo parado: {horas_para_texto(m['Horas Parado'])}",
                    f"Condução: {horas_para_texto(m['Horas Condução'])}",
                    "Avalia ociosidade"
                ]
            )

        st.divider()

        st.subheader("🚛 Caminhões trabalhados pelo motorista")
        st.dataframe(resumo_prefixo, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("📌 Indicadores do período")

        k1, k2, k3, k4, k5 = st.columns(5)

        velocidade_media = m["Distância (Km)"] / m["Horas Condução"] if m["Horas Condução"] > 0 else 0

        with k1:
            card_indicador("Tempo total", horas_para_texto(m["Horas Condução"] + m["Horas Parado"]))
        with k2:
            card_indicador("Distância total", f'{m["Distância (Km)"]:,.2f} km')
        with k3:
            card_indicador("Velocidade média", f"{velocidade_media:.2f} km/h")
        with k4:
            card_indicador("Consumo médio", f'{m["Km/l"]:.2f} km/l')
        with k5:
            card_indicador("Litros", f'{m["Litros"]:,.2f} L' if m["Litros"] > 0 else "-")

        st.divider()

        st.subheader("⚙️ Gráfico de RPM")

        rpm_df = pd.DataFrame({
            "Faixa": ["Verde", "Azul", "Amarela"],
            "Percentual": [
                m["RPM Verde (%)"],
                m["RPM Azul (%)"],
                m["RPM Amarela (%)"]
            ]
        })

        st.bar_chart(rpm_df.set_index("Faixa"))

        with st.expander("📂 Ver dados completos"):
            if prefixo_selecionado == "Todos":
                st.dataframe(df_motorista, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_motorista[df_motorista["Prefixo"] == prefixo_selecionado], use_container_width=True, hide_index=True)

    with aba2:
        st.subheader("🏆 Ranking IDM Biomata")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Motoristas", resumo["Motorista"].nunique())
        r2.metric("KM Total", f'{resumo["Distância (Km)"].sum():,.0f} km')
        r3.metric("Consumo Médio", f'{media_consumo:.2f} km/l')
        r4.metric("IDM Médio", f'{resumo["Nota IDM Biomata"].mean():.1f}')

        st.dataframe(resumo, use_container_width=True, hide_index=True)

        st.subheader("Top 10")
        st.bar_chart(resumo.head(10).set_index("Motorista")["Nota IDM Biomata"])

    with aba3:
        st.subheader("📋 Relatório completo")

        csv = resumo.to_csv(index=False).encode("utf-8-sig")
        csv_prefixo = resumo_prefixo.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar Ranking IDM Biomata",
            data=csv,
            file_name="ranking_idm_biomata.csv",
            mime="text/csv"
        )

        st.download_button(
            label="📥 Baixar Caminhões do Motorista",
            data=csv_prefixo,
            file_name="caminhoes_motorista_idm.csv",
            mime="text/csv"
        )

        with st.expander("Abrir dados originais"):
            st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.warning("Aguardando envio do relatório.")
